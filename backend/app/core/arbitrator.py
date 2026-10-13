from typing import List, Dict, Any, Tuple
from ..models.schemas import ProposedEffect
from ..database.models import Relationship, CharacterState, WorldState

VALID_EXPRESSIONS = {"neutral", "happy", "blush", "surprised", "thinking", "pout", "sad"}
VALID_EMOTIONS = {"neutral", "happy", "blush", "surprised", "thinking", "pout", "sad", "angry"}

class Arbitrator:
    """
    游戏规则裁决器
    负责审核、限制、修剪 AI 大模型提议的状态变动，确保游戏数值平衡与世界逻辑闭环。
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
        返回: (applied_affection_delta, applied_trust_delta, applied_details)
        """
        applied_affection_delta = 0
        applied_trust_delta = 0
        applied_details = []

        # 疲劳度/长对话衰减因子
        fatigue_penalty = 1.0
        if world_state.turns_in_current_scene >= cls.FATIGUE_TURNS_THRESHOLD:
            fatigue_penalty = 0.5  # 聊太久了，好感度增长减半甚至停滞

        for effect in proposed_effects:
            if effect.type == "affection_delta":
                try:
                    val = int(effect.value)
                except (ValueError, TypeError):
                    continue

                # 1. 裁剪单次最大增减幅
                clamped_val = max(cls.MIN_AFFECTION_DELTA, min(cls.MAX_AFFECTION_DELTA, val))

                # 2. 疲劳衰减
                if clamped_val > 0:
                    clamped_val = int(round(clamped_val * fatigue_penalty))

                # 3. 阶段好感度上限保护 (例如尚未表白突破时，上限为 60)
                current_aff = relationship.affection
                has_confessed = relationship.flags.get("confessed", False) if relationship.flags else False
                
                if not has_confessed and (current_aff + clamped_val > cls.PRE_CONFESSION_CAP):
                    actual_delta = max(0, cls.PRE_CONFESSION_CAP - current_aff)
                else:
                    actual_delta = clamped_val

                # 4. 数值不能低于 0 或超过 100
                new_aff = max(0, min(100, current_aff + actual_delta))
                final_delta = new_aff - current_aff

                if final_delta != 0:
                    applied_affection_delta += final_delta
                    relationship.affection = new_aff
                    applied_details.append({
                        "type": "affection_change",
                        "delta": final_delta,
                        "current": new_aff,
                        "reason": effect.reason or "对话互动"
                    })

            elif effect.type == "trust_delta":
                try:
                    val = int(effect.value)
                except (ValueError, TypeError):
                    continue
                clamped_trust_delta = max(-2, min(2, val))
                new_trust = max(0, min(100, relationship.trust + clamped_trust_delta))
                t_delta = new_trust - relationship.trust
                if t_delta != 0:
                    applied_trust_delta += t_delta
                    relationship.trust = new_trust
                    applied_details.append({
                        "type": "trust_change",
                        "delta": t_delta,
                        "current": new_trust,
                    })

        # 5. 根据新数值更新关系阶段
        cls._update_relationship_stage(relationship)

        return applied_affection_delta, applied_trust_delta, applied_details

    @classmethod
    def _update_relationship_stage(cls, relationship: Relationship):
        """自动推导关系阶段"""
        aff = relationship.affection
        has_confessed = relationship.flags.get("confessed", False) if relationship.flags else False

        if aff >= 80 and has_confessed:
            relationship.stage = "lover"         # 恋人
        elif aff >= 50:
            relationship.stage = "close"         # 亲密/暧昧
        elif aff >= 20:
            relationship.stage = "friend"        # 朋友
        else:
            relationship.stage = "acquaintance"  # 熟人/普通同学
