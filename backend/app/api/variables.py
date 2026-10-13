from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from ..database.session import get_db
from ..database.models import VariableChange, GameStateRevision
from ..variables.schemas import VariableSnapshot, VariablePatch, ApplyPatchResult
from ..variables.snapshot import SnapshotBuilder
from ..variables.engine import VariableEngine, RevisionConflictError

router = APIRouter()

@router.get("/snapshot", response_model=VariableSnapshot)
async def get_current_snapshot(db: AsyncSession = Depends(get_db)):
    """获取当前游戏统一变量状态快照 (stat_data 单一真源)"""
    return await SnapshotBuilder.build_snapshot(db)

@router.get("/changes")
async def get_variable_changes(
    limit: int = Query(default=30, le=100),
    character_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """查询变量变更审计日志 (追溯每一次数值变化的因果与版本)"""
    stmt = select(VariableChange).order_by(desc(VariableChange.id)).limit(limit)
    if character_id:
        stmt = stmt.where(VariableChange.character_id == character_id)

    res = await db.execute(stmt)
    records = res.scalars().all()

    return [
        {
            "id": r.id,
            "turn_id": r.turn_id,
            "revision_before": r.revision_before,
            "revision_after": r.revision_after,
            "source": r.source,
            "character_id": r.character_id,
            "path": r.path,
            "op": r.op,
            "old_value": r.old_value,
            "new_value": r.new_value,
            "reason": r.reason,
            "time": r.created_at.strftime("%H:%M:%S") if r.created_at else "",
        }
        for r in records
    ]

@router.post("/patch", response_model=ApplyPatchResult)
async def apply_variable_patch(
    patch: VariablePatch,
    db: AsyncSession = Depends(get_db),
):
    """
    提交变量补丁更新 (V0.2.1 安全强化版)
    1. 强制设定 source='external_client'，严禁外部请求自称 system 绕过鉴权；
    2. 严格乐观锁版本校验，若基线版本与当前数据库不一致抛出 409 冲突拒绝。
    """
    # 强制防伪装来源
    patch.source = "external_client"

    try:
        result = await VariableEngine.apply_patch(
            patch=patch,
            db=db,
            trusted_system=False,
        )
        await db.commit()
        return result
    except RevisionConflictError as err:
        rev_res = await db.execute(select(GameStateRevision).limit(1))
        current_rev = rev_res.scalar_one().revision if rev_res else 1
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "REVISION_CONFLICT",
                "message": str(err),
                "current_revision": current_rev,
                "submitted_revision": patch.base_revision,
            }
        )
