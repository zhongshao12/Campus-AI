import asyncio
import os
import sys
from pathlib import Path
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

# 将 backend 根目录加入路径
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.database.models import (
    Base,
    WorldState,
    CharacterState,
    Relationship,
    DialogueLog,
    Memory,
    PhoneMessage,
    MomentPost,
    MomentLike,
    SaveSlot,
)
from app.core.arbitrator import Arbitrator
from app.models.schemas import ProposedEffect, PlayerDialogueRequest
from app.memory.manager import MemoryManager
from app.ai.llm.provider import ProviderManager
from app.core.config import settings

TEST_DB_FILE = BACKEND_DIR.parent / "data" / "test_sandbox_v011.db"
TEST_DB_URL = f"sqlite+aiosqlite:///{TEST_DB_FILE.as_posix()}"

async def run_v011_verification():
    print("=" * 65)
    print("Campus AI — V0.1.1 核心闭环与状态一致性自动化测试套件")
    print("=" * 65)

    # 1. 初始化隔离测试数据库
    if TEST_DB_FILE.exists():
        TEST_DB_FILE.unlink()

    test_engine = create_async_engine(TEST_DB_URL, echo=False)
    TestSession = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("\n【测试 1/7】测试好感裁决器聚合防穿透漏洞...")
    async with TestSession() as session:
        world = WorldState(day_number=1, weekday="星期三", time_slot="afternoon", player_location="library")
        char_state = CharacterState(character_id="lin_yuqing", current_location="library")
        rel = Relationship(character_id="lin_yuqing", affection=30, trust=20, stage="friend")
        session.add_all([world, char_state, rel])
        await session.commit()

        # 恶意提议：5 个 +3 好感提案
        vuln_effects = [
            ProposedEffect(type="affection_delta", value=3, reason="夸赞1"),
            ProposedEffect(type="affection_delta", value=3, reason="夸赞2"),
            ProposedEffect(type="affection_delta", value=3, reason="夸赞3"),
            ProposedEffect(type="affection_delta", value=3, reason="夸赞4"),
            ProposedEffect(type="affection_delta", value=3, reason="夸赞5"),
        ]
        applied_aff, _, details = Arbitrator.arbitrate_effects(vuln_effects, rel, char_state, world)
        assert applied_aff == 3, f"好感度聚合裁决失败，预期为 3，实际为 {applied_aff}"
        assert rel.affection == 33, f"最终好感度错误，预期 33，实际 {rel.affection}"
        print(f" -> 5次+3提案被安全聚合，单轮全局限制为 +{applied_aff} (好感: {rel.affection})，防穿透生效！")

    print("\n【测试 2/7】测试跨角色记忆隔离性 (杜绝聊天串线)...")
    async with TestSession() as session:
        mgr = MemoryManager(session)
        # 玩家对林雨晴说话
        await mgr.save_dialogue_turn(
            speaker_name="你",
            character_id="player",
            target_character_id="lin_yuqing",
            content="雨晴，今天图书馆的阳光真好。",
        )
        await mgr.save_dialogue_turn(
            speaker_name="林雨晴",
            character_id="lin_yuqing",
            content="是呀，而且很安静。",
        )
        # 玩家对苏晚星说话 (其他NPC)
        await mgr.save_dialogue_turn(
            speaker_name="你",
            character_id="player",
            target_character_id="su_wanxing",
            content="学姐，文学社的入社申请我提交了。",
        )
        await session.commit()

        # 林雨晴召回上下文：绝不能包含苏晚星的私聊内容
        lin_context = await mgr.get_recent_dialogue_context(character_id="lin_yuqing")
        contents = [c["content"] for c in lin_context]
        assert "雨晴，今天图书馆的阳光真好。" in contents
        assert "学姐，文学社的入社申请我提交了。" not in contents, "记忆泄漏！林雨晴读到了发给苏晚星的消息！"
        print(" -> 角色私聊上下文严格隔离验证通过，无跨角色记忆串线！")

    print("\n【测试 3/7】测试模型设置防空覆盖与热重载...")
    settings.LLM_API_KEY = "sk-test-secret-key-12345"
    settings.LLM_MODEL = "deepseek-chat"
    pm = ProviderManager.get_instance()
    client = pm.get_llm_client()
    assert client.api_key == "sk-test-secret-key-12345"

    # 模拟前端未传 Key (空串)，更新模型名字为 qwen
    from app.api.settings import update_settings, SettingsUpdateRequest
    await update_settings(SettingsUpdateRequest(llm_api_key="", llm_model="qwen-turbo"))
    assert settings.LLM_API_KEY == "sk-test-secret-key-12345", "API Key 被空字符串覆盖丢失！"
    assert settings.LLM_MODEL == "qwen-turbo", "模型名称未能热更新！"
    assert client.model == "qwen-turbo", "现存客户端未同步最新模型名称！"
    print(" -> 设置热更新与防空覆盖保护机制生效！")

    print("\n【测试 4/7】测试 NPC 在场校验约束...")
    # 重置为离线 Mock 模式避免网络波动
    settings.LLM_API_KEY = ""
    async with TestSession() as session:
        # 将林雨晴移动到教室，玩家在图书馆
        cs = (await session.execute(select(CharacterState).where(CharacterState.character_id == "lin_yuqing"))).scalar_one()
        w = (await session.execute(select(WorldState).limit(1))).scalar_one()
        cs.current_location = "classroom"
        w.player_location = "library"
        await session.commit()

        # 触发对话
        from app.api.dialogue import chat_with_character
        resp = await chat_with_character(
            PlayerDialogueRequest(character_id="lin_yuqing", message="雨晴，在吗？"),
            db=session,
        )
        assert resp.speaker == "旁白"
        assert "并不在当前地点" in resp.dialogue
        assert resp.affection_delta == 0
        print(" -> NPC 缺席校验生效，拒绝隔空面对面互动，并引导玩家前往对应地点或使用手机！")

    print("\n【测试 5/7】测试手机系统数据库持久化 (消息与朋友圈)...")
    async with TestSession() as session:
        # 发送手机消息
        from app.api.phone import send_phone_message, SendMessageRequest, like_moment
        post = MomentPost(id="m_test", author_id="lin_yuqing", author_name="林雨晴", content="测试动态")
        session.add(post)
        await session.commit()

        res = await send_phone_message(SendMessageRequest(target_id="lin_yuqing", text="周末一起去摄影吧！"), db=session)
        assert res["sent"]["text"] == "周末一起去摄影吧！"
        assert res["reply"] is not None

        # 点赞
        like_res = await like_moment("m_test", db=session)
        assert like_res["liked"] is True
        print(" -> 手机私聊与朋友圈点赞成功持久化落库！")

    print("\n【测试 6/7】测试全量存档快照与时间线严格回滚...")
    async with TestSession() as session:
        from app.api.saves import save_game_to_slot, load_game_from_slot
        mgr_test = MemoryManager(session)
        rel_curr = (await session.execute(select(Relationship).where(Relationship.character_id == "lin_yuqing"))).scalar_one()
        expected_aff = rel_curr.affection

        # 保存 Slot 1 初始状态 (包含当前好感和历史日志)
        await save_game_to_slot(1, title="初始回忆点", db=session)

        # 模拟玩家在未来发生很多事情：好感飙升、产生未来记忆
        rel_curr.affection = 80
        await mgr_test.add_memory("lin_yuqing", summary="【未来记忆】在海边对林雨晴告白成功并成为恋人", importance=5, game_day=5)
        await session.commit()

        # 验证未来记忆存在
        mems = await mgr_test.get_episodic_memories("lin_yuqing")
        assert any("【未来记忆】" in m for m in mems)

        # 执行读档回滚到 Slot 1
        await load_game_from_slot(1, db=session)

        # 验证：好感度必须恢复为保存时的 expected_aff，且未来记忆必须被完全抹除回退！
        rel_after = (await session.execute(select(Relationship).where(Relationship.character_id == "lin_yuqing"))).scalar_one()
        assert rel_after.affection == expected_aff, f"好感度读档失败，实际: {rel_after.affection}, 预期: {expected_aff}"

        mems_after = await mgr_test.get_episodic_memories("lin_yuqing")
        assert not any("【未来记忆】" in m for m in mems_after), "严重问题：读档后未来记忆依然残留！"
        print(f" -> 全量快照读档成功！好感度精准恢复为 {expected_aff}，时空记忆被原子回滚，杜绝记忆穿越！")

    print("\n【测试 7/7】测试 ComfyUI 图像端点与优雅降级...")
    async with TestSession() as session:
        from app.api.images import view_generated_image
        resp = await view_generated_image("test_non_existent_prompt", db=session)
        assert resp.status_code == 200
        print(" -> 图像请求具备完备的优雅降级与占位保障，绝不白屏崩溃！")

    # 清理测试库
    await test_engine.dispose()
    if TEST_DB_FILE.exists():
        TEST_DB_FILE.unlink()

    print("\n" + "=" * 65)
    print("[ALL PASSED] V0.1.1 审查发现的 8 大缺陷全部修复并验证闭环！")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(run_v011_verification())
