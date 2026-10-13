import asyncio
import os
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

# 将 backend 根目录加入路径
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
    MomentPost,
    MomentLike,
    DialogueLog,
    Memory,
)
from app.variables.schemas import VariablePatch, VariableOperation
from app.variables.engine import VariableEngine, RevisionConflictError
from app.variables.snapshot import SnapshotBuilder

TEST_DB_FILE = BACKEND_DIR.parent / "data" / "test_sandbox_v021.db"
TEST_DB_URL = f"sqlite+aiosqlite:///{TEST_DB_FILE.as_posix()}"

async def run_v021_suite():
    print("=" * 65)
    print("Campus AI — V0.2.1 状态一致性与安全边界严密化测试套件")
    print("=" * 65)

    if TEST_DB_FILE.exists():
        TEST_DB_FILE.unlink()

    test_engine = create_async_engine(TEST_DB_URL, echo=False)
    TestSession = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 初始化测试数据
    async with TestSession() as session:
        state_rev = GameStateRevision(id=1, revision=5, schema_version=1)
        player = Player(name="你", energy=80, money=450, inventory={"orange_soda": 2})
        world = WorldState(day_number=3, weekday="星期五", time_slot="afternoon", player_location="library")
        char = CharacterState(character_id="lin_yuqing", current_location="library", current_mood="happy")
        rel = Relationship(character_id="lin_yuqing", affection=35, trust=25, familiarity=40, stage="friend")
        post = MomentPost(id="m_post_1", author_id="lin_yuqing", author_name="林雨晴", content="校园午后")
        session.add_all([state_rev, player, world, char, rel, post])
        await session.commit()

    print("\n[测试 1/6] 验证变量版本冲突严格拒绝 (拒绝过期并发基线)...")
    async with TestSession() as session:
        # 当前 revision 是 5，故意提交基于过期版本 4 的修改
        stale_patch = VariablePatch(
            base_revision=4,
            source="dialogue",
            operations=[
                VariableOperation(op="delta", path="/characters/lin_yuqing/relationship/affection", value=2, reason="旧对话")
            ]
        )
        conflict_caught = False
        try:
            await VariableEngine.apply_patch(stale_patch, db=session)
        except RevisionConflictError as e:
            conflict_caught = True
            print(f" -> 捕获版本冲突异常: {e}")

        assert conflict_caught, "版本冲突未能严格拒绝！"
        print(" -> 严格版本一致性乐观锁生效，过期并发更新被成功阻止！")

    print("\n[测试 2/6] 验证完整规范路径解析与严格枚举拦截...")
    async with TestSession() as session:
        # 路径错误：affection 属于 relationship，写在 state 下必须被拦截
        wrong_path_patch = VariablePatch(
            base_revision=5,
            source="dialogue",
            operations=[
                VariableOperation(op="delta", path="/characters/lin_yuqing/state/affection", value=2, reason="错误域"),
                VariableOperation(op="replace", path="/characters/lin_yuqing/state/current_mood", value="invalid_mood", reason="非法枚举"),
            ]
        )
        res = await VariableEngine.apply_patch(wrong_path_patch, db=session)
        assert len(res.applied_changes) == 0, "错误路径或非法枚举不应被应用！"
        assert len(res.rejected_changes) == 2, "未能精确记录 2 个拒绝操作！"
        print(" -> 错误路径跨域与非法枚举严格拦截验证通过！")

    print("\n[测试 3/6] 验证客户端自报来源防篡改 (外部接口强制 external_client)...")
    from httpx import ASGITransport, AsyncClient
    from app.main import app
    from app.database import session as session_module

    # 依赖注入覆盖为测试会话
    async def override_get_db():
        async with TestSession() as s:
            yield s

    app.dependency_overrides[session_module.get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 模拟外部客户端提交试图自称 system 来篡改金钱
        hacker_payload = {
            "base_revision": 5,
            "source": "system",
            "operations": [
                {"op": "delta", "path": "/player/money", "value": 10000, "reason": "作弊加钱"}
            ]
        }
        resp = await client.post("/api/variables/patch", json=hacker_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["applied_changes"]) == 0
        assert len(data["rejected_changes"]) == 1
        assert "越权操作被拒绝" in data["rejected_changes"][0]["reject_reason"]
        print(" -> 客户端自报来源被成功强制重写并拦截越权系统变量修改！")

    print("\n[测试 4/6] 验证手机朋友圈防重复刷好感机制...")
    async with TestSession() as session:
        from app.api.phone import like_moment
        # 第一次点赞
        res1 = await like_moment("m_post_1", db=session)
        assert res1["liked"] is True
        rel_1 = (await session.execute(select(Relationship).where(Relationship.character_id == "lin_yuqing"))).scalar_one()
        aff_after_like = rel_1.affection
        assert aff_after_like == 36, f"首次点赞好感应+1，当前为: {aff_after_like}"

        # 取消点赞
        res2 = await like_moment("m_post_1", db=session)
        assert res2["liked"] is False

        # 再次点赞 (不能重复增加好感)
        res3 = await like_moment("m_post_1", db=session)
        assert res3["liked"] is True
        rel_2 = (await session.execute(select(Relationship).where(Relationship.character_id == "lin_yuqing"))).scalar_one()
        assert rel_2.affection == 36, f"防刷生效失败！好感度被重复增加至: {rel_2.affection}"
        print(" -> 朋友圈防刷好感机制生效，取消后再点赞绝不重复增加好感！")

    print("\n[测试 5/6] 验证真·全量状态存档与原子重建恢复...")
    async with TestSession() as session:
        from app.api.saves import save_game_to_slot, load_game_from_slot
        # 保存当前状态 (包含玩家金钱450、体力80、熟悉度40)
        await save_game_to_slot(1, title="考前复习点", db=session)

        # 篡改玩家金钱为 0、体力为 10、好感度为 99
        p = (await session.execute(select(Player).limit(1))).scalar_one()
        p.money = 0
        p.energy = 10
        rel = (await session.execute(select(Relationship).where(Relationship.character_id == "lin_yuqing"))).scalar_one()
        rel.affection = 99
        rel.familiarity = 99
        await session.commit()

        # 读档恢复
        await load_game_from_slot(1, db=session)

        # 验证全表字段彻底还原
        p_restored = (await session.execute(select(Player).limit(1))).scalar_one()
        assert p_restored.money == 450, f"玩家金钱未恢复: {p_restored.money}"
        assert p_restored.energy == 80, f"玩家体力未恢复: {p_restored.energy}"

        rel_restored = (await session.execute(select(Relationship).where(Relationship.character_id == "lin_yuqing"))).scalar_one()
        assert rel_restored.affection == 36, f"好感度未恢复: {rel_restored.affection}"
        assert rel_restored.familiarity == 40, f"熟悉度未恢复: {rel_restored.familiarity}"
        print(" -> 全量存档与原子重建恢复验证通过，玩家属性、好感、熟悉度全表一致！")

    print("\n[测试 6/6] 验证开启新游戏会话接口 (POST /api/game/new)...")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        new_resp = await client.post("/api/game/new")
        assert new_resp.status_code == 200
        snap = new_resp.json()["snapshot"]
        assert snap["revision"] == 1
        assert snap["world"]["day_number"] == 1
        assert snap["world"]["weekday"] == "星期三"
        assert snap["world"]["player_location"] == "library"
        assert snap["player"]["money"] == 300
        assert snap["characters"]["lin_yuqing"]["relationship"]["affection"] == 25
        print(" -> 开启新篇章接口验证通过，世界、角色与版本号原子归位！")

    # 清除依赖覆盖与清理测试库
    app.dependency_overrides.clear()
    await test_engine.dispose()
    if TEST_DB_FILE.exists():
        TEST_DB_FILE.unlink()

    print("\n" + "=" * 65)
    print("[ALL PASSED] V0.2.1 状态一致性、版本乐观锁与全量存档测试全量通过！")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(run_v021_suite())
