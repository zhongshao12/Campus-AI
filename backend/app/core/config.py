import os
import yaml
from pathlib import Path
from typing import Dict, Any
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = BASE_DIR / "config"

class Settings(BaseSettings):
    APP_NAME: str = "Campus AI"
    DEBUG: bool = True
    
    # LLM
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"
    LLM_MODEL: str = "deepseek-chat"
    
    # ComfyUI
    COMFYUI_BASE_URL: str = "http://127.0.0.1:8188"
    
    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

def load_yaml(file_path: Path) -> Dict[str, Any]:
    if not file_path.exists():
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def get_world_config() -> Dict[str, Any]:
    return load_yaml(CONFIG_DIR / "world.yaml")

def get_character_config(character_id: str) -> Dict[str, Any]:
    char_file = CONFIG_DIR / "characters" / f"{character_id}.yaml"
    return load_yaml(char_file)
