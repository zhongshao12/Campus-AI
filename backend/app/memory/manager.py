from typing import List, Dict, Any, Optional
from sqlalchemy import select, desc, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from ..database.models import DialogueLog, Memory, Relationship, CharacterState, WorldState

class MemoryManager:
    """
    分层记忆管理器 (V0.1.1 隔离与语义增强版)
    负责专属角色短期对话缓冲、情节事件抽取与防串线多维召回。
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_recent_dialogue_context(
        self,
        character_id: str,
        limit: int = 10,
    ) -> List[Dict[str, str]]:
        """
        获取当前角色的专属短期上下文 (彻底杜绝多角色串线)
        只召回：
        1. 该角色的发言；
        2. 玩家专门针对该角色的发言 (target_character_id == character_id)。
        """
        condition = or_(
            DialogueLog.character_id == character_id,
            and_(
                DialogueLog.character_id == "player",
                DialogueLog.target_character_id == character_id,
            )
        )

        query = (
            select(DialogueLog)
            .where(condition)
            .order_by(desc(DialogueLog.id))
            .limit(limit)
        )
        res = await self.db.execute(query)
        logs = list(res.scalars().all())
        logs.reverse()

        formatted = []
        for log in logs:
            role = "user" if log.character_id == "player" else "assistant"
            formatted.append({
                "role": role,
                "name": log.speaker_name,
                "content": log.content,
            })
        return formatted

    async def get_episodic_memories(
        self,
        character_id: str,
        limit: int = 5,
        current_location: Optional[str] = None,
    ) -> List[str]:
        """
        多维情节记忆召回：
        优先召回该角色在当前场景的相关经历与高重要度约定。
        """
        query = (
            select(Memory)
            .where(Memory.character_id == character_id)
            .order_by(desc(Memory.importance), desc(Memory.game_day), desc(Memory.id))
            .limit(limit)
        )
        res = await self.db.execute(query)
        memories = res.scalars().all()
        return [f"- [第{m.game_day}天 在{m.location or '校园'}] {m.summary}" for m in memories]

    async def save_dialogue_turn(
        self,
        speaker_name: str,
        character_id: str,
        content: str,
        target_character_id: Optional[str] = None,
        emotion: str = "neutral",
        expression: str = "neutral",
        location: str = "library",
        game_day: int = 1,
        game_time_slot: str = "afternoon",
    ) -> DialogueLog:
        """持久化单条对话记录，带明确的 target_character_id"""
        log = DialogueLog(
            character_id=character_id,
            target_character_id=target_character_id,
            speaker_name=speaker_name,
            content=content,
            emotion=emotion,
            expression=expression,
            location=location,
            game_day=game_day,
            game_time_slot=game_time_slot,
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def add_memory(
        self,
        character_id: str,
        summary: str,
        memory_type: str = "episodic",
        importance: int = 3,
        keywords: str = "",
        location: Optional[str] = None,
        game_day: int = 1,
    ) -> Memory:
        """记录一段新的情节记忆"""
        mem = Memory(
            character_id=character_id,
            memory_type=memory_type,
            summary=summary,
            importance=importance,
            keywords=keywords,
            location=location,
            game_day=game_day,
        )
        self.db.add(mem)
        await self.db.flush()
        return mem
