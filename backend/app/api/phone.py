from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database.session import get_db
from ..database.models import Relationship, CharacterState, WorldState
from ..core.arbitrator import Arbitrator
from ..ai.llm.client import LLMClient
from ..ai.comfyui.client import ComfyUIClient

router = APIRouter()
llm_client = LLMClient()
comfy_client = ComfyUIClient()

# 模拟内存消息队列与朋友圈数据库 (保证单机运行丝滑)
PHONE_MESSAGES: Dict[str, List[Dict[str, Any]]] = {
    "lin_yuqing": [
        {
            "id": 1,
            "sender": "lin_yuqing",
            "sender_name": "林雨晴",
            "text": "今天在图书馆看到一本很有趣的摄影集，下次借给你看呀~",
            "time": "14:20",
            "is_me": False,
            "type": "text",
        }
    ],
    "group_lit": [
        {
            "id": 1,
            "sender": "su_wanxing",
            "sender_name": "苏晚星 (社长)",
            "text": "各位社员好，本周五下午在文学社活动室有一期关于近代诗歌的研讨会哦。",
            "time": "09:30",
            "is_me": False,
            "type": "text",
        },
        {
            "id": 2,
            "sender": "lin_yuqing",
            "sender_name": "林雨晴",
            "text": "收到！我会带相机去帮大家拍记录照片的~ 📷",
            "time": "09:35",
            "is_me": False,
            "type": "text",
        }
    ]
}

MOMENTS_FEED = [
    {
        "id": "moment_1",
        "author_id": "lin_yuqing",
        "author_name": "林雨晴",
        "avatar": "👧",
        "time_str": "1 小时前",
        "content": "图书馆靠窗的第三个位置，下午两点半的阳光永远是最温柔的。配上一罐柑橘味汽水，今日份充电完毕！🥤✨",
        "image": "library_sunny.png",
        "likes": ["苏晚星", "你"],
        "comments": [
            {"author": "苏晚星", "text": "注意保护视力，别看太久入神了。"},
            {"author": "林雨晴", "text": "知道啦学姐！放心好啦~"}
        ]
    },
    {
        "id": "moment_2",
        "author_id": "su_wanxing",
        "author_name": "苏晚星",
        "avatar": "📚",
        "time_str": "昨天 21:15",
        "content": "雨后的香樟树叶落了一地。写了一首未完成的短诗，似乎还缺少一个合衬的韵脚。",
        "image": None,
        "likes": ["林雨晴"],
        "comments": []
    }
]

class SendMessageRequest(BaseModel):
    target_id: str  # lin_yuqing, group_lit, etc.
    text: str
    is_group: bool = False

class CommentRequest(BaseModel):
    content: str

class PhotoRequest(BaseModel):
    character_id: str = "lin_yuqing"
    scene_description: str = "cute selfie in university library, smiling"

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
async def get_messages(target_id: str):
    """获取与指定联系人或群组的聊天记录"""
    return PHONE_MESSAGES.get(target_id, [])

@router.post("/messages/send")
async def send_phone_message(
    req: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """通过手机发送消息（私聊/群聊）"""
    if req.target_id not in PHONE_MESSAGES:
        PHONE_MESSAGES[req.target_id] = []

    # 1. 记录我的发言
    my_msg = {
        "id": len(PHONE_MESSAGES[req.target_id]) + 1,
        "sender": "player",
        "sender_name": "你",
        "text": req.text,
        "time": "刚刚",
        "is_me": True,
        "type": "text",
    }
    PHONE_MESSAGES[req.target_id].append(my_msg)

    reply_msg = None

    if req.target_id == "lin_yuqing":
        # 获取林雨晴好感度
        rel_res = await db.execute(select(Relationship).where(Relationship.character_id == "lin_yuqing"))
        rel = rel_res.scalar_one_or_none()
        aff = rel.affection if rel else 25

        # 针对手机简短打字风格的快速智能回复
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
            if rel:
                rel.affection = min(100, rel.affection + 1)
                await db.commit()
        else:
            reply_text = f"看到你的消息啦！“{req.text}”是吧？等下自习结束我们当面聊聊呀~ ✨"
            reply_type = "text"

        reply_msg = {
            "id": len(PHONE_MESSAGES[req.target_id]) + 1,
            "sender": "lin_yuqing",
            "sender_name": "林雨晴",
            "text": reply_text,
            "time": "刚刚",
            "is_me": False,
            "type": reply_type,
        }
        PHONE_MESSAGES[req.target_id].append(reply_msg)

    elif req.target_id == "group_lit":
        reply_msg = {
            "id": len(PHONE_MESSAGES[req.target_id]) + 1,
            "sender": "su_wanxing",
            "sender_name": "苏晚星 (社长)",
            "text": "收到你的提议，周五活动我们可以把这个话题加进讨论议程中。",
            "time": "刚刚",
            "is_me": False,
            "type": "text",
        }
        PHONE_MESSAGES[req.target_id].append(reply_msg)

    return {
        "status": "success",
        "sent": my_msg,
        "reply": reply_msg,
    }

@router.get("/moments")
async def get_moments():
    """获取校园朋友圈动态流"""
    return MOMENTS_FEED

@router.post("/moments/{moment_id}/like")
async def like_moment(moment_id: str, db: AsyncSession = Depends(get_db)):
    """给朋友圈动态点赞"""
    for m in MOMENTS_FEED:
        if m["id"] == moment_id:
            if "你" in m["likes"]:
                m["likes"].remove("你")
                return {"liked": False, "likes": m["likes"]}
            else:
                m["likes"].append("你")
                # 点赞增加微量好感度
                if m["author_id"] == "lin_yuqing":
                    rel_res = await db.execute(select(Relationship).where(Relationship.character_id == "lin_yuqing"))
                    rel = rel_res.scalar_one_or_none()
                    if rel:
                        rel.affection = min(100, rel.affection + 1)
                        await db.commit()
                return {"liked": True, "likes": m["likes"]}
    raise HTTPException(status_code=404, detail="未找到该动态")

@router.post("/moments/{moment_id}/comment")
async def comment_moment(
    moment_id: str,
    req: CommentRequest,
    db: AsyncSession = Depends(get_db),
):
    """评论朋友圈动态，并获得作者互动回复"""
    for m in MOMENTS_FEED:
        if m["id"] == moment_id:
            # 记录我的评论
            m["comments"].append({"author": "你", "text": req.content})

            # 如果评论的是林雨晴，林雨晴回复并加好感
            reply_text = None
            if m["author_id"] == "lin_yuqing":
                reply_text = "嘿嘿，下次分你半瓶！记得帮我占位哦~"
                m["comments"].append({"author": "林雨晴", "text": reply_text})
                rel_res = await db.execute(select(Relationship).where(Relationship.character_id == "lin_yuqing"))
                rel = rel_res.scalar_one_or_none()
                if rel:
                    rel.affection = min(100, rel.affection + 1)
                    await db.commit()

            return {
                "status": "success",
                "comments": m["comments"],
                "author_reply": reply_text,
            }
    raise HTTPException(status_code=404, detail="未找到该动态")

@router.post("/request_photo")
async def request_character_photo(
    req: PhotoRequest,
    db: AsyncSession = Depends(get_db),
):
    """请求角色发送专属自拍/拍照，优先调用 ComfyUI"""
    prompt = f"1girl, lin_yuqing, black hair, blue eyes, cute smartphone selfie, casual outfit, university student, natural lighting, masterpiece, high quality, {req.scene_description}"
    
    prompt_id = await comfy_client.generate_cg(prompt=prompt, width=768, height=1024)
    
    # 构造返回消息
    photo_url = f"/api/images/view/{prompt_id}" if prompt_id else None
    
    # 写入聊天记录
    if req.character_id in PHONE_MESSAGES:
        PHONE_MESSAGES[req.character_id].append({
            "id": len(PHONE_MESSAGES[req.character_id]) + 1,
            "sender": req.character_id,
            "sender_name": "林雨晴",
            "text": "这是刚才随手拍的自拍，只发给你一个人看哦~ 🤫",
            "time": "刚刚",
            "is_me": False,
            "type": "image",
            "image_url": photo_url,
        })

    return {
        "status": "success",
        "has_realtime_cg": prompt_id is not None,
        "photo_url": photo_url,
        "message": "自拍已送达私信聊天框！",
    }
