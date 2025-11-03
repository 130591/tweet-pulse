import tweepy
from typing import Optional

class TwitterClient:
  def __init__(self, bearer_token: str):
    self.client = tweepy.Client(bearer_token=bearer_token)
  
  def search_tweets(self, query: str, max_results: int = 10, **kwargs) -> tweepy.Response:
    """Busca tweets usando a API do Twitter."""
    return self.client.search_recent_tweets(
      query=query,
      max_results=max_results,
      tweet_fields=["created_at", "public_metrics", "author_id", "lang"],
      **kwargs
    )