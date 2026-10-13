import logging
from typing import Optional, Dict, Any
import httpx
from ...core.config import settings
from .client import LLMClient

logger = logging.getLogger(__name__)

class ProviderManager:
    """
    统一模型供应管理中心 (LLM & Image Provider Manager)
    负责动态读取最新配置、提供连接测试、保护敏感密钥、确保设置热更新立即可用。
    """

    _instance: Optional["ProviderManager"] = None
    _llm_client: Optional[LLMClient] = None

    @classmethod
    def get_instance(cls) -> "ProviderManager":
        if cls._instance is None:
            cls._instance = ProviderManager()
        return cls._instance

    def get_llm_client(self) -> LLMClient:
        """获取当前配置绑定的 LLM 客户端实例"""
        if self._llm_client is None:
            self._llm_client = LLMClient()
        return self._llm_client

    def reload_llm_client(self):
        """当配置更新时，强制刷新 LLM 客户端"""
        logger.info("重新装载 LLM 客户端配置...")
        self._llm_client = LLMClient()

    async def test_llm_connection(self) -> Dict[str, Any]:
        """测试当前云端大模型连接状态"""
        client = self.get_llm_client()
        if not client.api_key or client.api_key.startswith("your_api"):
            return {
                "success": True,
                "mode": "mock",
                "message": "当前处于智能离线模式，无需公网 API Key 即可畅玩！",
            }

        headers = {
            "Authorization": f"Bearer {client.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": client.model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 5,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as http_c:
                res = await http_c.post(
                    f"{client.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                if res.status_code == 200:
                    return {
                        "success": True,
                        "mode": "cloud",
                        "model": client.model,
                        "message": f"成功连接到云端大模型: {client.model}",
                    }
                else:
                    return {
                        "success": False,
                        "status_code": res.status_code,
                        "message": f"云端服务返回错误: {res.text[:120]}",
                    }
        except Exception as e:
            return {
                "success": False,
                "message": f"连接异常或超时: {str(e)}",
            }
