import os
from pathlib import Path
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from .models import (
    Base,
    WorldState,
    CharacterState,
    Relationship,
    Player,
    PhoneMessage,
    MomentPost,
    MomentLike,
    MomentComment,
)

# 保证数据存储目录存在
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "game.db"
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH.as_posix()}"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """初始化数据库表并注入初始世界和角色状态"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select

        # 1. Player
        res = await session.execute(select(Player).limit(1))
        player = res.scalar_one_or_none()
        if not player:
            player = Player(name="你", major="计算机科学与技术")
            session.add(player)

        # 2. WorldState (按 Day 1 = 星期三 保证对齐)
        res = await session.execute(select(WorldState).limit(1))
        world = res.scalar_one_or_none()
        if not world:
            world = WorldState(
                day_number=1,
                weekday="星期三",
                time_slot="afternoon",
                weather="sunny",
                player_location="library",
            )
            session.add(world)

        # 3. Lin Yuqing CharacterState
        res = await session.execute(select(CharacterState).where(CharacterState.character_id == "lin_yuqing"))
        char_state = res.scalar_one_or_none()
        if not char_state:
            char_state = CharacterState(
                character_id="lin_yuqing",
                current_location="library",
                current_mood="happy",
                fatigue=0,
            )
            session.add(char_state)

        # 4. Lin Yuqing Relationship
        res = await session.execute(select(Relationship).where(Relationship.character_id == "lin_yuqing"))
        rel = res.scalar_one_or_none()
        if not rel:
            rel = Relationship(
                character_id="lin_yuqing",
                affection=25,
                trust=20,
                stage="friend",
                flags={"met_in_library": True},
            )
            session.add(rel)

        # 5. 初始朋友圈动态持久化
        res = await session.execute(select(MomentPost).limit(1))
        if not res.scalar_one_or_none():
            post1 = MomentPost(
                id="moment_1",
                author_id="lin_yuqing",
                author_name="林雨晴",
                avatar="👧",
                time_str="1 小时前",
                content="图书馆靠窗的第三个位置，下午两点半的阳光永远是最温柔的。配上一罐柑橘味汽水，今日份充电完毕！🥤✨",
                image_url=None,
            )
            post2 = MomentPost(
                id="moment_2",
                author_id="su_wanxing",
                author_name="苏晚星",
                avatar="📚",
                time_str="昨天 21:15",
                content="雨后的香樟树叶落了一地。写了一首未完成的短诗，似乎还缺少一个合衬的韵脚。",
                image_url=None,
            )
            session.add_all([post1, post2])

            like1 = MomentLike(moment_id="moment_1", user_name="苏晚星")
            session.add(like1)

            cmt1 = MomentComment(moment_id="moment_1", author_name="苏晚星", text="注意保护视力，别看太久入神了。")
            cmt2 = MomentComment(moment_id="moment_1", author_name="林雨晴", text="知道啦学姐！放心好啦~")
            session.add_all([cmt1, cmt2])

        # 6. 初始手机聊天消息持久化
        res = await session.execute(select(PhoneMessage).limit(1))
        if not res.scalar_one_or_none():
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
            msg3 = PhoneMessage(
                contact_id="group_lit",
                sender_id="lin_yuqing",
                sender_name="林雨晴",
                text="收到！我会带相机去帮大家拍记录照片的~ 📷",
                msg_type="text",
            )
            session.add_all([msg1, msg2, msg3])

        await session.commit()
