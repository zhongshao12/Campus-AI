from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database.session import get_db
from ..database.models import CharacterState, Relationship, WorldState
from ..models.schemas import CharacterStatusResponse
from ..core.config import get_character_config

router = APIRouter()

@router.get("/{character_id}/status", response_model=CharacterStatusResponse)
async def get_character_status(character_id: str, db: AsyncSession = Depends(get_db)):
    """获取指定角色当前状态与关系详情"""
    char_res = await db.execute(select(CharacterState).where(CharacterState.character_id == character_id))
    char_state = char_res.scalar_one_or_none()
    if not char_state:
        raise HTTPException(status_code=404, detail="未找到该角色状态")

    rel_res = await db.execute(select(Relationship).where(Relationship.character_id == character_id))
    rel = rel_res.scalar_one_or_none()
    if not rel:
        raise HTTPException(status_code=404, detail="未找到该角色关系数据")

    world_res = await db.execute(select(WorldState).limit(1))
    world = world_res.scalar_one_or_none()
    current_slot = world.time_slot if world else "afternoon"

    cfg = get_character_config(character_id)
    schedule = cfg.get("schedule", {})
    slot_info = schedule.get(current_slot, {})
    activity = slot_info.get("activity", "闲逛中")

    return CharacterStatusResponse(
        character_id=character_id,
        name=cfg.get("name", character_id),
        title=cfg.get("title", ""),
        affection=rel.affection,
        trust=rel.trust,
        stage=rel.stage,
        current_mood=char_state.current_mood,
        current_location=char_state.current_location,
        schedule_activity=activity,
    )

@router.get("/{character_id}/config")
async def get_character_full_config(character_id: str):
    """获取角色的配置元数据（包含立绘表情映射表、性格标签等，供前端渲染）"""
    cfg = get_character_config(character_id)
    if not cfg:
        raise HTTPException(status_code=404, detail="角色配置文件不存在")
    return cfg
