from typing import List, Dict, Any, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from ..database.models import DialogueLog, Memory, Relationship, CharacterState, WorldState

class MemoryManager:
    """
    分层记忆管理器
    负责多级记忆读写：短期上下文缓冲、情节事件抽取与结构化 Prompt 注入。
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_recent_dialogue_context(
        self,
        character_id: str,
        limit: int = 10,
    ) -> List[Dict[str, str]]:
        """获取最近几轮对话，作为短期连续上下文"""
        query = (
            select(DialogueLog)
            .where(
                (DialogueLog.character_id == character_id) | 
                (DialogueLog.character_id == "player")
            )
            .order_by(desc(DialogueLog.id))
            .limit(limit)
        )
        res = await self.db.execute(query)
        logs = list(res.scalars().all())
        logs.reverse()  # 恢复正序时间流

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
    ) -> List[str]:
        """获取与该角色相关的情节记忆（重大经历、约定、印象）"""
        query = (
            select(Memory)
            .where(Memory.character_id == character_id)
            .order_by(desc(Memory.importance), desc(Memory.id))
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
        emotion: str = "neutral",
        expression: str = "neutral",
        location: str = "library",
        game_day: int = 1,
        game_time_slot: str = "afternoon",
    ) -> DialogueLog:
        """持久化单条对话记录"""
        log = DialogueLog(
            character_id=character_id,
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
