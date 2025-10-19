from typing import TypedDict 
from .config import settings, Settings
from tweetpulse.services.tweet_fetcher import TweetFetcher

class TweetPulseSettings(TypedDict):
  twitter_token: str
  db_url: str


def get_tweet_fetcher() -> TweetFetcher:
  return TweetFetcher(settings.TWITTER_BEARER_TOKEN)

def get_settings() -> TweetPulseSettings:
  return TweetPulseSettings(
    twitter_token=settings.TWITTER_BEARER_TOKEN,
    db_url=settings.DATABASE_URL
  )

def get_app_settings() -> Settings:
  return settings