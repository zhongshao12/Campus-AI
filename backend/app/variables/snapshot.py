from typing import Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database.models import (
    GameStateRevision,
    WorldState,
    Player,
    CharacterState,
    Relationship,
    EventRecord,
)
from .schemas import VariableSnapshot

class SnapshotBuilder:
    """
    状态快照构建器
    从 SQLite 核心实体表聚合提取单一真源的 stat_data 变量快照
    """

    @classmethod
    async def build_snapshot(cls, db: AsyncSession) -> VariableSnapshot:
        # 1. 版本号
        rev_res = await db.execute(select(GameStateRevision).limit(1))
        rev = rev_res.scalar_one_or_none()
        current_rev = rev.revision if rev else 1
        schema_v = rev.schema_version if rev else 1

        # 2. 玩家
        p_res = await db.execute(select(Player).limit(1))
        player = p_res.scalar_one_or_none()
        player_dict = {
            "name": player.name if player else "你",
            "energy": getattr(player, "energy", 100),
            "mood": getattr(player, "mood", "happy"),
            "money": getattr(player, "money", 300),
            "inventory": getattr(player, "inventory", {}),
        }

        # 3. 世界
        w_res = await db.execute(select(WorldState).limit(1))
        world = w_res.scalar_one_or_none()
        world_dict = {
            "day_number": world.day_number if world else 1,
            "weekday": world.weekday if world else "星期三",
            "time_slot": world.time_slot if world else "afternoon",
            "weather": world.weather if world else "sunny",
            "player_location": world.player_location if world else "library",
            "turns_in_current_scene": world.turns_in_current_scene if world else 0,
        }

        # 4. 角色与关系
        cs_res = await db.execute(select(CharacterState))
        char_states = {c.character_id: c for c in cs_res.scalars().all()}

        rel_res = await db.execute(select(Relationship))
        relationships = {r.character_id: r for r in rel_res.scalars().all()}

        characters_dict: Dict[str, Any] = {}
        all_char_ids = set(char_states.keys()).union(set(relationships.keys()))
        for cid in all_char_ids:
            cs = char_states.get(cid)
            rel = relationships.get(cid)
            characters_dict[cid] = {
                "state": {
                    "current_location": cs.current_location if cs else "unknown",
                    "current_mood": cs.current_mood if cs else "neutral",
                    "fatigue": cs.fatigue if cs else 0,
                    "is_busy": cs.is_busy if cs else False,
                },
                "relationship": {
                    "affection": rel.affection if rel else 0,
                    "trust": rel.trust if rel else 0,
                    "familiarity": getattr(rel, "familiarity", 20) if rel else 20,
                    "stage": rel.stage if rel else "acquaintance",
                    "flags": rel.flags if rel else {},
                }
            }

        # 5. 事件
        ev_res = await db.execute(select(EventRecord))
        events_dict = {e.event_id: {"status": e.status, "day": e.triggered_day, "details": e.details} for e in ev_res.scalars().all()}

        return VariableSnapshot(
            schema_version=schema_v,
            revision=current_rev,
            world=world_dict,
            player=player_dict,
            characters=characters_dict,
            events=events_dict,
            system={
                "turns_in_scene": world.turns_in_current_scene if world else 0,
            }
        )
