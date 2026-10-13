from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from ..database.session import get_db
from ..database.models import (
    Relationship,
    CharacterState,
    WorldState,
    PhoneMessage,
    MomentPost,
    MomentLike,
    MomentComment,
)
from ..ai.comfyui.client import ComfyUIClient
from ..variables.snapshot import SnapshotBuilder
from ..variables.schemas import VariablePatch, VariableOperation
from ..variables.engine import VariableEngine

router = APIRouter()
comfy_client = ComfyUIClient()

class SendMessageRequest(BaseModel):
    target_id: str  # lin_yuqing, group_lit, etc.
    text: str
    is_group: bool = False

class CommentRequest(BaseModel):
    content: str

class PhotoRequest(BaseModel):
    character_id: str = "lin_yuqing"
    scene_description: str = "cute selfie in university library, smiling"

async def _apply_phone_affection_reward(character_id: str, delta: int, reason: str, db: AsyncSession):
    """统一走 VariableEngine 进行手机交互的好感度裁决与版本递增"""
    snapshot = await SnapshotBuilder.build_snapshot(db)
    patch = VariablePatch(
        base_revision=snapshot.revision,
        operations=[
            VariableOperation(
                op="delta",
                path=f"/characters/{character_id}/relationship/affection",
                value=delta,
                reason=reason,
            )
        ],
        source="phone",
    )
    await VariableEngine.apply_patch(patch, db=db, trusted_system=True)

@router.get("/contacts")
async def get_contacts(db: AsyncSession = Depends(get_db)):
    """获取手机通讯录列表"""
    rel_res = await db.execute(select(Relationship).where(Relationship.character_id == "lin_yuqing"))
    rel = rel_res.scalar_one_or_none()
    aff = rel.affection if rel else 25

    return [
        {
            "id": "lin_yuqing",
            "name": "林雨晴",
            "avatar": "👧",
            "signature": "晴天适合读小说，雨天适合听雨声 ☁️",
            "is_group": False,
            "unread_count": 0,
            "affection": aff,
            "online_status": "在线",
        },
        {
            "id": "su_wanxing",
            "name": "苏晚星 (学姐)",
            "avatar": "📚",
            "signature": "文字是时间的琥珀。",
            "is_group": False,
            "unread_count": 0,
            "affection": 10,
            "online_status": "离开",
        },
        {
            "id": "group_lit",
            "name": "大学文学社研讨组 📖",
            "avatar": "🏛️",
            "signature": "群成员：社长、雨晴、你等 6 人",
            "is_group": True,
            "unread_count": 0,
            "affection": None,
            "online_status": "群聊",
        },
        {
            "id": "group_class",
            "name": "计算机大二 (3) 班通知群",
            "avatar": "💻",
            "signature": "班长：明天微积分作业截止提交！",
            "is_group": True,
            "unread_count": 0,
            "affection": None,
            "online_status": "群聊",
        }
    ]

@router.get("/messages/{target_id}")
async def get_messages(target_id: str, db: AsyncSession = Depends(get_db)):
    """从数据库持久化读取与指定联系人或群组的聊天记录"""
    stmt = (
        select(PhoneMessage)
        .where(PhoneMessage.contact_id == target_id)
        .order_by(PhoneMessage.id.asc())
    )
    res = await db.execute(stmt)
    records = res.scalars().all()

    return [
        {
            "id": r.id,
            "sender": r.sender_id,
            "sender_name": r.sender_name,
            "text": r.text,
            "time": r.created_at.strftime("%H:%M") if r.created_at else "刚刚",
            "is_me": r.sender_id == "player",
            "type": r.msg_type,
            "image_url": r.image_url,
        }
        for r in records
    ]

@router.post("/messages/send")
async def send_phone_message(
    req: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """通过手机发送消息，统一通过 VariableEngine 裁决好感度并入库"""
    my_msg = PhoneMessage(
        contact_id=req.target_id,
        sender_id="player",
        sender_name="你",
        text=req.text,
        msg_type="text",
    )
    db.add(my_msg)
    await db.flush()

    reply_msg_data = None

    if req.target_id == "lin_yuqing":
        text_lower = req.text.lower()
        if "自拍" in text_lower or "照片" in text_lower or "看看你" in text_lower:
            reply_text = "诶？突然要看照片呀……等我找一张刚才拍的给你看，不许笑我哦！📸"
            reply_type = "photo_prompt"
        elif "在干嘛" in text_lower or "在忙吗" in text_lower:
            reply_text = "在翻文学评论呢~ 刚刚看到一段很有趣的话，正想着跟你分享呢！你那边怎么样呀？"
            reply_type = "text"
        elif "喜欢" in text_lower or "想你" in text_lower:
            reply_text = "（秒回）……笨蛋，手机屏幕上突然弹出来这个，差点被旁边的同学看到了啦！⁄(⁄ ⁄•⁄-⁄•⁄ ⁄)⁄"
            reply_type = "text"
            # 统一通过变量引擎裁决好感
            await _apply_phone_affection_reward("lin_yuqing", 1, "手机收到心动表白私信", db)
        else:
            reply_text = f"看到你的消息啦！“{req.text}”是吧？等下自习结束我们当面聊聊呀~ ✨"
            reply_type = "text"

        reply_db = PhoneMessage(
            contact_id=req.target_id,
            sender_id="lin_yuqing",
            sender_name="林雨晴",
            text=reply_text,
            msg_type=reply_type,
        )
        db.add(reply_db)
        await db.flush()

        reply_msg_data = {
            "id": reply_db.id,
            "sender": "lin_yuqing",
            "sender_name": "林雨晴",
            "text": reply_text,
            "time": "刚刚",
            "is_me": False,
            "type": reply_type,
        }

    elif req.target_id == "group_lit":
        reply_db = PhoneMessage(
            contact_id=req.target_id,
            sender_id="su_wanxing",
            sender_name="苏晚星 (社长)",
            text="收到你的提议，周五活动我们可以把这个话题加进讨论议程中。",
            msg_type="text",
        )
        db.add(reply_db)
        await db.flush()

        reply_msg_data = {
            "id": reply_db.id,
            "sender": "su_wanxing",
            "sender_name": "苏晚星 (社长)",
            "text": reply_db.text,
            "time": "刚刚",
            "is_me": False,
            "type": "text",
        }

    await db.commit()

    return {
        "status": "success",
        "sent": {
            "id": my_msg.id,
            "sender": "player",
            "sender_name": "你",
            "text": my_msg.text,
            "time": "刚刚",
            "is_me": True,
            "type": "text",
        },
        "reply": reply_msg_data,
    }

@router.get("/moments")
async def get_moments(db: AsyncSession = Depends(get_db)):
    """从数据库加载朋友圈动态流、点赞列表及评论"""
    posts_res = await db.execute(select(MomentPost).order_by(MomentPost.created_at.desc()))
    posts = posts_res.scalars().all()

    results = []
    for p in posts:
        likes_res = await db.execute(select(MomentLike.user_name).where(MomentLike.moment_id == p.id))
        likes = list(likes_res.scalars().all())

        cmts_res = await db.execute(
            select(MomentComment).where(MomentComment.moment_id == p.id).order_by(MomentComment.id.asc())
        )
        cmts = [{"author": c.author_name, "text": c.text} for c in cmts_res.scalars().all()]

        results.append({
            "id": p.id,
            "author_id": p.author_id,
            "author_name": p.author_name,
            "avatar": p.avatar,
            "time_str": p.time_str,
            "content": p.content,
            "image": p.image_url,
            "likes": likes,
            "comments": cmts,
        })
    return results

@router.post("/moments/{moment_id}/like")
async def like_moment(moment_id: str, db: AsyncSession = Depends(get_db)):
    """
    点赞朋友圈动态 (V0.2.1 防刷好感机制)
    只有首次点赞给予好感度增益，取消再点不重复赠送；统一经由 VariableEngine 校验。
    """
    like_res = await db.execute(
        select(MomentLike).where(MomentLike.moment_id == moment_id, MomentLike.user_name == "你")
    )
    existing_like = like_res.scalar_one_or_none()

    if existing_like:
        await db.delete(existing_like)
        liked = False
    else:
        new_like = MomentLike(moment_id=moment_id, user_name="你")
        db.add(new_like)
        liked = True

        # 检查是否为首次点赞（通过查询当前角色的约定flags判断，防止反复取消再点刷分）
        post_res = await db.execute(select(MomentPost).where(MomentPost.id == moment_id))
        post = post_res.scalar_one_or_none()
        if post and post.author_id == "lin_yuqing":
            rel_res = await db.execute(select(Relationship).where(Relationship.character_id == "lin_yuqing"))
            rel = rel_res.scalar_one_or_none()
            if rel:
                flags = rel.flags or {}
                liked_key = f"liked_moment_{moment_id}"
                if not flags.get(liked_key):
                    flags[liked_key] = True
                    rel.flags = flags
                    # 走统一变量引擎
                    await _apply_phone_affection_reward("lin_yuqing", 1, "朋友圈动态首次点赞心动", db)

    await db.commit()

    all_likes_res = await db.execute(select(MomentLike.user_name).where(MomentLike.moment_id == moment_id))
    all_likes = list(all_likes_res.scalars().all())

    return {"liked": liked, "likes": all_likes}

@router.post("/moments/{moment_id}/comment")
async def comment_moment(
    moment_id: str,
    req: CommentRequest,
    db: AsyncSession = Depends(get_db),
):
    """发表朋友圈评论并由角色互动，经由 VariableEngine 统一更新好感"""
    my_cmt = MomentComment(moment_id=moment_id, author_name="你", text=req.content)
    db.add(my_cmt)

    reply_text = None
    post_res = await db.execute(select(MomentPost).where(MomentPost.id == moment_id))
    post = post_res.scalar_one_or_none()

    if post and post.author_id == "lin_yuqing":
        reply_text = "嘿嘿，下次分你半瓶！记得帮我占位哦~"
        author_cmt = MomentComment(moment_id=moment_id, author_name="林雨晴", text=reply_text)
        db.add(author_cmt)

        # 走统一变量引擎
        await _apply_phone_affection_reward("lin_yuqing", 1, "朋友圈互动暖心评论", db)

    await db.commit()

    all_cmts = await db.execute(
        select(MomentComment).where(MomentComment.moment_id == moment_id).order_by(MomentComment.id.asc())
    )
    comments_list = [{"author": c.author_name, "text": c.text} for c in all_cmts.scalars().all()]

    return {
        "status": "success",
        "comments": comments_list,
        "author_reply": reply_text,
    }

@router.post("/request_photo")
async def request_character_photo(
    req: PhotoRequest,
    db: AsyncSession = Depends(get_db),
):
    """请求角色自拍并持久化记录到聊天与图鉴中"""
    prompt = f"1girl, lin_yuqing, black hair, blue eyes, cute smartphone selfie, casual outfit, university student, natural lighting, masterpiece, high quality, {req.scene_description}"
    photo_url = await comfy_client.generate_cg(prompt=prompt, width=768, height=1024, wait=False)

    msg = PhoneMessage(
        contact_id=req.character_id,
        sender_id=req.character_id,
        sender_name="林雨晴",
        text="这是刚才随手拍的自拍，只发给你一个人看哦~ 🤫",
        msg_type="image",
        image_url=photo_url or "/api/images/view/placeholder_selfie",
    )
    db.add(msg)
    await db.commit()

    return {
        "status": "success",
        "has_realtime_cg": photo_url is not None,
        "photo_url": msg.image_url,
        "message": "自拍已送达私信聊天框！",
    }
