from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from ..core.config import settings
from ..ai.comfyui.client import ComfyUIClient

router = APIRouter()
comfy_client = ComfyUIClient()

class SettingsUpdateRequest(BaseModel):
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_model: Optional[str] = None
    comfyui_base_url: Optional[str] = None

@router.get("")
async def get_current_settings():
    """获取当前游戏系统运行配置"""
    comfy_online = await comfy_client.is_available()
    masked_key = ""
    if settings.LLM_API_KEY:
        masked_key = settings.LLM_API_KEY[:4] + "******" + settings.LLM_API_KEY[-4:] if len(settings.LLM_API_KEY) > 8 else "已配置"

    return {
        "llm_model": settings.LLM_MODEL,
        "llm_base_url": settings.LLM_BASE_URL,
        "llm_api_key_masked": masked_key,
        "is_using_mock": not bool(settings.LLM_API_KEY) or settings.LLM_API_KEY.startswith("your_api"),
        "comfyui_base_url": settings.COMFYUI_BASE_URL,
        "comfyui_online": comfy_online,
    }

@router.post("")
async def update_settings(req: SettingsUpdateRequest):
    """更新大模型或 ComfyUI 配置"""
    if req.llm_api_key is not None:
        settings.LLM_API_KEY = req.llm_api_key.strip()
    if req.llm_base_url is not None:
        settings.LLM_BASE_URL = req.llm_base_url.strip()
    if req.llm_model is not None:
        settings.LLM_MODEL = req.llm_model.strip()
    if req.comfyui_base_url is not None:
        settings.COMFYUI_BASE_URL = req.comfyui_base_url.strip()

    return {"message": "设置已保存并生效"}
