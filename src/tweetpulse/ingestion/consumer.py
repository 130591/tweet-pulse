import logging
from typing import Callable
from redis import Redis
import asyncio
from tweetpulse.core.config import get_settings

settings = get_settings()

class StreamConsumer:
  def __init__(
    self, redis: Redis, stream_key: str,
    group_name: str, consumer_name: str,
    processor: Callable
  ):
    self.redis = redis
    self.stream_key = stream_key
    self.group_name = group_name
    self.consumer_name = consumer_name
    self.processor = processor
    self.logger = logging.getLogger(__name__)

  async def start(self):
    try:
      try:
        self.redis.xgroup_create(
          name=self.group_name,
          stream=self.stream_key,
          id="0",
          mkstream=True
        )
      except Exception as e:
        self.logger.error(f"Error creating consumer group: {e}")
        pass

      self.logger.info(f"Consumer {self.consumer_name} started in group {self.group_name}")

      while True:
        messages = self.redis.xreadgroup(
          groupname=self.group_name,
          consumername=self.consumer_name,
          streams={self.stream_key: ">"},
          count=10,
          block=1000
        )

        if not messages:
          await asyncio.sleep(1)
          continue

        for stream, msgs in messages:
          for msg_id, fields in msgs:
            try:
              message_dict = {k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v for k, v in fields.items()}
              await self.processor(message_dict)
              self.redis.xack(self.stream_key, self.group_name, msg_id)
            except Exception as e:
              self.logger.error(f"Error processing message: {e}")

    except asyncio.CancelledError:
      self.logger.info(f"Consumer {self.consumer_name} stopped")
    except Exception as e:
      self.logger.error(f"Consumer {self.consumer_name} error: {e}")

async def main():
  logger = logging.getLogger(__name__)
  redis = Redis.from_url(settings.REDIS_URL)

  async def process_tweet(fields):
    logger.info(f"Processing tweet: {fields}")

  consumers = [
    StreamConsumer(redis, 'ingest:stream', "workers", f"worker-{i}", process_tweet)
    for i in range(4)
  ]

  await asyncio.gather(*[c.start() for c in consumers])