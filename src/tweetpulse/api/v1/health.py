from fastapi import APIRouter
from tweetpulse.core.config import settings

router = APIRouter()

@app.get("/health")
async def health():
  return {"status": "healthy", "debug": settings.DEBUG}
