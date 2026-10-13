import asyncio
import os
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

# 将 backend 加入模块搜索路径
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.database.models import (
    Base,
    WorldState,
    Player,
    CharacterState,
    Relationship,
    GameStateRevision,
    VariableChange,
)
from app.variables.schemas import VariablePatch, VariableOperation
from app.variables.snapshot import SnapshotBuilder
from app.variables.engine import VariableEngine
from app.variables.registry import VARIABLE_RULES

TEST_DB_FILE = BACKEND_DIR.parent / "data" / "test_variable_engine.db"
TEST_DB_URL = f"sqlite+aiosqlite:///{TEST_DB_FILE.as_posix()}"

async def run_variable_engine_suite():
    print("=" * 65)
    print("Campus AI — V0.2.0 正式变量系统 (Variable Engine) 自动化测试")
    print("=" * 65)

    if TEST_DB_FILE.exists():
        TEST_DB_FILE.unlink()

    engine = create_async_engine(TEST_DB_URL, echo=False)
    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 初始化测试基础数据
    async with SessionLocal() as session:
        state_rev = GameStateRevision(id=1, revision=10, schema_version=1)
        player = Player(name="你", energy=90, money=500)
        world = WorldState(day_number=2, weekday="星期四", time_slot="afternoon", player_location="library")
        char = CharacterState(character_id="lin_yuqing", current_location="library", current_mood="neutral")
        rel = Relationship(character_id="lin_yuqing", affection=40, trust=30, stage="friend")
        session.add_all([state_rev, player, world, char, rel])
        await session.commit()

    print("\n[测试 1/6] 验证统一状态快照构建 (SnapshotBuilder)...")
    async with SessionLocal() as session:
        snapshot = await SnapshotBuilder.build_snapshot(session)
        assert snapshot.revision == 10
        assert snapshot.player["money"] == 500
        assert snapshot.world["weekday"] == "星期四"
        assert "lin_yuqing" in snapshot.characters
        assert snapshot.characters["lin_yuqing"]["relationship"]["affection"] == 40
        print(" -> 统一变量快照构建成功，单一真源 stat_data 结构完整！")

    print("\n[测试 2/6] 验证所有权权限拦截 (拦截 AI 篡改钱包/越权提升恋爱阶段)...")
    async with SessionLocal() as session:
        illegal_patch = VariablePatch(
            base_revision=10,
            source="dialogue",  # 来源为 AI 对话提议
            operations=[
                VariableOperation(op="delta", path="/player/money", value=9999, reason="黑客AI送钱"),
                VariableOperation(op="replace", path="/characters/lin_yuqing/relationship/stage", value="lover", reason="强制结婚"),
            ]
        )
        result = await VariableEngine.apply_patch(illegal_patch, db=session)
        assert len(result.applied_changes) == 0, "越权操作未被拦截！"
        assert len(result.rejected_changes) == 2, "拒绝列表数量不符！"
        assert "越权操作被拒绝" in result.rejected_changes[0].reject_reason
        assert "越权操作被拒绝" in result.rejected_changes[1].reject_reason
        print(" -> 越权路径与非法所有权拦截验证通过，核心系统变量被严密保护！")

    print("\n[测试 3/6] 验证同路径预聚合与单轮限幅安全裁剪...")
    async with SessionLocal() as session:
        multi_delta_patch = VariablePatch(
            base_revision=10,
            source="dialogue",
            operations=[
                VariableOperation(op="delta", path="/characters/lin_yuqing/relationship/affection", value=3, reason="夸赞发型"),
                VariableOperation(op="delta", path="/characters/lin_yuqing/relationship/affection", value=3, reason="请喝汽水"),
                VariableOperation(op="delta", path="/characters/lin_yuqing/relationship/affection", value=3, reason="分享小说"),
                VariableOperation(op="replace", path="/characters/lin_yuqing/state/current_mood", value="happy", reason="感到开心"),
            ]
        )
        res = await VariableEngine.apply_patch(multi_delta_patch, db=session)
        await session.commit()

        # 3次 +3 提案总和为 +9，必须被裁剪为 +3
        aff_change = next(c for c in res.applied_changes if "affection" in c.path)
        assert aff_change.delta == 3, f"聚合裁剪失败，实际 delta={aff_change.delta}"
        assert aff_change.new_value == 43, f"好感更新失败，实际={aff_change.new_value}"
        assert aff_change.status == "clamped"

        mood_change = next(c for c in res.applied_changes if "current_mood" in c.path)
        assert mood_change.new_value == "happy"
        print(" -> 多重提议聚合与单轮最大增幅裁剪生效，防数值通胀闭环通过！")

    print("\n[测试 4/6] 验证全局修订版本号递增 (Revision Increment)...")
    async with SessionLocal() as session:
        rev_after = (await session.execute(select(GameStateRevision).limit(1))).scalar_one()
        assert rev_after.revision == 11, f"版本号未能递增，实际={rev_after.revision}"
        print(f" -> 全局状态版本由 10 成功递增至 {rev_after.revision}，乐观锁防时序冲突就绪！")

    print("\n[测试 5/6] 验证变更审计因果日志 (VariableChange Logging)...")
    async with SessionLocal() as session:
        changes = (await session.execute(select(VariableChange).order_by(VariableChange.id.asc()))).scalars().all()
        assert len(changes) == 2  # 好感度 + 心情
        assert changes[0].path == "/characters/lin_yuqing/relationship/affection"
        assert changes[0].old_value == "40"
        assert changes[0].new_value == "43"
        assert "夸赞发型" in changes[0].reason
        print(" -> 审计因果日志记录完备，每一次变量变动均可精准追溯！")

    print("\n[测试 6/6] 验证变量 API 路由端点...")
    from httpx import ASGITransport, AsyncClient
    from app.main import app
    from app.database.session import init_db
    # 确保主数据库同步建立新增的表
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        snap_resp = await client.get("/api/variables/snapshot")
        assert snap_resp.status_code == 200
        assert "revision" in snap_resp.json()

        log_resp = await client.get("/api/variables/changes")
        assert log_resp.status_code == 200
        assert isinstance(log_resp.json(), list)
        print(" -> 变量 API 接口 (/api/variables/snapshot, /changes) 联调通过！")

    # 清理测试数据库
    await engine.dispose()
    if TEST_DB_FILE.exists():
        TEST_DB_FILE.unlink()

    print("\n" + "=" * 65)
    print("[ALL PASSED] V0.2.0 正式变量系统核心架构与测试全量通过！")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(run_variable_engine_suite())
