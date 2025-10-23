from typing import TypedDict 
from .config import settings, Settings
from tweetpulse.services.tweet_fetcher import TweetFetcher
from tweetpulse.repositories.tweet_repository import TweetRepository
from tweetpulse.utils.twitter_client import TwitterClient
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import Depends

class TweetPulseSettings(TypedDict):
  twitter_token: str
  db_url: str

# Define base dependencies first
def get_twitter_client() -> TwitterClient:
  return TwitterClient(settings.TWITTER_BEARER_TOKEN)

def get_db_session() -> Session:
  engine = create_engine(settings.DATABASE_URL)
  SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
  return SessionLocal()

def get_tweet_repository(session: Session = Depends(get_db_session)) -> TweetRepository:
  return TweetRepository(session)

# Define composed dependencies
def get_tweet_fetcher(
  twitter_client: TwitterClient = Depends(get_twitter_client),
  repository: TweetRepository = Depends(get_tweet_repository)
) -> TweetFetcher:
  return TweetFetcher(twitter_client, repository)

def get_settings() -> TweetPulseSettings:
  return TweetPulseSettings(
    twitter_token=settings.TWITTER_BEARER_TOKEN,
    db_url=settings.DATABASE_URL
  )

def get_app_settings() -> Settings:
  return settings