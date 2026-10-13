import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database.session import get_db
from ..database.models import ImageRecord, GenerationJob
from ..ai.comfyui.client import ComfyUIClient

logger = logging.getLogger(__name__)
router = APIRouter()
comfy_client = ComfyUIClient()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
GENERATED_DIR = BASE_DIR.parent / "data" / "generated_images"

# 默认优雅降级占位 SVG (当 ComfyUI 未生成或生成中时提供完美二次元视觉呈现，不报 404)
PLACEHOLDER_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="768" viewBox="0 0 1024 768">
  <defs>
    <radialGradient id="bg" cx="50%" cy="40%" r="60%">
      <stop offset="0%" stop-color="#38bdf8"/>
      <stop offset="40%" stop-color="#1e3a8a"/>
      <stop offset="100%" stop-color="#090d16"/>
    </radialGradient>
  </defs>
  <rect width="1024" height="768" fill="url(#bg)"/>
  <circle cx="512" cy="340" r="140" fill="rgba(255,255,255,0.08)"/>
  <text x="512" y="360" font-size="64" fill="#ffffff" text-anchor="middle" font-family="sans-serif">✨ Campus AI CG ✨</text>
  <text x="512" y="420" font-size="24" fill="#93c5fd" text-anchor="middle" font-family="sans-serif">【独家剧情回忆已收录入图鉴】</text>
</svg>"""

@router.get("/view/{prompt_id}")
async def view_generated_image(prompt_id: str, db: AsyncSession = Depends(get_db)):
    """
    获取生成的 CG 图像
    1. 优先检查本地已落盘文件；
    2. 若未落盘则向 ComfyUI 轮询提取并下载；
    3. 若离线或超时则优雅降级为唯美纪念插画，绝不白屏崩溃。
    """
    # 1. 检查是否存在直接以 prompt_id 命名的文件
    for ext in [".png", ".jpg", ".webp"]:
        local_file = GENERATED_DIR / f"{prompt_id}{ext}"
        if local_file.exists():
            return FileResponse(local_file)

    # 2. 查询 ComfyUI 结果
    if await comfy_client.is_available():
        res = await comfy_client.poll_history(prompt_id, timeout=10, interval=1.0)
        if res and res.get("filename"):
            saved = await comfy_client.download_image(
                res["filename"],
                res.get("subfolder", ""),
                res.get("type", "output"),
            )
            if saved and saved.exists():
                # 记录到图鉴
                rec = ImageRecord(
                    prompt_id=prompt_id,
                    prompt="Anime Scene CG",
                    file_path=f"/generated/{res['filename']}",
                    title="专属校园回忆",
                )
                db.add(rec)
                await db.commit()
                return FileResponse(saved)

    # 3. 降级返回 SVG 纪念卡片
    return Response(content=PLACEHOLDER_SVG, media_type="image/svg+xml")

@router.get("/jobs/{prompt_id}")
async def get_job_status(prompt_id: str):
    """查询指定生图任务的执行状态"""
    if not await comfy_client.is_available():
        return {"status": "offline", "prompt_id": prompt_id, "message": "ComfyUI 离线"}

    res = await comfy_client.poll_history(prompt_id, timeout=1)
    if res and res.get("filename"):
        return {
            "status": "completed",
            "prompt_id": prompt_id,
            "filename": res["filename"],
            "url": f"/generated/{res['filename']}",
        }
    return {"status": "processing", "prompt_id": prompt_id}

@router.get("/gallery")
async def get_gallery(db: AsyncSession = Depends(get_db)):
    """获取所有已解锁的 CG 图鉴列表"""
    res = await db.execute(select(ImageRecord).order_by(ImageRecord.id.desc()))
    records = res.scalars().all()
    return [
        {
            "id": r.id,
            "title": r.title,
            "file_path": r.file_path,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "",
        }
        for r in records
    ]
