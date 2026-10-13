from typing import List, Dict, Any, Tuple
from ..models.schemas import ProposedEffect
from ..database.models import Relationship, CharacterState, WorldState

VALID_EXPRESSIONS = {"neutral", "happy", "blush", "surprised", "thinking", "pout", "sad"}
VALID_EMOTIONS = {"neutral", "happy", "blush", "surprised", "thinking", "pout", "sad", "angry"}

class Arbitrator:
    """
    游戏规则裁决器 (V0.1.1 强化版)
    负责聚合审核、全局 Clamp 裁剪、疲劳衰减、阶段锁与恋人确认事件校验。
    """

    MAX_AFFECTION_DELTA = 3
    MIN_AFFECTION_DELTA = -3
    PRE_CONFESSION_CAP = 60
    FATIGUE_TURNS_THRESHOLD = 8

    @classmethod
    def sanitize_expression(cls, raw_expr: str) -> str:
        """表情回退机制"""
        if not raw_expr:
            return "neutral"
        cleaned = raw_expr.lower().strip()
        return cleaned if cleaned in VALID_EXPRESSIONS else "neutral"

    @classmethod
    def sanitize_emotion(cls, raw_emotion: str) -> str:
        """情绪回退机制"""
        if not raw_emotion:
            return "neutral"
        cleaned = raw_emotion.lower().strip()
        return cleaned if cleaned in VALID_EMOTIONS else "neutral"

    @classmethod
    def arbitrate_effects(
        cls,
        proposed_effects: List[ProposedEffect],
        relationship: Relationship,
        char_state: CharacterState,
        world_state: WorldState,
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        裁决状态变动
        核心改进：先预聚合所有提案总和，再进行全局单轮限制，防累计穿透攻击。
        """
        raw_aff_total = 0
        raw_trust_total = 0
        reasons = []

        # 1. 聚合所有同类效果提议
        for effect in proposed_effects:
            if effect.type == "affection_delta":
                try:
                    raw_aff_total += int(effect.value)
                    if effect.reason:
                        reasons.append(effect.reason)
                except (ValueError, TypeError):
                    pass
            elif effect.type == "trust_delta":
                try:
                    raw_trust_total += int(effect.value)
                except (ValueError, TypeError):
                    pass

        applied_details = []

        # 2. 全局单轮好感裁剪 [-3, +3]
        clamped_aff = max(cls.MIN_AFFECTION_DELTA, min(cls.MAX_AFFECTION_DELTA, raw_aff_total))

        # 3. 疲劳度衰减
        if world_state.turns_in_current_scene >= cls.FATIGUE_TURNS_THRESHOLD and clamped_aff > 0:
            clamped_aff = max(1, clamped_aff // 2)

        # 4. 阶段门槛锁 (未表白前上限锁死在 60)
        has_confessed = relationship.flags.get("confessed", False) if relationship.flags else False
        current_aff = relationship.affection
        if not has_confessed and (current_aff + clamped_aff > cls.PRE_CONFESSION_CAP):
            actual_aff_delta = max(0, cls.PRE_CONFESSION_CAP - current_aff)
        else:
            actual_aff_delta = clamped_aff

        # 5. 执行好感更新
        new_aff = max(0, min(100, current_aff + actual_aff_delta))
        final_aff_delta = new_aff - current_aff
        if final_aff_delta != 0:
            relationship.affection = new_aff
            applied_details.append({
                "type": "affection_change",
                "delta": final_aff_delta,
                "current": new_aff,
                "reason": "、".join(reasons) if reasons else "对话互动",
            })

        # 6. 信任度裁剪与更新 [-2, +2]
        clamped_trust = max(-2, min(2, raw_trust_total))
        new_trust = max(0, min(100, relationship.trust + clamped_trust))
        final_trust_delta = new_trust - relationship.trust
        if final_trust_delta != 0:
            relationship.trust = new_trust
            applied_details.append({
                "type": "trust_change",
                "delta": final_trust_delta,
                "current": new_trust,
            })

        # 7. 关系阶段自动演化
        cls._update_relationship_stage(relationship)

        return final_aff_delta, final_trust_delta, applied_details

    @classmethod
    def _update_relationship_stage(cls, relationship: Relationship):
        """关系阶段裁决：恋人阶段必须经过表白事件"""
        aff = relationship.affection
        has_confessed = relationship.flags.get("confessed", False) if relationship.flags else False

        if aff >= 80 and has_confessed:
            relationship.stage = "lover"
        elif aff >= 50:
            relationship.stage = "close"
        elif aff >= 20:
            relationship.stage = "friend"
        else:
            relationship.stage = "acquaintance"
