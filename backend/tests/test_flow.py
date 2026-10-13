import asyncio
import os
import sys
from pathlib import Path

# 将 backend 加入模块搜索路径
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.database.session import init_db, AsyncSessionLocal
from app.database.models import WorldState, Relationship, CharacterState, Player
from app.core.arbitrator import Arbitrator
from app.models.schemas import ProposedEffect, PlayerDialogueRequest
from app.memory.manager import MemoryManager
from app.ai.llm.client import LLMClient
from sqlalchemy import select

async def run_backend_verification():
    print("=" * 60)
    print("【1/5】测试数据库初始化与种子数据...")
    await init_db()
    async with AsyncSessionLocal() as session:
        world = (await session.execute(select(WorldState).limit(1))).scalar_one_or_none()
        assert world is not None, "WorldState 初始化失败"
        print(f" -> 世界状态正常: 第{world.day_number}天 {world.weekday} {world.time_slot} 地点:{world.player_location}")

        rel = (await session.execute(select(Relationship).where(Relationship.character_id == "lin_yuqing"))).scalar_one_or_none()
        assert rel is not None, "Relationship 初始化失败"
        print(f" -> 初始好感正常: 林雨晴 好感度={rel.affection}, 关系阶段={rel.stage}")

    print("\n【2/5】测试规则裁决器 (Arbitrator) 边界保护...")
    async with AsyncSessionLocal() as session:
        rel = (await session.execute(select(Relationship).where(Relationship.character_id == "lin_yuqing"))).scalar_one_or_none()
        char_state = (await session.execute(select(CharacterState).where(CharacterState.character_id == "lin_yuqing"))).scalar_one_or_none()
        world = (await session.execute(select(WorldState).limit(1))).scalar_one_or_none()

        # 模拟 AI 试图非法提议 +99 好感
        extreme_effects = [ProposedEffect(type="affection_delta", value=99, reason="极端数值攻击")]
        aff_delta, _, details = Arbitrator.arbitrate_effects(extreme_effects, rel, char_state, world)
        assert aff_delta <= Arbitrator.MAX_AFFECTION_DELTA, f"裁决器未能限制好感度变动: {aff_delta}"
        print(f" -> 极端数值 +99 被成功裁决裁剪为: +{aff_delta} (当前好感: {rel.affection})")

    print("\n【3/5】测试多级记忆系统 (MemoryManager)...")
    async with AsyncSessionLocal() as session:
        mgr = MemoryManager(session)
        # 写入一条情节记忆
        mem = await mgr.add_memory(
            character_id="lin_yuqing",
            summary="玩家在图书馆向林雨晴推荐了村上春树的短篇小说集，两人聊得十分投机。",
            importance=4,
            location="大学图书馆",
            game_day=1,
        )
        await session.commit()
        
        # 召回情节记忆
        memories = await mgr.get_episodic_memories("lin_yuqing", limit=3)
        assert len(memories) > 0, "未能检索出情节记忆"
        print(f" -> 成功召回情节记忆:\n    {memories[0]}")

    print("\n【4/5】测试 LLM 结构化对话与角色表现...")
    llm = LLMClient()
    mock_resp = await llm.generate_dialogue(
        character_id="lin_yuqing",
        player_message="雨晴，这本小说我也很喜欢，里面的句子好美。",
        affection=28,
        trust=20,
        stage="friend",
        location_name="大学图书馆",
        time_slot_name="下午",
        weather="晴天",
        episodic_memories=["- [第1天 在大学图书馆] 玩家在图书馆向林雨晴推荐了村上春树的短篇小说集"],
        recent_history=[],
    )
    assert mock_resp.speaker == "林雨晴"
    assert mock_resp.expression in ["neutral", "happy", "blush", "surprised", "thinking", "pout", "sad"]
    print(f" -> 角色对白: [{mock_resp.speaker}] {mock_resp.dialogue}")
    print(f" -> 立绘表情: {mock_resp.expression} | 动作: {mock_resp.action} | 心理: {mock_resp.inner_thought}")
    print(f" -> 提议效果: {mock_resp.proposed_effects}")

    print("\n【5/5】测试存档快照与状态恢复...")
    async with AsyncSessionLocal() as session:
        from app.api.saves import save_game_to_slot, load_game_from_slot
        # 修改好感度后存入 1 号槽
        rel = (await session.execute(select(Relationship).where(Relationship.character_id == "lin_yuqing"))).scalar_one_or_none()
        old_aff = rel.affection
        rel.affection = 42
        await session.commit()

        await save_game_to_slot(slot_index=1, title="图书馆温馨初遇", db=session)
        print(" -> 已保存快照到 1 号槽位 (好感度=42)")

        # 篡改数据
        rel.affection = 10
        await session.commit()
        print(" -> 将当前好感度临时篡改为 10")

        # 读档恢复
        await load_game_from_slot(slot_index=1, db=session)
        rel_restored = (await session.execute(select(Relationship).where(Relationship.character_id == "lin_yuqing"))).scalar_one_or_none()
        assert rel_restored.affection == 42, f"读档恢复失败，期望 42，实际 {rel_restored.affection}"
        print(f" -> 读档成功！好感度完美恢复为: {rel_restored.affection}")

    print("=" * 60)
    print("【测试结果】后端所有核心模块校验全部通过！")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_backend_verification())
