from typing import Literal, Union, List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

class VariableOperation(BaseModel):
    """原子变量操作 (支持增量 delta 与全量 replace)"""
    model_config = ConfigDict(extra="forbid")

    op: Literal["delta", "replace"] = Field(..., description="操作类型: delta(数值增减) 或 replace(替换)")
    path: str = Field(..., min_length=2, max_length=200, description="变量路径，例如: /characters/lin_yuqing/relationship/affection")
    value: Union[int, float, str, bool] = Field(..., description="变动数值或新状态")
    reason: str = Field(default="", max_length=300, description="引发该变量变化的原因")

class VariablePatch(BaseModel):
    """变量补丁载荷 (类似 JSONPatch，带有基线版本防时序并发冲突)"""
    model_config = ConfigDict(extra="forbid")

    base_revision: int = Field(..., ge=0, description="提出修改时依据的基线状态版本")
    operations: List[VariableOperation] = Field(default_factory=list, max_length=15, description="操作序列")
    source: str = Field(default="dialogue", description="变更来源: dialogue, action, phone, system")

class AppliedChangeDetail(BaseModel):
    path: str
    op: str
    old_value: Any
    new_value: Any
    delta: Optional[float] = None
    reason: str
    status: Literal["applied", "rejected", "clamped"] = "applied"
    reject_reason: Optional[str] = None

class ApplyPatchResult(BaseModel):
    success: bool
    revision_before: int
    revision_after: int
    applied_changes: List[AppliedChangeDetail] = []
    rejected_changes: List[AppliedChangeDetail] = []

class VariableSnapshot(BaseModel):
    """统一游戏状态快照 (stat_data 单一真源)"""
    schema_version: int = 1
    revision: int = 1
    world: Dict[str, Any]
    player: Dict[str, Any]
    characters: Dict[str, Any]
    events: Dict[str, Any] = {}
    system: Dict[str, Any] = {}
