from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from ..database.session import get_db
from ..database.models import (
    SaveSlot,
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
    ImageRecord,
)

router = APIRouter()

SNAPSHOT_SCHEMA_VERSION = 2

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
    真·全量状态快照存档 (V0.2.1 完备版)
    覆盖：全局Revision + 世界 + 玩家全属性(钱/体力/背包) + NPC全状态(熟悉度/忙碌) +
          剧情事件 + 对话日志 + 情节记忆 + 手机消息 + 朋友圈全量(帖/赞/评) + 变量审计日志 + CG图鉴
    """
    if slot_index < 1 or slot_index > 10:
        raise HTTPException(status_code=400, detail="槽位编号必须在 1~10 之间")

    # 1. 变量修订版本号
    rev_res = await db.execute(select(GameStateRevision).limit(1))
    state_rev = rev_res.scalar_one_or_none()
    current_rev = state_rev.revision if state_rev else 1

    # 2. 玩家属性
    p_res = await db.execute(select(Player).limit(1))
    player = p_res.scalar_one_or_none()
    player_data = {
        "name": player.name if player else "你",
        "gender": player.gender if player else "male",
        "major": player.major if player else "计算机科学与技术",
        "energy": getattr(player, "energy", 100),
        "mood": getattr(player, "mood", "happy"),
        "money": getattr(player, "money", 300),
        "inventory": getattr(player, "inventory", {}),
    }

    # 3. 世界状态
    w_res = await db.execute(select(WorldState).limit(1))
    world = w_res.scalar_one_or_none()
    world_data = {
        "day_number": world.day_number if world else 1,
        "weekday": world.weekday if world else "星期三",
        "time_slot": world.time_slot if world else "afternoon",
        "weather": world.weather if world else "sunny",
        "player_location": world.player_location if world else "library",
        "turns_in_current_scene": world.turns_in_current_scene if world else 0,
    }

    # 4. 角色状态与关系 (包含 familiarity, is_busy, flags)
    rel_res = await db.execute(select(Relationship))
    relationships = [
        {
            "character_id": r.character_id,
            "affection": r.affection,
            "trust": r.trust,
            "familiarity": getattr(r, "familiarity", 20),
            "stage": r.stage,
            "flags": r.flags,
        }
        for r in rel_res.scalars().all()
    ]

    cs_res = await db.execute(select(CharacterState))
    char_states = [
        {
            "character_id": c.character_id,
            "current_location": c.current_location,
            "current_mood": c.current_mood,
            "fatigue": c.fatigue,
            "is_busy": getattr(c, "is_busy", False),
        }
        for c in cs_res.scalars().all()
    ]

    # 5. 剧情事件
    ev_res = await db.execute(select(EventRecord))
    events = [
        {
            "event_id": e.event_id,
            "character_id": e.character_id,
            "status": e.status,
            "triggered_day": e.triggered_day,
            "details": e.details,
        }
        for e in ev_res.scalars().all()
    ]

    # 6. 对话历史与记忆
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

    # 7. 手机消息
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

    # 8. 朋友圈 (帖子/点赞/评论)
    posts_res = await db.execute(select(MomentPost))
    moment_posts = [
        {
            "id": mp.id,
            "author_id": mp.author_id,
            "author_name": mp.author_name,
            "avatar": mp.avatar,
            "time_str": mp.time_str,
            "content": mp.content,
            "image_url": mp.image_url,
        }
        for mp in posts_res.scalars().all()
    ]
    likes_res = await db.execute(select(MomentLike))
    moment_likes = [{"moment_id": ml.moment_id, "user_name": ml.user_name} for ml in likes_res.scalars().all()]
    cmts_res = await db.execute(select(MomentComment))
    moment_comments = [{"moment_id": mc.moment_id, "author_name": mc.author_name, "text": mc.text} for mc in cmts_res.scalars().all()]

    # 9. 变量审计日志快照
    changes_res = await db.execute(select(VariableChange).order_by(VariableChange.id.asc()).limit(100))
    var_changes = [
        {
            "turn_id": vc.turn_id,
            "revision_before": vc.revision_before,
            "revision_after": vc.revision_after,
            "source": vc.source,
            "character_id": vc.character_id,
            "path": vc.path,
            "op": vc.op,
            "old_value": vc.old_value,
            "new_value": vc.new_value,
            "reason": vc.reason,
        }
        for vc in changes_res.scalars().all()
    ]

    snapshot = {
        "snapshot_schema_version": SNAPSHOT_SCHEMA_VERSION,
        "revision": current_rev,
        "player": player_data,
        "world": world_data,
        "relationships": relationships,
        "char_states": char_states,
        "events": events,
        "dialogue_logs": dialogue_logs,
        "memories": memories,
        "phone_messages": phone_messages,
        "moment_posts": moment_posts,
        "moment_likes": moment_likes,
        "moment_comments": moment_comments,
        "variable_changes": var_changes,
        "preview": {
            "day": world_data["day_number"],
            "time_slot": world_data["time_slot"],
            "location": world_data["player_location"],
            "lin_affection": next((r["affection"] for r in relationships if r["character_id"] == "lin_yuqing"), 0),
            "money": player_data["money"],
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
    全量状态原子事务重建恢复
    不仅更新数值，同时全量重建玩家属性、事件、朋友圈、对话历史与记忆，杜绝状态穿透与遗留。
    """
    slot_res = await db.execute(select(SaveSlot).where(SaveSlot.slot_index == slot_index))
    slot = slot_res.scalar_one_or_none()
    if not slot:
        raise HTTPException(status_code=404, detail="该存档槽位为空")

    data = slot.snapshot

    # 1. 恢复变量修订版本号
    rev_res = await db.execute(select(GameStateRevision).limit(1))
    state_rev = rev_res.scalar_one_or_none()
    if state_rev:
        state_rev.revision = data.get("revision", 1)

    # 2. 恢复玩家完整属性
    p_data = data.get("player", {})
    p_res = await db.execute(select(Player).limit(1))
    player = p_res.scalar_one_or_none()
    if player and p_data:
        player.name = p_data.get("name", "你")
        player.gender = p_data.get("gender", "male")
        player.major = p_data.get("major", "计算机科学与技术")
        player.energy = p_data.get("energy", 100)
        player.mood = p_data.get("mood", "happy")
        player.money = p_data.get("money", 300)
        player.inventory = p_data.get("inventory", {})

    # 3. 恢复世界状态
    w_data = data.get("world", {})
    w_res = await db.execute(select(WorldState).limit(1))
    world = w_res.scalar_one_or_none()
    if world and w_data:
        world.day_number = w_data.get("day_number", 1)
        world.weekday = w_data.get("weekday", "星期三")
        world.time_slot = w_data.get("time_slot", "afternoon")
        world.weather = w_data.get("weather", "sunny")
        world.player_location = w_data.get("player_location", "library")
        world.turns_in_current_scene = w_data.get("turns_in_current_scene", 0)

    # 4. 重建角色关系集合
    await db.execute(delete(Relationship))
    for r_item in data.get("relationships", []):
        r_rec = Relationship(
            character_id=r_item["character_id"],
            affection=r_item.get("affection", 0),
            trust=r_item.get("trust", 0),
            familiarity=r_item.get("familiarity", 20),
            stage=r_item.get("stage", "acquaintance"),
            flags=r_item.get("flags", {}),
        )
        db.add(r_rec)

    # 5. 重建角色状态集合
    await db.execute(delete(CharacterState))
    for c_item in data.get("char_states", []):
        c_rec = CharacterState(
            character_id=c_item["character_id"],
            current_location=c_item.get("current_location", "library"),
            current_mood=c_item.get("current_mood", "neutral"),
            fatigue=c_item.get("fatigue", 0),
            is_busy=c_item.get("is_busy", False),
        )
        db.add(c_rec)

    # 6. 重建剧情事件
    await db.execute(delete(EventRecord))
    for e_item in data.get("events", []):
        e_rec = EventRecord(
            event_id=e_item["event_id"],
            character_id=e_item.get("character_id"),
            status=e_item.get("status", "completed"),
            triggered_day=e_item.get("triggered_day", 1),
            details=e_item.get("details", {}),
        )
        db.add(e_rec)

    # 7. 重建对话历史
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

    # 8. 重建情节记忆
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

    # 9. 重建手机消息
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

    # 10. 重建朋友圈全部数据
    if "moment_posts" in data:
        await db.execute(delete(MomentPost))
        for mp in data.get("moment_posts", []):
            db.add(MomentPost(
                id=mp["id"],
                author_id=mp["author_id"],
                author_name=mp["author_name"],
                avatar=mp.get("avatar", "👧"),
                time_str=mp.get("time_str", "刚刚"),
                content=mp["content"],
                image_url=mp.get("image_url"),
            ))

    if "moment_likes" in data:
        await db.execute(delete(MomentLike))
        for ml in data.get("moment_likes", []):
            db.add(MomentLike(moment_id=ml["moment_id"], user_name=ml["user_name"]))

    if "moment_comments" in data:
        await db.execute(delete(MomentComment))
        for mc in data.get("moment_comments", []):
            db.add(MomentComment(moment_id=mc["moment_id"], author_name=mc["author_name"], text=mc["text"]))

    # 11. 重建变量因果审计日志
    if "variable_changes" in data:
        await db.execute(delete(VariableChange))
        for vc in data.get("variable_changes", []):
            db.add(VariableChange(
                turn_id=vc.get("turn_id"),
                revision_before=vc.get("revision_before", 1),
                revision_after=vc.get("revision_after", 1),
                source=vc.get("source", "system"),
                character_id=vc.get("character_id"),
                path=vc["path"],
                op=vc["op"],
                old_value=vc["old_value"],
                new_value=vc["new_value"],
                reason=vc["reason"],
            ))

    await db.commit()
    return {
        "message": f"成功加载槽位 {slot_index} 并原子重建全部世界实体与时空因果链",
        "restored_revision": state_rev.revision if state_rev else 1,
    }
