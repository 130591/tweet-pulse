import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

import pyarrow as pa
import pyarrow.parquet as pq
from redis import Redis

logger = logging.getLogger(__name__)
TWENTY_FOUR_HOURS = 86400

class Storage:
  def __init__(
    self, 
    redis: Redis, 
    staging_dir: Path,
    cache_ttl: int = TWENTY_FOUR_HOURS,
    buffer_limit: int = 1000
  ):
    self.redis = redis
    self.staging_dir = Path(staging_dir)
    self.cache_ttl = cache_ttl
    self.buffer_limit = buffer_limit
    
    self.staging_buffer: List[dict] = []
    self.buffer_lock = asyncio.Lock()
    
    self.stats = {
      "cached_tweets": 0,
      "staged_tweets": 0,
      "flushes": 0
    }

  async def store(self, enriched_tweet: Dict) -> None:
    tweet_id = enriched_tweet.get('id')
    if not tweet_id:
      raise ValueError("Tweet must have 'id' field")
    
    await asyncio.gather(
      self._cache_in_redis(enriched_tweet),
      self.append_to_staging(enriched_tweet),
      return_exceptions=True
    )
  
  async def _cache_in_redis(self, tweet: Dict) -> None:
    tweet_id = tweet['id']
    sentiment = tweet.get('sentiment', 'unknown')

    pipe = self.redis.pipeline()

    tweet_hash = {
      k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
      for k, v in tweet.items()
    }

    pipe.hset(f"tweet:{tweet_id}", mapping=tweet_hash)
    pipe.expire(f"tweet:{tweet_id}", self.cache_ttl)

    pipe.lpush("tweets:recent", tweet_id)
    pipe.ltrim("tweets:recent", 0, 999)

    if sentiment:
      pipe.sadd(f"tweets:by_sentiment:{sentiment}", tweet_id)
      pipe.expire(f"tweets:by_sentiment:{sentiment}", self.cache_ttl)
    
    pipe.incr("stats:cached_tweets")
    await pipe.execute()
    
    self.stats['cached_tweets'] += 1

  async def append_to_staging(self, tweet: Dict) -> None:
    async with self.buffer_lock:
      self.staging_buffer.append(tweet)
      if len(self.staging_buffer) >= self.buffer_limit:
        await self.flush_staging_buffer()
  
  async def flush_staging_buffer(self) -> None:
    if not self.staging_buffer:
      return
    
    self.staging_dir.mkdir(parents=True, exist_ok=True)
    timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"tweets_{timestamp_str}.parquet"
    filepath = self.staging_dir / filename

    try:
      table = pa.Table.from_pylist(self.staging_buffer)
      pq.write_table(
        table, 
        filepath, 
        compression='snappy', 
        use_dictionary=True
      )
      logger.info(f"Flushed {len(self.staging_buffer)} tweets to {filepath}")

      self.stats['staged_tweets'] += len(self.staging_buffer)
      self.stats['flushes'] += 1

      self.staging_buffer = []
      
    except Exception as e:
      logger.error(f"Failed to flush staging buffer: {e}")
      raise

  async def flush(self) -> None:
    async with self.buffer_lock:
      if self.staging_buffer:
        await self.flush_staging_buffer()
  
  async def get_from_cache(self, tweet_id: str) -> Optional[Dict]:
    tweet_hash = await self.redis.hgetall(f"tweet:{tweet_id}")
    
    if not tweet_hash:
      return None
    
    tweet = {}
    for key, value in tweet_hash.items():
      try:
        tweet[key] = json.loads(value)
      except (json.JSONDecodeError, TypeError):
        tweet[key] = value
    
    return tweet
  
  async def get_recent_tweets(self, limit: int = 1000) -> List[Dict]:
    tweet_ids = await self.redis.lrange("tweets:recent", 0, limit - 1)
    if not tweet_ids:
      return []
    
    tweets = await asyncio.gather(
      *[
        self.get_from_cache(tweet_id)
        for tweet_id in tweet_ids
      ]
    )
    
    return [t for t in tweets if t is not None]
  
  async def get_by_sentiment(self, sentiment: str, limit: int = 1000) -> List[Dict]:
    tweet_ids = await self.redis.srandmember(f"tweets:by_sentiment:{sentiment}", limit)
    
    if not tweet_ids:
      return []
    
    tweets = await asyncio.gather(
      *[
        self.get_from_cache(tweet_id)
        for tweet_id in tweet_ids
      ]
    )
    
    return [t for t in tweets if t is not None]


  async def get_stats(self) -> Dict:
    staging_files = list(self.staging_dir.glob("*.parquet"))
    cached_total = await self.redis.get("stats:cached_tweets")

    return {
      "cached_tweets": int(cached_total) if cached_total else 0,
      "staged_tweets": self.stats['staged_tweets'],
      "flushes": self.stats['flushes'],
      "buffer_size": len(self.staging_buffer),
      "staging_files": len(staging_files)
    }

  async def cleanup_old_files(self, days: int = 7) -> int:
    from datetime import timedelta
    
    cutoff_date = datetime.now() - timedelta(days=days)
    removed = 0

    for filepath in self.staging_dir.glob("*.parquet"):
      try:
        timestamp_str = filepath.stem.split("_", 1)[1]
        file_date = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")

        if file_date < cutoff_date:
          filepath.unlink()
          removed += 1
          logger.info(f"Removed old file: {filepath}")

      except (ValueError, IndexError):
        continue

    return removed

  async def close(self) -> None:
    logger.info("Closing Tweet Storage")

    await self.flush()
    logger.info(f"Final stats: {await self.get_stats()}")

      