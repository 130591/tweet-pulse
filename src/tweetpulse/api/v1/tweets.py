from fastapi import APIRouter, Depends
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from tweetpulse.services.tweet_service import TweetService
from tweetpulse.core.config import settings
from tweetpulse.core.dependencies import get_session, get_tweet_fetcher

router = APIRouter()

@router.get("/stats")
async def get_stats(
  session: Annotated[AsyncSession, Depends(get_session)] = None,
):
  
  service = TweetService(session)
  stats = await service.get_stats()
  return stats

@app.get("/settings")
async def get_app_settings():
	return {
		"debug": settings.DEBUG,
		"max_tweets_per_request": settings.MAX_TWEETS_PER_REQUEST,
		"twitter_configured": bool(settings.TWITTER_BEARER_TOKEN)
	}

@app.get("/tweets")
async def get_tweets(
  fetcher = Depends(get_tweet_fetcher)
):
  return await fetcher.fetch_tweets("python", settings.MAX_TWEETS_PER_REQUEST)