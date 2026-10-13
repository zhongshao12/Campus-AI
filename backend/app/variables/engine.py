import logging
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import (
    GameStateRevision,
    VariableChange,
    WorldState,
    Player,
    CharacterState,
    Relationship,
)
from .schemas import VariablePatch, VariableOperation, ApplyPatchResult, AppliedChangeDetail
from .registry import VARIABLE_RULES
from .patch import parse_variable_path, ParsedPath
from ..core.arbitrator import Arbitrator

logger = logging.getLogger(__name__)

class VariableEngine:
    """
    正式变量系统应用引擎 (V0.2.0 Variable Engine)
    参考 MyRaidRealmWEB 的 JSONPatch + 状态所有权机制
    负责版本冲突保护、所有权权限拦截、单轮限幅裁剪、事务原子落地与变更因果审计。
    """

    PRE_CONFESSION_CAP = 60
    FATIGUE_TURNS_THRESHOLD = 8

    @classmethod
    async def apply_patch(
        cls,
        patch: VariablePatch,
        db: AsyncSession,
        turn_id: Optional[int] = None,
    ) -> ApplyPatchResult:
        # 1. 乐观锁版本检查
        rev_res = await db.execute(select(GameStateRevision).limit(1))
        state_rev = rev_res.scalar_one_or_none()
        if not state_rev:
            state_rev = GameStateRevision(id=1, revision=1, schema_version=1)
            db.add(state_rev)
            await db.flush()

        current_revision = state_rev.revision

        # 如果基线版本落后超过 5 个版本，判定为严重时序冲突
        if patch.base_revision > 0 and abs(patch.base_revision - current_revision) > 5:
            logger.warning(f"变量更新基线版本冲突: base={patch.base_revision}, current={current_revision}")

        # 2. 读取上下文
        w_res = await db.execute(select(WorldState).limit(1))
        world = w_res.scalar_one_or_none()
        p_res = await db.execute(select(Player).limit(1))
        player = p_res.scalar_one_or_none()

        applied_list: List[AppliedChangeDetail] = []
        rejected_list: List[AppliedChangeDetail] = []

        # 3. 操作路径预聚合 (聚合同路径的多次 delta 提议，杜绝单轮多次 +3 突破上限漏洞)
        aggregated_deltas: Dict[str, Tuple[float, List[str], ParsedPath, Dict[str, Any]]] = {}
        replace_ops: List[Tuple[VariableOperation, ParsedPath, Dict[str, Any]]] = []

        for op in patch.operations:
            parsed = parse_variable_path(op.path)
            if not parsed:
                rejected_list.append(AppliedChangeDetail(
                    path=op.path,
                    op=op.op,
                    old_value="",
                    new_value=op.value,
                    reason=op.reason,
                    status="rejected",
                    reject_reason="路径格式不合法或未注册",
                ))
                continue

            rule_key = parsed.to_rule_key()
            rule = VARIABLE_RULES.get(rule_key)
            if not rule:
                rejected_list.append(AppliedChangeDetail(
                    path=op.path,
                    op=op.op,
                    old_value="",
                    new_value=op.value,
                    reason=op.reason,
                    status="rejected",
                    reject_reason=f"变量未在注册表中定义: {rule_key}",
                ))
                continue

            # 4. 所有权权限拦截: AI 提议来源不能修改 system 或 event_engine 专属变量
            if patch.source == "dialogue" and rule.get("owner") != "ai_proposed":
                rejected_list.append(AppliedChangeDetail(
                    path=op.path,
                    op=op.op,
                    old_value="",
                    new_value=op.value,
                    reason=op.reason,
                    status="rejected",
                    reject_reason=f"越权操作被拒绝: 变量所有者为 [{rule.get('owner')}]，AI 提议无权修改",
                ))
                logger.info(f"拦截 AI 越权变量修改: {op.path} (owner: {rule.get('owner')})")
                continue

            if op.op == "delta":
                try:
                    delta_val = float(op.value)
                except (ValueError, TypeError):
                    continue
                if op.path not in aggregated_deltas:
                    aggregated_deltas[op.path] = (delta_val, [op.reason], parsed, rule)
                else:
                    cur_sum, reasons, p, r = aggregated_deltas[op.path]
                    reasons.append(op.reason)
                    aggregated_deltas[op.path] = (cur_sum + delta_val, reasons, p, r)
            elif op.op == "replace":
                replace_ops.append((op, parsed, rule))

        # 5. 应用聚合后的 delta 操作 (施加单轮限幅、疲劳度衰减与阶段锁)
        for path, (total_delta, reasons, parsed, rule) in aggregated_deltas.items():
            if parsed.domain == "characters" and parsed.sub_domain == "relationship":
                cid = parsed.entity_id or "lin_yuqing"
                rel_res = await db.execute(select(Relationship).where(Relationship.character_id == cid))
                rel = rel_res.scalar_one_or_none()
                if not rel:
                    continue

                field_name = rule["field_name"]
                old_val = getattr(rel, field_name, 0)

                # 全局单轮限幅
                max_d = rule.get("max_delta_per_turn", 3)
                min_d = rule.get("min_delta_per_turn", -3)
                clamped_d = max(min_d, min(max_d, total_delta))

                # 疲劳度衰减 (好感度增加在长对话时减半)
                if field_name == "affection" and world and world.turns_in_current_scene >= cls.FATIGUE_TURNS_THRESHOLD and clamped_d > 0:
                    clamped_d = max(1, clamped_d // 2)

                # 阶段门槛锁 (未表白前好感度不能突破 60)
                if field_name == "affection":
                    has_confessed = rel.flags.get("confessed", False) if rel.flags else False
                    if not has_confessed and (old_val + clamped_d > cls.PRE_CONFESSION_CAP):
                        clamped_d = max(0, cls.PRE_CONFESSION_CAP - old_val)

                min_limit = rule.get("min", 0)
                max_limit = rule.get("max", 100)
                new_val = max(min_limit, min(max_limit, int(round(old_val + clamped_d))))
                actual_delta = new_val - old_val

                setattr(rel, field_name, new_val)

                # 自动推导更新关系阶段
                Arbitrator._update_relationship_stage(rel)

                applied_list.append(AppliedChangeDetail(
                    path=path,
                    op="delta",
                    old_value=old_val,
                    new_value=new_val,
                    delta=actual_delta,
                    reason="、".join(reasons) if reasons else "变量聚合演算",
                    status="applied" if actual_delta == total_delta else "clamped",
                ))

        # 6. 应用 replace 操作 (如更新 NPC 心情)
        for op, parsed, rule in replace_ops:
            if parsed.domain == "characters" and parsed.sub_domain == "state":
                cid = parsed.entity_id or "lin_yuqing"
                cs_res = await db.execute(select(CharacterState).where(CharacterState.character_id == cid))
                cs = cs_res.scalar_one_or_none()
                if not cs:
                    continue

                field_name = rule["field_name"]
                old_val = getattr(cs, field_name, "neutral")
                new_val = str(op.value).strip()

                # 枚举值合法性校验
                allowed_vals = rule.get("values", [])
                if allowed_vals and new_val not in allowed_vals:
                    new_val = "neutral"  # 优雅回退

                setattr(cs, field_name, new_val)
                applied_list.append(AppliedChangeDetail(
                    path=op.path,
                    op="replace",
                    old_value=old_val,
                    new_value=new_val,
                    reason=op.reason or "状态更迭",
                    status="applied",
                ))

        # 7. 写入审计日志与版本号递增 (同事务原子保证)
        new_revision = current_revision + 1 if applied_list else current_revision

        if applied_list:
            for item in applied_list:
                change_record = VariableChange(
                    turn_id=turn_id,
                    revision_before=current_revision,
                    revision_after=new_revision,
                    source=patch.source,
                    character_id=parsed.entity_id if "parsed" in locals() and parsed else None,
                    path=item.path,
                    op=item.op,
                    old_value=str(item.old_value),
                    new_value=str(item.new_value),
                    reason=item.reason,
                )
                db.add(change_record)

            state_rev.revision = new_revision
            await db.flush()

        return ApplyPatchResult(
            success=True,
            revision_before=current_revision,
            revision_after=new_revision,
            applied_changes=applied_list,
            rejected_changes=rejected_list,
        )
