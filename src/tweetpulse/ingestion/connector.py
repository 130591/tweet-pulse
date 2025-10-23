import asyncio
import logging
import tweepy
from typing import List
from redis import Redis
from tweetpulse.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class TwitterStreamConnector:
  def __init__(self, redis: Redis, keywords: List[str], stream_key: str):
    self.redis = redis
    self.keywords = keywords
    self.stream_key = stream_key
    self.client = tweepy.StreamingClient(
      bearer_token=settings.TWITTER_BEARER_TOKEN,
      wait_on_rate_limit=True
    )
    self.is_running = False

  def start(self):
    """Start the Twitter stream."""
    self.is_running = True
    logger.info(f"Starting Twitter stream with keywords: {self.keywords}")

    # Add rules for keywords
    for keyword in self.keywords:
      try:
        self.client.add_rules([tweepy.StreamRule(keyword)])
        logger.info(f"Added rule for keyword: {keyword}")
      except Exception as e:
        logger.error(f"Error adding rule for {keyword}: {e}")

    # Set up tweet handler
    self.client.on_tweet = self.on_tweet

    # Start filtering (this would need to be run in a thread or similar)
    # For now, just log that we're ready
    logger.info("Twitter stream connector initialized")

  def on_tweet(self, tweet):
    """Handle incoming tweets."""
    try:
      # Prepare message for Redis stream
      message = {
        "id": str(tweet.id),
        "text": tweet.text,
        "author_id": str(tweet.author_id),
        "created_at": tweet.created_at.isoformat() if tweet.created_at else "",
        "ingested_at": asyncio.get_event_loop().time(),
        "source": "twitter_stream"
      }

      # Add to Redis stream
      self.redis.xadd(self.stream_key, message)

      logger.info(f"Pushed tweet {tweet.id} to stream")

    except Exception as e:
      logger.error(f"Error processing tweet {tweet.id}: {e}")

  def close(self):
    """Close the stream connection."""
    self.is_running = False
    logger.info("Twitter stream connector closed")
