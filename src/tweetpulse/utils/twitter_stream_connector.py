from tweetpulse.core.config import get_settings
import asyncio
from datetime import datetime
from redis.asyncio import Redis
from typing import List
import tweepy
import logging

logger = logging.getLogger(__name__)

settings = get_settings()

class TwitterStreamConnector:
  def __init__(self, redis: Redis, keywords: List[str]):
    self.redis = redis
    self.keywords = keywords
    self.stream_key = "ingest:stream"
  
  self.client = tweepy.StreamingClient(bearer_token=settings.TWITTER_BEARER_TOKEN, wait_on_rate_limit=True)
  
  async def start(self):
    print(f"Starting stream with keywords: {self.keywords}")

  for keyword in self.keywords:
    self.client.add_rules([tweepy.StreamRule(keyword)])
  
  def on_tweet(self, tweet):
    asyncio.create_task(self.push_to_stream(tweet))
    self.client.on_tweet(tweet)
    self.client.filter(tweet_fields=["created_at", "public_metrics", "author_id", "lang"], rules=[tweepy.StreamRule(keyword)])

  async def push_to_stream(self, tweet):
    message = {
      "id": tweet.id,
      "text": tweet.text,
      "author_id": tweet.author_id,
      "created_at": tweet.created_at.isoformat(),
      "ingested_at": datetime.now(datetime.timezone.utc).isoformat(),
    }

    await self.redis.xadd(name=self.stream_key, fields=message, maxlen=100000)
    logger.info(f"Pushed tweet {tweet.id} to stream")

async def main():
  redis = await Redis.from_url(settings.REDIS_URL)
  stream_connector = TwitterStreamConnector(redis, settings.STREAM_KEYWORDS)
  await stream_connector.start()

if __name__ == "__main__":
  asyncio.run(main())