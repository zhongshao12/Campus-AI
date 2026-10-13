from fastapi import APIRouter
from .dialogue import router as dialogue_router
from .world import router as world_router
from .characters import router as characters_router
from .saves import router as saves_router
from .phone import router as phone_router
from .settings import router as settings_router
from .images import router as images_router

api_router = APIRouter()
api_router.include_router(dialogue_router, prefix="/dialogue", tags=["Dialogue"])
api_router.include_router(world_router, prefix="/world", tags=["World"])
api_router.include_router(characters_router, prefix="/characters", tags=["Characters"])
api_router.include_router(saves_router, prefix="/saves", tags=["Saves"])
api_router.include_router(phone_router, prefix="/phone", tags=["Phone"])
api_router.include_router(settings_router, prefix="/settings", tags=["Settings"])
api_router.include_router(images_router, prefix="/images", tags=["Images"])
