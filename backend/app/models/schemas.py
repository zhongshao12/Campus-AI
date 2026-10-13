from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

# --- LLM 提议效应 ---
class ProposedEffect(BaseModel):
    type: str = Field(description="变动类型: affection_delta, trust_delta, flag_set")
    value: Union[int, float, str, bool] = Field(description="变动值")
    reason: Optional[str] = Field(default=None, description="变动理由")

# --- LLM 结构化输出规范 ---
class LLMDialogueResponse(BaseModel):
    speaker: str = Field(description="角色名字")
    dialogue: str = Field(description="角色对白，口吻自然生动")
    emotion: str = Field(default="neutral", description="情绪状态: neutral, happy, blush, surprised, thinking, pout, sad")
    expression: str = Field(default="neutral", description="立绘表情标签")
    action: Optional[str] = Field(default=None, description="角色当下的小动作")
    inner_thought: Optional[str] = Field(default=None, description="内心独白或心理活动")
    proposed_effects: List[ProposedEffect] = Field(default_factory=list, description="提议的状态变更")
    event_trigger: Optional[str] = Field(default=None, description="剧情事件标识")
    image_request: Optional[Dict[str, Any]] = Field(default=None, description="是否请求生成专属CG")

# --- 前端玩家交互请求 ---
class PlayerDialogueRequest(BaseModel):
    message: str = Field(..., description="玩家输入的话语")
    character_id: str = Field(default="lin_yuqing", description="交谈的NPC ID")
    action_type: str = Field(default="speak", description="行动类型: speak, invite, give_gift")

# --- 前端对话返回响应 ---
class DialogueTurnResponse(BaseModel):
    speaker: str
    dialogue: str
    emotion: str
    expression: str
    action: Optional[str] = None
    inner_thought: Optional[str] = None
    affection: int
    affection_delta: int
    trust: int
    stage: str
    applied_effects: List[Dict[str, Any]] = []
    cg_image_url: Optional[str] = None
    event_triggered: Optional[str] = None

# --- 世界与状态 ---
class WorldStateResponse(BaseModel):
    day_number: int
    weekday: str
    time_slot: str
    weather: str
    player_location: str
    location_name: str
    location_description: str
    present_characters: List[str]

class AdvanceTimeRequest(BaseModel):
    target_location: Optional[str] = None

class CharacterStatusResponse(BaseModel):
    character_id: str
    name: str
    title: str
    affection: int
    trust: int
    stage: str
    current_mood: str
    current_location: str
    schedule_activity: Optional[str] = None

class SaveSlotInfo(BaseModel):
    slot_index: int
    title: str
    saved_at: str
    preview: Dict[str, Any]
