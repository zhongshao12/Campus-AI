import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database.session import get_db
from ..database.models import WorldState, CharacterState, Relationship, Player, GameStateRevision
from ..models.schemas import PlayerDialogueRequest, DialogueTurnResponse
from ..memory.manager import MemoryManager
from ..core.arbitrator import Arbitrator
from ..core.config import get_world_config, get_character_config
from ..ai.llm.provider import ProviderManager
from ..ai.comfyui.client import ComfyUIClient
from ..variables.snapshot import SnapshotBuilder
from ..variables.schemas import VariablePatch, VariableOperation
from ..variables.engine import VariableEngine

logger = logging.getLogger(__name__)
router = APIRouter()
comfyui_client = ComfyUIClient()

@router.post("/chat", response_model=DialogueTurnResponse)
async def chat_with_character(
    req: PlayerDialogueRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    核心交互接口：玩家与 NPC 进行自由面对面对话
    V0.2.0 全面接入 VariableEngine (统一变量补丁、审计与版本递增)
    """
    # 1. 查询世界状态与快照
    world_res = await db.execute(select(WorldState).limit(1))
    world = world_res.scalar_one_or_none()
    if not world:
        raise HTTPException(status_code=500, detail="世界状态未初始化")

    # 读取当前变量快照以取得最新 revision
    snapshot = await SnapshotBuilder.build_snapshot(db)

    # 2. 查询角色与关系
    rel_res = await db.execute(select(Relationship).where(Relationship.character_id == req.character_id))
    relationship = rel_res.scalar_one_or_none()
    if not relationship:
        raise HTTPException(status_code=404, detail="未找到该角色好感数据")

    char_res = await db.execute(select(CharacterState).where(CharacterState.character_id == req.character_id))
    char_state = char_res.scalar_one_or_none()
    if not char_state:
        raise HTTPException(status_code=404, detail="未找到该角色状态数据")

    # 3. 严格校验 NPC 在场约束
    world_cfg = get_world_config()
    char_cfg = get_character_config(req.character_id)
    char_name = char_cfg.get("name", "对方")

    if char_state.current_location != world.player_location:
        loc_item = next((l for l in world_cfg.get("locations", []) if l["id"] == char_state.current_location), None)
        loc_name = loc_item["name"] if loc_item else "校园其他地方"
        schedule = char_cfg.get("schedule", {}).get(world.time_slot, {})
        activity = schedule.get("activity", "忙碌中")

        return DialogueTurnResponse(
            speaker="旁白",
            dialogue=f"【{char_name}】现在并不在当前地点。根据日程，她正在【{loc_name}】{activity}。你可以前往该地点，或者打开手机给她发私信哦。",
            emotion="neutral",
            expression="neutral",
            action=None,
            inner_thought=None,
            affection=relationship.affection,
            affection_delta=0,
            trust=relationship.trust,
            stage=relationship.stage,
            applied_effects=[],
            cg_image_url=None,
            event_triggered=None,
        )

    # 4. 记忆管理器与上下文组装
    memory_mgr = MemoryManager(db)
    recent_history = await memory_mgr.get_recent_dialogue_context(character_id=req.character_id, limit=8)
    episodic_memories = await memory_mgr.get_episodic_memories(character_id=req.character_id, limit=4)

    # 5. 地点与时间展示名称
    current_loc_name = next(
        (l.get("name", "校园") for l in world_cfg.get("locations", []) if l["id"] == world.player_location),
        "校园"
    )
    time_name = next(
        (t.get("name", "此时") for t in world_cfg.get("time_slots", []) if t["id"] == world.time_slot),
        "此时"
    )

    # 6. 动态获取 LLM 客户端并调用
    llm_client = ProviderManager.get_instance().get_llm_client()
    llm_resp = await llm_client.generate_dialogue(
        character_id=req.character_id,
        player_message=req.message,
        affection=relationship.affection,
        trust=relationship.trust,
        stage=relationship.stage,
        location_name=current_loc_name,
        time_slot_name=time_name,
        weather=world.weather,
        episodic_memories=episodic_memories,
        recent_history=recent_history,
    )

    clean_expression = Arbitrator.sanitize_expression(llm_resp.expression)
    clean_emotion = Arbitrator.sanitize_emotion(llm_resp.emotion)

    # 7. 构建标准化 VariablePatch 变量补丁
    operations = []
    for eff in llm_resp.proposed_effects:
        if eff.type == "affection_delta":
            operations.append(VariableOperation(
                op="delta",
                path=f"/characters/{req.character_id}/relationship/affection",
                value=eff.value,
                reason=eff.reason or "对话互动好感变动",
            ))
        elif eff.type == "trust_delta":
            operations.append(VariableOperation(
                op="delta",
                path=f"/characters/{req.character_id}/relationship/trust",
                value=eff.value,
                reason=eff.reason or "对话信任变动",
            ))

    # 心情更迭也纳入正式变量补丁
    operations.append(VariableOperation(
        op="replace",
        path=f"/characters/{req.character_id}/state/current_mood",
        value=clean_emotion,
        reason=f"角色对话情绪表现为 {clean_emotion}",
    ))

    patch = VariablePatch(
        base_revision=snapshot.revision,
        operations=operations,
        source="dialogue",
    )

    # 8. VariableEngine 统一应用补丁 (权限拦截、单轮限幅、事务落库、写入审计日志)
    world.turns_in_current_scene += 1
    patch_result = await VariableEngine.apply_patch(
        patch=patch,
        db=db,
        turn_id=world.turns_in_current_scene,
    )

    # 提取实际生效的好感度与信任度变化
    applied_aff_delta = 0
    applied_details = []
    for chg in patch_result.applied_changes:
        if "affection" in chg.path and chg.delta is not None:
            applied_aff_delta = int(chg.delta)
        applied_details.append({
            "path": chg.path,
            "type": "variable_change",
            "delta": chg.delta,
            "old": chg.old_value,
            "current": chg.new_value,
            "reason": chg.reason,
            "status": chg.status,
        })

    # 9. 持久化对话记录 (带明确 target_character_id)
    await memory_mgr.save_dialogue_turn(
        speaker_name="你",
        character_id="player",
        target_character_id=req.character_id,
        content=req.message,
        location=world.player_location,
        game_day=world.day_number,
        game_time_slot=world.time_slot,
    )
    await memory_mgr.save_dialogue_turn(
        speaker_name=llm_resp.speaker,
        character_id=req.character_id,
        target_character_id=None,
        content=llm_resp.dialogue,
        emotion=clean_emotion,
        expression=clean_expression,
        location=world.player_location,
        game_day=world.day_number,
        game_time_slot=world.time_slot,
    )

    # 10. 智能生成关键情节记忆
    if abs(applied_aff_delta) >= 2 or clean_emotion in ["blush", "surprised"]:
        memory_summary = f"在{current_loc_name}与你交谈，{llm_resp.speaker}{clean_emotion}，对白提到：“{llm_resp.dialogue[:28]}...”"
        await memory_mgr.add_memory(
            character_id=req.character_id,
            summary=memory_summary,
            importance=4 if clean_emotion == "blush" else 3,
            location=current_loc_name,
            game_day=world.day_number,
        )

    # 11. CG 图像任务触发
    cg_url = None
    if llm_resp.image_request:
        prompt = llm_resp.image_request.get("prompt", "anime girl in library, masterpiece")
        cg_url = await comfyui_client.generate_cg(prompt=prompt, wait=False)

    await db.commit()

    return DialogueTurnResponse(
        speaker=llm_resp.speaker,
        dialogue=llm_resp.dialogue,
        emotion=clean_emotion,
        expression=clean_expression,
        action=llm_resp.action,
        inner_thought=llm_resp.inner_thought,
        affection=relationship.affection,
        affection_delta=applied_aff_delta,
        trust=relationship.trust,
        stage=relationship.stage,
        applied_effects=applied_details,
        cg_image_url=cg_url,
        event_triggered=llm_resp.event_trigger,
    )
