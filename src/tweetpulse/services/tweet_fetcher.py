import logging
import tweepy
from typing import List, Dict, Any
from pydantic import BaseModel
from tweetpulse.repositories.tweet_repository import TweetRepository
from tweetpulse.utils.twitter_client import TwitterClient

logger = logging.getLogger(__name__)

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
    def __init__(self, twitter_client: TwitterClient, repository: TweetRepository):
        self.client = twitter_client  # Usa TwitterClient customizado
        self.repository = repository
    
    def _parse_tweets(self, tweets: List[tweepy.Tweet]) -> List[TweetResponse]:
        tweet_list = []
        for tweet in tweets:
            tweet_list.append(TweetResponse(
                id=str(tweet.id),
                content=tweet.text,
                author_id=str(tweet.author_id),
                created_at=tweet.created_at.isoformat() if tweet.created_at else "",
                metrics=tweet.public_metrics or {}
            ))
        return tweet_list
    
    def _response_to_tweets(self, response: tweepy.Response) -> TweetsResponse:
        return TweetsResponse(
            tweets=self._parse_tweets(response.data),
            total=response.meta.get("result_count", 0)
        )
    
    async def fetch_tweets(self, query: str, max_results: int = 100) -> TweetsResponse:
        try:
          # Usa o método do TwitterClient customizado
          response = self.client.search_tweets(query, max_results)
          
          if not response.data:
              return TweetsResponse(tweets=[], total=0)
          
          tweets_response = self._response_to_tweets(response)
          
          # Salva cada tweet no banco
          for tweet_data in tweets_response.tweets:
              try:
                  self.repository.create(
                      id=tweet_data.id,
                      content=tweet_data.content,
                      author_id=tweet_data.author_id,
                      created_at=tweet_data.created_at,
                      like_count=tweet_data.metrics.get("like_count", 0),
                      retweet_count=tweet_data.metrics.get("retweet_count", 0),
                      reply_count=tweet_data.metrics.get("reply_count", 0),
                      quote_count=tweet_data.metrics.get("quote_count", 0),
                      bookmark_count=tweet_data.metrics.get("bookmark_count", 0),
                      impression_count=tweet_data.metrics.get("impression_count", 0)
                  )
              except Exception as e:
                  logger.error(f"Erro ao salvar tweet {tweet_data.id}: {e}")
          
          return tweets_response
            
        except Exception as e:
            logger.error(f"Erro ao buscar tweets: {e}")
            return TweetsResponse(tweets=[], total=0)