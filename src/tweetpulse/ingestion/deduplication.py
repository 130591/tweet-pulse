import logging
from redis import Redis
from redis.asyncio import Redis as AsyncRedis

logger = logging.getLogger(__name__)

class BloomDeduplicator:
    def __init__(self, redis: Redis, key: str):
      self.redis = redis
      self.bloom_key = "dedup:bloom"

    async def is_duplicate(self, tweet_id: str) -> bool:
      exists = await self.redis.bf().exists(self.bloom_key, tweet_id)
      if not exists:
        await self.redis.bf().add(self.bloom_key, tweet_id)
        return False

      is_dup = await self.redis.sismember(self.bloom_key, tweet_id)
      
      if not is_dup:
        await self.redis.sadd("dedup:seen", tweet_id)
        await self.redis.bf().add(self.bloom_key, tweet_id)
      return is_dup

async def process_tweet(fields):
  deduplicator = BloomDeduplicator(redis, "dedup:bloom")
  is_dup = await deduplicator.is_duplicate(fields["id"])
  if not is_dup:
    await redis.xadd("ingest:stream", fields)