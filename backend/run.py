import uvicorn
from pathlib import Path
import sys

# 确保 backend 目录在 sys.path 中
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

if __name__ == "__main__":
    print("=" * 60)
    print("正在启动 Campus AI 游戏后端服务...")
    print("API 文档地址: http://127.0.0.1:8000/docs")
    print("=" * 60)
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
