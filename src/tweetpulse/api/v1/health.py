from fastapi import APIRouter
from tweetpulse.core.config import get_settings

settings = get_settings()

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.VERSION}
