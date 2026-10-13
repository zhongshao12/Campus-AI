from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from ..database.session import get_db
from ..database.models import (
    SaveSlot,
    WorldState,
    CharacterState,
    Relationship,
    DialogueLog,
    Memory,
    PhoneMessage,
)
from ..models.schemas import SaveSlotInfo

router = APIRouter()

@router.get("/slots")
async def list_save_slots(db: AsyncSession = Depends(get_db)):
    """获取所有存档槽位列表"""
    res = await db.execute(select(SaveSlot).order_by(SaveSlot.slot_index))
    slots = res.scalars().all()
    results = []
    for s in slots:
        results.append({
            "slot_index": s.slot_index,
            "title": s.title,
            "saved_at": s.saved_at.strftime("%Y-%m-%d %H:%M:%S") if s.saved_at else "",
            "preview": s.snapshot.get("preview", {}),
        })
    return results

@router.post("/save/{slot_index}")
async def save_game_to_slot(
    slot_index: int,
    title: str = "手动存档",
    db: AsyncSession = Depends(get_db),
):
    """
    全量状态快照存档 (V0.1.1 强化版)
    打包：世界状态 + 角色与关系 + 全部对话历史 + 全部情节记忆 + 手机消息
    彻底解决读档后记忆穿越问题。
    """
    if slot_index < 1 or slot_index > 10:
        raise HTTPException(status_code=400, detail="槽位编号必须在 1~10 之间")

    # 1. 世界状态
    w_res = await db.execute(select(WorldState).limit(1))
    world = w_res.scalar_one_or_none()

    # 2. 关系与状态
    rel_res = await db.execute(select(Relationship))
    relationships = [
        {"character_id": r.character_id, "affection": r.affection, "trust": r.trust, "stage": r.stage, "flags": r.flags}
        for r in rel_res.scalars().all()
    ]

    cs_res = await db.execute(select(CharacterState))
    char_states = [
        {"character_id": c.character_id, "current_location": c.current_location, "current_mood": c.current_mood, "fatigue": c.fatigue}
        for c in cs_res.scalars().all()
    ]

    # 3. 对话历史完整快照
    dlg_res = await db.execute(select(DialogueLog).order_by(DialogueLog.id.asc()))
    dialogue_logs = [
        {
            "character_id": d.character_id,
            "target_character_id": d.target_character_id,
            "speaker_name": d.speaker_name,
            "content": d.content,
            "emotion": d.emotion,
            "expression": d.expression,
            "location": d.location,
            "game_day": d.game_day,
            "game_time_slot": d.game_time_slot,
        }
        for d in dlg_res.scalars().all()
    ]

    # 4. 情节记忆完整快照
    mem_res = await db.execute(select(Memory).order_by(Memory.id.asc()))
    memories = [
        {
            "character_id": m.character_id,
            "memory_type": m.memory_type,
            "summary": m.summary,
            "keywords": m.keywords,
            "importance": m.importance,
            "location": m.location,
            "game_day": m.game_day,
        }
        for m in mem_res.scalars().all()
    ]

    # 5. 手机消息完整快照
    msg_res = await db.execute(select(PhoneMessage).order_by(PhoneMessage.id.asc()))
    phone_messages = [
        {
            "contact_id": pm.contact_id,
            "sender_id": pm.sender_id,
            "sender_name": pm.sender_name,
            "text": pm.text,
            "msg_type": pm.msg_type,
            "image_url": pm.image_url,
        }
        for pm in msg_res.scalars().all()
    ]

    snapshot = {
        "world": {
            "day_number": world.day_number if world else 1,
            "weekday": world.weekday if world else "星期三",
            "time_slot": world.time_slot if world else "afternoon",
            "weather": world.weather if world else "sunny",
            "player_location": world.player_location if world else "library",
            "turns_in_current_scene": world.turns_in_current_scene if world else 0,
        },
        "relationships": relationships,
        "char_states": char_states,
        "dialogue_logs": dialogue_logs,
        "memories": memories,
        "phone_messages": phone_messages,
        "preview": {
            "day": world.day_number if world else 1,
            "time_slot": world.time_slot if world else "afternoon",
            "location": world.player_location if world else "library",
            "lin_affection": next((r["affection"] for r in relationships if r["character_id"] == "lin_yuqing"), 0),
        }
    }

    slot_res = await db.execute(select(SaveSlot).where(SaveSlot.slot_index == slot_index))
    slot = slot_res.scalar_one_or_none()
    if not slot:
        slot = SaveSlot(slot_index=slot_index, title=title, snapshot=snapshot)
        db.add(slot)
    else:
        slot.title = title
        slot.snapshot = snapshot

    await db.commit()
    return {"message": f"成功保存完整状态到槽位 {slot_index}", "slot_index": slot_index}

@router.post("/load/{slot_index}")
async def load_game_from_slot(slot_index: int, db: AsyncSession = Depends(get_db)):
    """
    原子还原指定槽位的完整快照
    不仅还原世界和数值，同时回滚对话日志与记忆，彻底保证时间线一致性。
    """
    slot_res = await db.execute(select(SaveSlot).where(SaveSlot.slot_index == slot_index))
    slot = slot_res.scalar_one_or_none()
    if not slot:
        raise HTTPException(status_code=404, detail="该存档槽位为空")

    data = slot.snapshot

    # 1. 恢复世界状态
    w_data = data.get("world", {})
    w_res = await db.execute(select(WorldState).limit(1))
    world = w_res.scalar_one_or_none()
    if world:
        world.day_number = w_data.get("day_number", 1)
        world.weekday = w_data.get("weekday", "星期三")
        world.time_slot = w_data.get("time_slot", "afternoon")
        world.weather = w_data.get("weather", "sunny")
        world.player_location = w_data.get("player_location", "library")
        world.turns_in_current_scene = w_data.get("turns_in_current_scene", 0)

    # 2. 恢复关系
    for r_item in data.get("relationships", []):
        rel_res = await db.execute(select(Relationship).where(Relationship.character_id == r_item["character_id"]))
        rel = rel_res.scalar_one_or_none()
        if rel:
            rel.affection = r_item.get("affection", 0)
            rel.trust = r_item.get("trust", 0)
            rel.stage = r_item.get("stage", "acquaintance")
            rel.flags = r_item.get("flags", {})

    # 3. 恢复角色状态
    for c_item in data.get("char_states", []):
        cs_res = await db.execute(select(CharacterState).where(CharacterState.character_id == c_item["character_id"]))
        cs = cs_res.scalar_one_or_none()
        if cs:
            cs.current_location = c_item.get("current_location", "library")
            cs.current_mood = c_item.get("current_mood", "neutral")
            cs.fatigue = c_item.get("fatigue", 0)

    # 4. 关键：回滚并精准重构对话历史
    await db.execute(delete(DialogueLog))
    for d_item in data.get("dialogue_logs", []):
        d_rec = DialogueLog(
            character_id=d_item["character_id"],
            target_character_id=d_item.get("target_character_id"),
            speaker_name=d_item["speaker_name"],
            content=d_item["content"],
            emotion=d_item.get("emotion", "neutral"),
            expression=d_item.get("expression", "neutral"),
            location=d_item.get("location", "library"),
            game_day=d_item.get("game_day", 1),
            game_time_slot=d_item.get("game_time_slot", "afternoon"),
        )
        db.add(d_rec)

    # 5. 关键：回滚并精准重构情节记忆
    await db.execute(delete(Memory))
    for m_item in data.get("memories", []):
        m_rec = Memory(
            character_id=m_item["character_id"],
            memory_type=m_item.get("memory_type", "episodic"),
            summary=m_item["summary"],
            keywords=m_item.get("keywords", ""),
            importance=m_item.get("importance", 3),
            location=m_item.get("location"),
            game_day=m_item.get("game_day", 1),
        )
        db.add(m_rec)

    # 6. 回滚并恢复手机消息
    if "phone_messages" in data:
        await db.execute(delete(PhoneMessage))
        for p_item in data.get("phone_messages", []):
            p_rec = PhoneMessage(
                contact_id=p_item["contact_id"],
                sender_id=p_item["sender_id"],
                sender_name=p_item["sender_name"],
                text=p_item["text"],
                msg_type=p_item.get("msg_type", "text"),
                image_url=p_item.get("image_url"),
            )
            db.add(p_rec)

    await db.commit()
    return {"message": f"成功加载槽位 {slot_index} 并完美还原世界状态、记忆与历史时间线"}
