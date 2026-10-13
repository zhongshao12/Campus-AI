import os
from pathlib import Path
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from .models import Base, WorldState, CharacterState, Relationship, Player

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

    # 检查并初始化默认世界状态和主角与林雨晴的状态
    async with AsyncSessionLocal() as session:
        # 1. Player
        from sqlalchemy import select
        res = await session.execute(select(Player).limit(1))
        player = res.scalar_one_or_none()
        if not player:
            player = Player(name="你", major="计算机科学与技术")
            session.add(player)

        # 2. WorldState
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

        await session.commit()
