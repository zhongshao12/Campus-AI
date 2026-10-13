import uuid
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import httpx

from ...core.config import settings

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
GENERATED_DIR = BASE_DIR.parent / "data" / "generated_images"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
WORKFLOWS_DIR = BASE_DIR.parent / "workflows"

class ComfyUIClient:
    """
    ComfyUI 本地生图引擎客户端 (专为 RTX 4070 8GB 调优)
    支持异步生图提交、任务状态轮询、成品图下载落盘与多工作流自适应。
    """

    def __init__(self, base_url: Optional[str] = None):
        self.client_id = str(uuid.uuid4())

    @property
    def base_url(self) -> str:
        return settings.COMFYUI_BASE_URL.rstrip("/")

    async def is_available(self) -> bool:
        """检查本地 ComfyUI 是否在线运行"""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.base_url}/system_stats")
                return res.status_code == 200
        except Exception:
            return False

    def _build_workflow_payload(
        self,
        prompt: str,
        negative_prompt: str,
        seed: int,
        width: int,
        height: int,
    ) -> Dict[str, Any]:
        """优先从 workflows/scene_cg.json 读取，若无则使用通用高兼容 SDXL/Anima 工作流"""
        cg_workflow_file = WORKFLOWS_DIR / "scene_cg.json"
        if cg_workflow_file.exists():
            try:
                with open(cg_workflow_file, "r", encoding="utf-8") as f:
                    workflow_data = json.load(f)
                return {"client_id": self.client_id, "prompt": workflow_data}
            except Exception as e:
                logger.warning(f"读取 workflows/scene_cg.json 失败: {e}，使用默认工作流模板。")

        return {
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
                        "steps": 24,
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

    async def submit_prompt(
        self,
        prompt: str,
        negative_prompt: str = "low quality, bad anatomy, blurry, worst quality",
        seed: int = 123456,
        width: int = 1024,
        height: int = 768,
    ) -> Optional[str]:
        """向 ComfyUI 提交任务，返回 prompt_id"""
        payload = self._build_workflow_payload(prompt, negative_prompt, seed, width, height)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(f"{self.base_url}/prompt", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    prompt_id = data.get("prompt_id")
                    logger.info(f"ComfyUI 任务已成功提交，prompt_id: {prompt_id}")
                    return prompt_id
        except Exception as e:
            logger.warning(f"提交 ComfyUI 任务异常: {e}")
        return None

    async def poll_history(self, prompt_id: str, timeout: int = 45, interval: float = 1.5) -> Optional[Dict[str, Any]]:
        """轮询查询指定任务执行状态，直到成功生成图像或超时"""
        elapsed = 0.0
        async with httpx.AsyncClient(timeout=10.0) as client:
            while elapsed < timeout:
                try:
                    res = await client.get(f"{self.base_url}/history/{prompt_id}")
                    if res.status_code == 200:
                        data = res.json()
                        if prompt_id in data:
                            history_entry = data[prompt_id]
                            # 提取输出图片列表
                            outputs = history_entry.get("outputs", {})
                            for node_id, node_output in outputs.items():
                                if "images" in node_output and len(node_output["images"]) > 0:
                                    img_info = node_output["images"][0]
                                    return {
                                        "status": "completed",
                                        "filename": img_info.get("filename"),
                                        "subfolder": img_info.get("subfolder", ""),
                                        "type": img_info.get("type", "output"),
                                    }
                except Exception as e:
                    logger.debug(f"轮询 ComfyUI history 出现重试: {e}")

                await asyncio.sleep(interval)
                elapsed += interval

        return None

    async def download_image(self, filename: str, subfolder: str = "", img_type: str = "output") -> Optional[Path]:
        """从 ComfyUI 获取生成完毕的图片并持久化落盘到 data/generated_images"""
        target_path = GENERATED_DIR / filename
        params = {
            "filename": filename,
            "subfolder": subfolder,
            "type": img_type,
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.get(f"{self.base_url}/view", params=params)
                if res.status_code == 200:
                    target_path.write_bytes(res.content)
                    logger.info(f"ComfyUI 图片已成功持久化至: {target_path}")
                    return target_path
        except Exception as e:
            logger.error(f"下载 ComfyUI 图片失败: {e}")
        return None

    async def generate_cg(
        self,
        prompt: str,
        negative_prompt: str = "low quality, bad anatomy, blurry, worst quality",
        seed: int = 123456,
        width: int = 1024,
        height: int = 768,
        wait: bool = False,
    ) -> Optional[str]:
        """
        统一生图入口：
        若 ComfyUI 在线：提交任务；若 wait=True 则等待生成并下载，返回本地访问 URL；
        若 ComfyUI 离线：优雅降级并记录。
        """
        if not await self.is_available():
            logger.info("ComfyUI 未连接，启用占位降级展示。")
            return None

        prompt_id = await self.submit_prompt(prompt, negative_prompt, seed, width, height)
        if not prompt_id:
            return None

        if wait:
            poll_res = await self.poll_history(prompt_id, timeout=30)
            if poll_res and poll_res.get("filename"):
                saved_path = await self.download_image(
                    filename=poll_res["filename"],
                    subfolder=poll_res.get("subfolder", ""),
                    img_type=poll_res.get("type", "output"),
                )
                if saved_path:
                    return f"/generated/{poll_res['filename']}"

        # 异步返回可由前端直接调用的任务查询/预览 URL
        return f"/api/images/view/{prompt_id}"
