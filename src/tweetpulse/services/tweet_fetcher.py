import tweepy
from typing import List, Dict, Any
from pydantic import BaseModel

class TweetResponse(BaseModel):
  id: str
  content: str
  author_id: str
  created_at: str
  metrics: Dict[str, Any]

class TweetsResponse(BaseModel):
  tweets: List[TweetResponse]
  total: int

class TweetFetcher:
  def __init__(self, bearer_token: str):
    self.client = tweepy.Client(bearer_token=bearer_token)
  
  async def fetch_tweets(self, query: str, max_results: int = 10) -> TweetsResponse:
    try:
      tweets = self.client.search_recent_tweets(
        query=query,
        max_results=max_results,
        tweet_fields=[
            "created_at", "public_metrics", "author_id", "lang"
        ]
      )
        
      if not tweets.data:
        return TweetsResponse(tweets=[], total=0)
        
      tweet_list = []
      for tweet in tweets.data:
            tweet_list.append(TweetResponse(
                id=str(tweet.id),
                content=tweet.text,
                author_id=str(tweet.author_id),
                created_at=tweet.created_at.isoformat() if tweet.created_at else "",
                metrics=tweet.public_metrics or {}
            ))
        
      return TweetsResponse(
        tweets=tweet_list,
        total=tweets.meta.get("result_count", 0)
      )
        
    except Exception as e:
        print(f"Erro ao buscar tweets: {e}")
        return TweetsResponse(tweets=[], total=0)