from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from ..database.session import get_db
from ..database.models import (
    GameStateRevision,
    WorldState,
    Player,
    CharacterState,
    Relationship,
    DialogueLog,
    Memory,
    EventRecord,
    PhoneMessage,
    MomentPost,
    MomentLike,
    MomentComment,
    VariableChange,
)
from ..variables.snapshot import SnapshotBuilder

router = APIRouter()

@router.post("/new")
async def start_new_game(db: AsyncSession = Depends(get_db)):
    """
    开启全新游戏篇章 (Reset to Day 1)
    原子重置世界时钟、玩家属性、NPC状态、好感度与版本号，并清空历史记忆。
    """
    # 1. 重置版本号为 1
    rev_res = await db.execute(select(GameStateRevision).limit(1))
    state_rev = rev_res.scalar_one_or_none()
    if state_rev:
        state_rev.revision = 1
        state_rev.schema_version = 1
    else:
        db.add(GameStateRevision(id=1, revision=1, schema_version=1))

    # 2. 重置玩家
    p_res = await db.execute(select(Player).limit(1))
    player = p_res.scalar_one_or_none()
    if player:
        player.name = "你"
        player.energy = 100
        player.mood = "happy"
        player.money = 300
        player.inventory = {"orange_soda": 1}

    # 3. 重置世界状态 (第1天 星期三 下午 图书馆)
    w_res = await db.execute(select(WorldState).limit(1))
    world = w_res.scalar_one_or_none()
    if world:
        world.day_number = 1
        world.weekday = "星期三"
        world.time_slot = "afternoon"
        world.weather = "sunny"
        world.player_location = "library"
        world.turns_in_current_scene = 0

    # 4. 重置角色与关系
    rel_res = await db.execute(select(Relationship).where(Relationship.character_id == "lin_yuqing"))
    rel = rel_res.scalar_one_or_none()
    if rel:
        rel.affection = 25
        rel.trust = 20
        rel.familiarity = 20
        rel.stage = "friend"
        rel.flags = {"met_in_library": True}

    cs_res = await db.execute(select(CharacterState).where(CharacterState.character_id == "lin_yuqing"))
    cs = cs_res.scalar_one_or_none()
    if cs:
        cs.current_location = "library"
        cs.current_mood = "happy"
        cs.fatigue = 0
        cs.is_busy = False

    # 5. 清空对话、记忆与日志
    await db.execute(delete(DialogueLog))
    await db.execute(delete(Memory))
    await db.execute(delete(EventRecord))
    await db.execute(delete(VariableChange))

    # 6. 恢复初始手机消息
    await db.execute(delete(PhoneMessage))
    msg1 = PhoneMessage(
        contact_id="lin_yuqing",
        sender_id="lin_yuqing",
        sender_name="林雨晴",
        text="今天在图书馆看到一本很有趣的摄影集，下次借给你看呀~",
        msg_type="text",
    )
    msg2 = PhoneMessage(
        contact_id="group_lit",
        sender_id="su_wanxing",
        sender_name="苏晚星 (社长)",
        text="各位社员好，本周五下午在文学社活动室有一期关于近代诗歌的研讨会哦。",
        msg_type="text",
    )
    db.add_all([msg1, msg2])

    await db.commit()

    snapshot = await SnapshotBuilder.build_snapshot(db)
    return {
        "message": "已成功开启新游戏篇章，世界状态已重置为初始状态！",
        "snapshot": snapshot,
    }

@router.get("/current")
async def get_current_game(db: AsyncSession = Depends(get_db)):
    """获取当前游戏会话基础概览"""
    snapshot = await SnapshotBuilder.build_snapshot(db)
    return {
        "revision": snapshot.revision,
        "day": snapshot.world["day_number"],
        "weekday": snapshot.world["weekday"],
        "time_slot": snapshot.world["time_slot"],
        "location": snapshot.world["player_location"],
        "player": snapshot.player,
    }
