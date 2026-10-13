from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from ..database.session import get_db
from ..database.models import SaveSlot, WorldState, CharacterState, Relationship, DialogueLog, Memory
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
    title: str = "自动/手动存档",
    db: AsyncSession = Depends(get_db),
):
    """将当前完整游戏状态打包快照存入指定槽位"""
    if slot_index < 1 or slot_index > 10:
        raise HTTPException(status_code=400, detail="槽位编号必须在 1~10 之间")

    # 1. 抓取世界
    w_res = await db.execute(select(WorldState).limit(1))
    world = w_res.scalar_one_or_none()

    # 2. 抓取角色与关系
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

    snapshot = {
        "world": {
            "day_number": world.day_number if world else 1,
            "weekday": world.weekday if world else "星期三",
            "time_slot": world.time_slot if world else "afternoon",
            "weather": world.weather if world else "sunny",
            "player_location": world.player_location if world else "library",
        },
        "relationships": relationships,
        "char_states": char_states,
        "preview": {
            "day": world.day_number if world else 1,
            "time_slot": world.time_slot if world else "afternoon",
            "location": world.player_location if world else "library",
            "lin_affection": next((r["affection"] for r in relationships if r["character_id"] == "lin_yuqing"), 0),
        }
    }

    # 查询是否存在该槽位
    slot_res = await db.execute(select(SaveSlot).where(SaveSlot.slot_index == slot_index))
    slot = slot_res.scalar_one_or_none()
    if not slot:
        slot = SaveSlot(slot_index=slot_index, title=title, snapshot=snapshot)
        db.add(slot)
    else:
        slot.title = title
        slot.snapshot = snapshot

    await db.commit()
    return {"message": f"成功保存到槽位 {slot_index}", "slot_index": slot_index}

@router.post("/load/{slot_index}")
async def load_game_from_slot(slot_index: int, db: AsyncSession = Depends(get_db)):
    """从指定槽位恢复游戏完整状态快照"""
    slot_res = await db.execute(select(SaveSlot).where(SaveSlot.slot_index == slot_index))
    slot = slot_res.scalar_one_or_none()
    if not slot:
        raise HTTPException(status_code=404, detail="该存档槽位为空")

    data = slot.snapshot

    # 1. 恢复世界
    w_data = data.get("world", {})
    w_res = await db.execute(select(WorldState).limit(1))
    world = w_res.scalar_one_or_none()
    if world:
        world.day_number = w_data.get("day_number", 1)
        world.weekday = w_data.get("weekday", "星期三")
        world.time_slot = w_data.get("time_slot", "afternoon")
        world.weather = w_data.get("weather", "sunny")
        world.player_location = w_data.get("player_location", "library")
        world.turns_in_current_scene = 0

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

    await db.commit()
    return {"message": f"成功加载槽位 {slot_index} 的游戏进度"}
