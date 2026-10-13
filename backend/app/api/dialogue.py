import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database.session import get_db
from ..database.models import WorldState, CharacterState, Relationship, Player
from ..models.schemas import PlayerDialogueRequest, DialogueTurnResponse
from ..memory.manager import MemoryManager
from ..core.arbitrator import Arbitrator
from ..core.config import get_world_config, get_character_config
from ..ai.llm.client import LLMClient
from ..ai.comfyui.client import ComfyUIClient

logger = logging.getLogger(__name__)
router = APIRouter()
llm_client = LLMClient()
comfyui_client = ComfyUIClient()

@router.post("/chat", response_model=DialogueTurnResponse)
async def chat_with_character(
    req: PlayerDialogueRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    核心交互接口：玩家与 NPC 进行自由对话
    执行流程：状态读取 -> 记忆装配 -> LLM 生成 -> 规则裁决 -> 状态与记忆写入 -> 响应下发
    """
    # 1. 查询世界状态
    world_res = await db.execute(select(WorldState).limit(1))
    world = world_res.scalar_one_or_none()
    if not world:
        raise HTTPException(status_code=500, detail="世界状态未初始化")

    # 2. 查询角色与关系
    rel_res = await db.execute(select(Relationship).where(Relationship.character_id == req.character_id))
    relationship = rel_res.scalar_one_or_none()
    if not relationship:
        raise HTTPException(status_code=404, detail="未找到该角色好感数据")

    char_res = await db.execute(select(CharacterState).where(CharacterState.character_id == req.character_id))
    char_state = char_res.scalar_one_or_none()
    if not char_state:
        raise HTTPException(status_code=404, detail="未找到该角色状态数据")

    # 3. 记忆管理器与上下文组装
    memory_mgr = MemoryManager(db)
    recent_history = await memory_mgr.get_recent_dialogue_context(character_id=req.character_id, limit=8)
    episodic_memories = await memory_mgr.get_episodic_memories(character_id=req.character_id, limit=4)

    # 4. 获取地点与时间展示名称
    world_cfg = get_world_config()
    loc_name = "图书馆"
    for loc in world_cfg.get("locations", []):
        if loc.get("id") == world.player_location:
            loc_name = loc.get("name", "校园")
            break

    time_name = "下午"
    for ts in world_cfg.get("time_slots", []):
        if ts.get("id") == world.time_slot:
            time_name = ts.get("name", "此时")
            break

    # 5. 调用云端大模型生成
    llm_resp = await llm_client.generate_dialogue(
        character_id=req.character_id,
        player_message=req.message,
        affection=relationship.affection,
        trust=relationship.trust,
        stage=relationship.stage,
        location_name=loc_name,
        time_slot_name=time_name,
        weather=world.weather,
        episodic_memories=episodic_memories,
        recent_history=recent_history,
    )

    # 6. 核心规则裁决（防作弊、防越权、防数值爆炸）
    aff_delta, trust_delta, applied_details = Arbitrator.arbitrate_effects(
        proposed_effects=llm_resp.proposed_effects,
        relationship=relationship,
        char_state=char_state,
        world_state=world,
    )

    clean_expression = Arbitrator.sanitize_expression(llm_resp.expression)
    clean_emotion = Arbitrator.sanitize_emotion(llm_resp.emotion)

    # 7. 更新对话轮数
    world.turns_in_current_scene += 1

    # 8. 持久化短期对话日志
    await memory_mgr.save_dialogue_turn(
        speaker_name="你",
        character_id="player",
        content=req.message,
        location=world.player_location,
        game_day=world.day_number,
        game_time_slot=world.time_slot,
    )
    await memory_mgr.save_dialogue_turn(
        speaker_name=llm_resp.speaker,
        character_id=req.character_id,
        content=llm_resp.dialogue,
        emotion=clean_emotion,
        expression=clean_expression,
        location=world.player_location,
        game_day=world.day_number,
        game_time_slot=world.time_slot,
    )

    # 9. 智能生成关键情节记忆（如好感度产生跃迁或触碰重要话题）
    if abs(aff_delta) >= 2 or llm_resp.emotion in ["blush", "surprised"]:
        memory_summary = f"在{loc_name}与你交谈，{llm_resp.speaker}{clean_emotion}，对白提到：“{llm_resp.dialogue[:30]}...”"
        await memory_mgr.add_memory(
            character_id=req.character_id,
            summary=memory_summary,
            importance=4 if clean_emotion == "blush" else 3,
            location=loc_name,
            game_day=world.day_number,
        )

    # 10. CG 生图触发（如符合特定事件）
    cg_url = None
    if llm_resp.image_request:
        prompt_id = await comfyui_client.generate_cg(
            prompt=llm_resp.image_request.get("prompt", "anime girl in library, masterpiece"),
        )
        if prompt_id:
            cg_url = f"/api/images/view/{prompt_id}"

    await db.commit()

    return DialogueTurnResponse(
        speaker=llm_resp.speaker,
        dialogue=llm_resp.dialogue,
        emotion=clean_emotion,
        expression=clean_expression,
        action=llm_resp.action,
        inner_thought=llm_resp.inner_thought,
        affection=relationship.affection,
        affection_delta=aff_delta,
        trust=relationship.trust,
        stage=relationship.stage,
        applied_effects=applied_details,
        cg_image_url=cg_url,
        event_triggered=llm_resp.event_trigger,
    )
