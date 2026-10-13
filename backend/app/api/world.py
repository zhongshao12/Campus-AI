from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database.session import get_db
from ..database.models import WorldState, CharacterState
from ..models.schemas import WorldStateResponse, AdvanceTimeRequest
from ..core.config import get_world_config, get_character_config

router = APIRouter()

TIME_SLOT_SEQUENCE = ["morning", "noon", "afternoon", "dusk", "night"]
WEEKDAY_SEQUENCE = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

@router.get("/state", response_model=WorldStateResponse)
async def get_current_world_state(db: AsyncSession = Depends(get_db)):
    """获取当前游戏世界状态与场景信息"""
    world_res = await db.execute(select(WorldState).limit(1))
    world = world_res.scalar_one_or_none()
    if not world:
        raise HTTPException(status_code=500, detail="世界未初始化")

    world_cfg = get_world_config()
    loc_meta = next(
        (l for l in world_cfg.get("locations", []) if l["id"] == world.player_location),
        {"name": "校园", "description": "阳光明媚的校园。"}
    )

    # 查找当前地点在场的角色
    chars_res = await db.execute(
        select(CharacterState.character_id).where(CharacterState.current_location == world.player_location)
    )
    present_chars = [c for c in chars_res.scalars().all()]

    return WorldStateResponse(
        day_number=world.day_number,
        weekday=world.weekday,
        time_slot=world.time_slot,
        weather=world.weather,
        player_location=world.player_location,
        location_name=loc_meta.get("name", "校园"),
        location_description=loc_meta.get("description", ""),
        present_characters=present_chars,
    )

@router.post("/move/{location_id}", response_model=WorldStateResponse)
async def move_to_location(location_id: str, db: AsyncSession = Depends(get_db)):
    """玩家在校园各地移动"""
    world_res = await db.execute(select(WorldState).limit(1))
    world = world_res.scalar_one_or_none()
    if not world:
        raise HTTPException(status_code=500, detail="世界未初始化")

    world_cfg = get_world_config()
    valid_ids = [l["id"] for l in world_cfg.get("locations", [])]
    if location_id not in valid_ids:
        raise HTTPException(status_code=400, detail=f"无效的地点ID: {location_id}")

    world.player_location = location_id
    world.turns_in_current_scene = 0
    await db.commit()

    return await get_current_world_state(db)

@router.post("/advance_time", response_model=WorldStateResponse)
async def advance_time_slot(
    req: AdvanceTimeRequest = None,
    db: AsyncSession = Depends(get_db),
):
    """推进时间段（morning -> noon -> afternoon -> dusk -> night -> 次日早晨）"""
    world_res = await db.execute(select(WorldState).limit(1))
    world = world_res.scalar_one_or_none()
    if not world:
        raise HTTPException(status_code=500, detail="世界未初始化")

    current_idx = TIME_SLOT_SEQUENCE.index(world.time_slot) if world.time_slot in TIME_SLOT_SEQUENCE else 0
    if current_idx < len(TIME_SLOT_SEQUENCE) - 1:
        world.time_slot = TIME_SLOT_SEQUENCE[current_idx + 1]
    else:
        # 进入下一天
        world.time_slot = TIME_SLOT_SEQUENCE[0]
        world.day_number += 1
        day_idx = (world.day_number - 1) % 7
        world.weekday = WEEKDAY_SEQUENCE[day_idx]

    world.turns_in_current_scene = 0

    if req and req.target_location:
        world.player_location = req.target_location

    # 根据时段自动更新 NPC 日程位置
    chars_res = await db.execute(select(CharacterState))
    char_states = chars_res.scalars().all()
    for cs in char_states:
        cfg = get_character_config(cs.character_id)
        schedule = cfg.get("schedule", {})
        slot_plan = schedule.get(world.time_slot)
        if slot_plan and "location" in slot_plan:
            cs.current_location = slot_plan["location"]

    await db.commit()
    return await get_current_world_state(db)
