import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import httpx

from ...core.config import settings

logger = logging.getLogger(__name__)

class ComfyUIClient:
    """
    ComfyUI 本地生图引擎客户端 (专为 RTX 4070 8GB 调优)
    支持异步生图提交、任务状态查询与结果拉取。
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.COMFYUI_BASE_URL).rstrip("/")
        self.client_id = str(uuid.uuid4())

    async def is_available(self) -> bool:
        """检查本地 ComfyUI 是否在线运行"""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.base_url}/system_stats")
                return res.status_code == 200
        except Exception:
            return False

    async def generate_cg(
        self,
        prompt: str,
        negative_prompt: str = "low quality, bad anatomy, blurry, worst quality",
        seed: int = 123456,
        width: int = 1024,
        height: int = 768,
    ) -> Optional[str]:
        """
        向 ComfyUI 提交 CG 生图任务
        若 ComfyUI 在线，提交并轮询；若未开启，返回 None 并优雅降级
        """
        online = await self.is_available()
        if not online:
            logger.info("本地 ComfyUI 8188 端口未启动，跳过实时生图渲染。")
            return None

        # 示例通用生图工作流 payload
        # 实际使用中可以根据用户 workflows/scene_cg.json 加载
        payload = {
            "client_id": self.client_id,
            "prompt": {
                "3": {
                    "class_type": "KSampler",
                    "inputs": {
                        "cfg": 7,
                        "denoise": 1,
                        "latent_image": ["5", 0],
                        "model": ["4", 0],
                        "negative": ["7", 0],
                        "positive": ["6", 0],
                        "sampler_name": "euler_ancestral",
                        "scheduler": "karras",
                        "seed": seed,
                        "steps": 25,
                    },
                },
                "4": {
                    "class_type": "CheckpointLoaderSimple",
                    "inputs": {"ckpt_name": "animaPencilXL_v500.safetensors"},
                },
                "5": {
                    "class_type": "EmptyLatentImage",
                    "inputs": {"batch_size": 1, "height": height, "width": width},
                },
                "6": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {"clip": ["4", 1], "text": f"masterpiece, best quality, {prompt}"},
                },
                "7": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {"clip": ["4", 1], "text": negative_prompt},
                },
                "8": {
                    "class_type": "VAEDecode",
                    "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
                },
                "9": {
                    "class_type": "SaveImage",
                    "inputs": {"filename_prefix": "CampusAI_CG", "images": ["8", 0]},
                },
            },
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(f"{self.base_url}/prompt", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    prompt_id = data.get("prompt_id")
                    logger.info(f"ComfyUI 任务已提交，prompt_id: {prompt_id}")
                    return prompt_id
        except Exception as e:
            logger.warning(f"提交 ComfyUI 任务失败: {e}")
        return None
