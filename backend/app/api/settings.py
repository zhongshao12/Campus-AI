from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from ..core.config import settings
from ..ai.comfyui.client import ComfyUIClient
from ..ai.llm.provider import ProviderManager

router = APIRouter()
comfy_client = ComfyUIClient()
provider_mgr = ProviderManager.get_instance()

class SettingsUpdateRequest(BaseModel):
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_model: Optional[str] = None
    comfyui_base_url: Optional[str] = None
    clear_api_key: Optional[bool] = False

@router.get("")
async def get_current_settings():
    """获取当前游戏系统运行配置"""
    comfy_online = await comfy_client.is_available()
    masked_key = ""
    if settings.LLM_API_KEY:
        masked_key = settings.LLM_API_KEY[:3] + "******" + settings.LLM_API_KEY[-3:] if len(settings.LLM_API_KEY) > 6 else "已配置"

    return {
        "llm_model": settings.LLM_MODEL,
        "llm_base_url": settings.LLM_BASE_URL,
        "llm_api_key_masked": masked_key,
        "has_api_key": bool(settings.LLM_API_KEY) and not settings.LLM_API_KEY.startswith("your_api"),
        "is_using_mock": not bool(settings.LLM_API_KEY) or settings.LLM_API_KEY.startswith("your_api"),
        "comfyui_base_url": settings.COMFYUI_BASE_URL,
        "comfyui_online": comfy_online,
    }

@router.post("")
async def update_settings(req: SettingsUpdateRequest):
    """更新大模型或 ComfyUI 配置，支持热重载并防止密钥被空值覆盖"""
    if req.clear_api_key:
        settings.LLM_API_KEY = ""
    elif req.llm_api_key and req.llm_api_key.strip():
        # 只有在传入了非空内容时才覆盖原有 Key
        settings.LLM_API_KEY = req.llm_api_key.strip()

    if req.llm_base_url and req.llm_base_url.strip():
        settings.LLM_BASE_URL = req.llm_base_url.strip()

    if req.llm_model and req.llm_model.strip():
        settings.LLM_MODEL = req.llm_model.strip()

    if req.comfyui_base_url and req.comfyui_base_url.strip():
        settings.COMFYUI_BASE_URL = req.comfyui_base_url.strip()

    # 触发 ProviderManager 重新加载
    provider_mgr.reload_llm_client()

    return {
        "message": "设置已保存并立即热生效",
        "llm_model": settings.LLM_MODEL,
        "has_key": bool(settings.LLM_API_KEY),
    }

@router.post("/test")
async def test_settings_connection():
    """测试当前大模型与 ComfyUI 的连接健康度"""
    llm_test = await provider_mgr.test_llm_connection()
    comfy_online = await comfy_client.is_available()

    return {
        "llm": llm_test,
        "comfyui": {
            "online": comfy_online,
            "base_url": settings.COMFYUI_BASE_URL,
        }
    }
