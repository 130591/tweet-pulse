from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from tweetpulse.core.config import settings
from tweetpulse.services.tweet_fetcher import TweetFetcher
from tweetpulse.models.database import SessionLocal, get_db

router = APIRouter()

class TweetStats(BaseModel):
    total_tweets: int
    positive_tweets: int
    negative_tweets: int
    neutral_tweets: int

@router.get("/stats", response_model=TweetStats)
async def get_stats(
    db: AsyncSession = Depends(get_db)
):
    """Retorna estatísticas sobre os tweets."""
    try:
        # Exemplo de consulta para obter estatísticas
        # Nota: Você precisará implementar essas consultas reais baseadas no seu modelo
        return {
            "total_tweets": 0,
            "positive_tweets": 0,
            "negative_tweets": 0,
            "neutral_tweets": 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings")
async def get_app_settings():
    """Retorna as configurações da aplicação."""
    return {
        "debug": settings.DEBUG,
        "max_tweets_per_request": settings.MAX_TWEETS_PER_REQUEST,
        "twitter_configured": bool(settings.TWITTER_BEARER_TOKEN)
    }

class TweetResponse(BaseModel):
    id: str
    content: str
    author_id: str
    created_at: str
    sentiment: Optional[str] = None
    confidence: Optional[float] = None

@router.get("/tweets", response_model=List[TweetResponse])
async def get_tweets(
    limit: int = 100,
    offset: int = 0,
    sentiment: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
	"""Retorna uma lista de tweets com opções de filtro."""
	try:
		# Exemplo de implementação - você precisará adaptar para seu caso de uso real
		fetcher = TweetFetcher(db)
		return await fetcher.fetch_tweets(limit=limit, offset=offset, sentiment=sentiment)
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))
	return await fetcher.fetch_tweets("python", settings.MAX_TWEETS_PER_REQUEST)