from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .core.config import settings
from .database.session import init_db
from .api import api_router

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_DIR = PROJECT_ROOT / "data" / "generated_images"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库与初始游戏数据
    await init_db()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="Campus AI: AI 驱动的开放式校园恋爱 Galgame 核心服务端",
    version="0.1.0",
    lifespan=lifespan,
)

# 配置跨域，供前端 Vue 3 调试与访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(api_router, prefix="/api")

# 挂载静态素材服务 (美术资源、立绘、背景与生成的CG)
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")
app.mount("/generated", StaticFiles(directory=str(GENERATED_DIR)), name="generated")

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "0.1.0",
        "llm_model": settings.LLM_MODEL,
        "comfyui_base": settings.COMFYUI_BASE_URL,
    }
