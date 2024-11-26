from fastapi import APIRouter
from .server import router as chat_router
from .openai_compatible import router as openai_router

router = APIRouter()
router.include_router(chat_router)
router.include_router(openai_router) 
