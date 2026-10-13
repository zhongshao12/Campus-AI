from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from ..database.session import get_db
from ..database.models import VariableChange, GameStateRevision
from ..variables.schemas import VariableSnapshot, VariablePatch, ApplyPatchResult
from ..variables.snapshot import SnapshotBuilder
from ..variables.engine import VariableEngine

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
    提交变量补丁更新
    经过 VariableEngine 的权限拦截、单轮限幅、所有权校验与版本递增
    """
    result = await VariableEngine.apply_patch(patch=patch, db=db)
    await db.commit()
    return result
