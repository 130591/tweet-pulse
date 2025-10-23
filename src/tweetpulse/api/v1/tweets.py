from fastapi import APIRouter, Depends
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from tweetpulse.services.tweet_service import TweetService

router = APIRouter()

@router.get("/stats")
async def get_stats(
  session: Annotated[AsyncSession, Depends(get_session)] = None,
):
  
  service = TweetService(session)
  stats = await service.get_stats()
  return stats