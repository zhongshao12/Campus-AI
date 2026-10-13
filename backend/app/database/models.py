from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, default="你")
    gender = Column(String(10), default="male")
    major = Column(String(50), default="计算机科学与技术")
    energy = Column(Integer, default=100)      # 体力 (0~100)
    mood = Column(String(20), default="happy")  # 心情
    money = Column(Integer, default=300)       # 零花钱
    inventory = Column(JSON, default=lambda: {"orange_soda": 1})  # 背包物品
    created_at = Column(DateTime, default=datetime.utcnow)

class GameStateRevision(Base):
    """全局变量状态版本与修订追踪表"""
    __tablename__ = "game_state_revisions"

    id = Column(Integer, primary_key=True, default=1)
    revision = Column(Integer, default=1, nullable=False)        # 每次任何变量变更递增
    schema_version = Column(Integer, default=1, nullable=False)  # 变量结构规范版本
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class VariableChange(Base):
    """变量变更审计日志表 (追溯每一次状态变化因果)"""
    __tablename__ = "variable_changes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    turn_id = Column(Integer, nullable=True, index=True)
    revision_before = Column(Integer, nullable=False)
    revision_after = Column(Integer, nullable=False)
    source = Column(String(50), default="system")  # dialogue, system, action, phone
    character_id = Column(String(50), nullable=True, index=True)
    path = Column(String(200), nullable=False)     # /characters/lin_yuqing/relationship/affection
    op = Column(String(20), nullable=False)        # delta, replace
    old_value = Column(String(100), nullable=False)
    new_value = Column(String(100), nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class WorldState(Base):
    __tablename__ = "world_states"

    id = Column(Integer, primary_key=True, autoincrement=True)
    day_number = Column(Integer, default=1)  # 游戏第几天
    weekday = Column(String(10), default="星期三")
    time_slot = Column(String(20), default="afternoon")  # morning, noon, afternoon, dusk, night
    weather = Column(String(20), default="sunny")  # sunny, cloudy, rainy
    player_location = Column(String(50), default="library")
    turns_in_current_scene = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CharacterState(Base):
    __tablename__ = "character_states"

    id = Column(Integer, primary_key=True, autoincrement=True)
    character_id = Column(String(50), unique=True, nullable=False, index=True)
    current_location = Column(String(50), default="library")
    current_mood = Column(String(20), default="neutral")  # happy, shy, sad, angry, surprised, neutral
    fatigue = Column(Integer, default=0)  # 0~100
    is_busy = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    character_id = Column(String(50), unique=True, nullable=False, index=True)
    affection = Column(Integer, default=15)  # 好感度 (0~100)
    trust = Column(Integer, default=10)      # 信任度 (0~100)
    familiarity = Column(Integer, default=20) # 熟悉度 (0~100)
    stage = Column(String(30), default="acquaintance")  # acquaintance, friend, close, crush, lover
    flags = Column(JSON, default=dict)       # 特殊标记与约定字典
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DialogueLog(Base):
    __tablename__ = "dialogue_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    character_id = Column(String(50), index=True)  # 发言主体标识（若玩家则为 "player"）
    target_character_id = Column(String(50), nullable=True, index=True)  # 对话指向的目标角色（彻底杜绝串线）
    speaker_name = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    emotion = Column(String(30), default="neutral")
    expression = Column(String(30), default="neutral")
    location = Column(String(50), default="library")
    game_day = Column(Integer, default=1)
    game_time_slot = Column(String(20), default="afternoon")
    created_at = Column(DateTime, default=datetime.utcnow)

class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    character_id = Column(String(50), nullable=False, index=True)
    memory_type = Column(String(20), default="episodic")  # episodic (情节记忆), fact (事实), promise (约定)
    summary = Column(Text, nullable=False)
    keywords = Column(String(255), default="")
    importance = Column(Integer, default=3)  # 1~5
    location = Column(String(50), nullable=True)
    game_day = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class EventRecord(Base):
    __tablename__ = "event_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(50), unique=True, nullable=False, index=True)
    character_id = Column(String(50), nullable=True)
    status = Column(String(20), default="completed")  # pending, completed, locked
    triggered_day = Column(Integer, default=1)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_id = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(String(30), default="pending")  # pending, processing, completed, failed
    category = Column(String(30), default="cg")     # cg, selfie, sprite
    character_id = Column(String(50), nullable=True)
    prompt = Column(Text, nullable=False)
    output_path = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class ImageRecord(Base):
    __tablename__ = "image_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_id = Column(String(100), nullable=True, index=True)
    category = Column(String(30), default="cg")
    character_id = Column(String(50), nullable=True)
    prompt = Column(Text, nullable=False)
    file_path = Column(String(255), nullable=False)
    unlocked = Column(Boolean, default=True)
    title = Column(String(100), default="新回忆 CG")
    created_at = Column(DateTime, default=datetime.utcnow)

class PhoneMessage(Base):
    __tablename__ = "phone_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contact_id = Column(String(50), nullable=False, index=True)
    sender_id = Column(String(50), nullable=False)
    sender_name = Column(String(50), nullable=False)
    text = Column(Text, nullable=False)
    msg_type = Column(String(20), default="text")
    image_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class MomentPost(Base):
    __tablename__ = "moment_posts"

    id = Column(String(50), primary_key=True)
    author_id = Column(String(50), nullable=False)
    author_name = Column(String(50), nullable=False)
    avatar = Column(String(20), default="👧")
    time_str = Column(String(50), default="刚刚")
    content = Column(Text, nullable=False)
    image_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class MomentLike(Base):
    __tablename__ = "moment_likes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    moment_id = Column(String(50), nullable=False, index=True)
    user_name = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class MomentComment(Base):
    __tablename__ = "moment_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    moment_id = Column(String(50), nullable=False, index=True)
    author_name = Column(String(50), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class SaveSlot(Base):
    __tablename__ = "save_slots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slot_index = Column(Integer, unique=True, nullable=False)
    title = Column(String(100), nullable=False)
    snapshot = Column(JSON, nullable=False)
    saved_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
