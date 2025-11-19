import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
from pydantic import BaseModel

from tweetpulse.repositories.tweet_repository import TweetRepository
from tweetpulse.ingestion.deduplication import BloomDeduplicator
from tweetpulse.ingestion.enrichment_lite import TweetEnricher
from tweetpulse.core.dependencies import get_redis_client, get_elasticsearch_client, get_db_session_factory

logger = logging.getLogger(__name__)


class TweetCreate(BaseModel):
  id: str
  text: str
  author_id: str
  created_at: datetime
  retweet_count: int = 0
  like_count: int = 0
  reply_count: int = 0
  quote_count: int = 0
  bookmark_count: int = 0
  impression_count: int = 0
  sentiment: str | None = None
  confidence: float | None = None
  
  class Config:
      extra = "allow"
  
  def to_db_dict(self) -> Dict[str, Any]:
    """Convert to database format (text -> content, filter extra fields)"""
    data = self.model_dump(exclude={'text'})
    data['content'] = self.text
    # Remove fields not in database schema
    data.pop('source', None)
    data.pop('ingested_at', None)
    data.pop('lang', None)
    return data


class TweetProcessorWorker:
  def __init__(self, worker_id: str = "worker_1"):
    self.worker_id = worker_id
    self.is_running = False
    self.redis = get_redis_client()
    self.elasticsearch = get_elasticsearch_client()
    self.db_factory = get_db_session_factory()
    self.dedup_service = BloomDeduplicator(self.redis, "dedup:bloom")
    self.enrichment_service = TweetEnricher()

  async def process_tweet(self, data: Dict[str, Any]) -> bool:
    tweet_id = data.get("id")

    if await self.dedup_service.is_duplicate(tweet_id):
      return False

    tweet = TweetCreate(**data)

    enriched_data = await self.enrichment_service.enrich(tweet.model_dump())
    enriched = TweetCreate(**enriched_data)

    async with self.db_factory() as session:
      repo = TweetRepository(session)
      await repo.upsert(enriched)

    await self.elasticsearch.index(
      index="tweets",
      id=tweet_id,
      body=enriched.model_dump()
    )

    return True

  async def start(self):
    self.is_running = True
    logger.info(f"Worker {self.worker_id} started")
    
    while self.is_running:
        try:
            messages = await self.redis.xreadgroup(
              groupname="workers",
              consumername=self.worker_id,
              streams={"ingest:stream": ">"},
              count=1,
              block=5000
            )
            
            if not messages:
              continue
                    
            for stream in messages:
              stream_name = stream[0]
              stream_messages = stream[1]
              for message in stream_messages:
                  message_id = message[0]
                  message_data = message[1]
                  await self.process_tweet(message_data)
                        
        except Exception as e:
            logger.exception(f"Error processing message: {e}")

  async def stop(self):
    self.is_running = False


class BatchProcessorWorker:
  def __init__(
      self,
      worker_id: str = "batch_worker_1",
      batch_size: int = 100,
      batch_timeout: float = 10.0
  ):
    self.worker_id = worker_id
    self.batch_size = batch_size
    self.batch_timeout = batch_timeout
    self.is_running = False
    self.buffer = []
    self.last_flush = asyncio.get_event_loop().time()

    self.redis = get_redis_client()
    self.elasticsearch = get_elasticsearch_client()
    self.db_factory = get_db_session_factory()

  async def start(self):
    self.is_running = True
    logger.info(f"Batch worker {self.worker_id} started")

    flush_task = asyncio.create_task(self._periodic_flush())

    try:
      while self.is_running:
        messages = await self.redis.xreadgroup(
          groupname="batch_workers",
          consumername=self.worker_id,
          streams={"ingest:stream": ">"},
          count=self.batch_size,
          block=1000
        )

        if messages:
          for stream_name, stream_messages in messages:
            for message in stream_messages:
              message_id = message[0]
              message_data = message[1]
              self.buffer.append((message_id, message_data))

            if len(self.buffer) >= self.batch_size:
              await self._flush()

    except KeyboardInterrupt:
      logger.info(f"Batch worker {self.worker_id} interrupted")
    finally:
      flush_task.cancel()
      await self._flush()
      self.is_running = False
      logger.info(f"Batch worker {self.worker_id} stopped")

  async def _flush(self):
    if not self.buffer:
      return

    try:
      tweets = []
      message_ids = []

      for message_id, data in self.buffer:
        tweet = TweetCreate(**data)
        tweets.append(tweet)
        message_ids.append(message_id)

      async with self.db_factory() as session:
        repo = TweetRepository(session)
        await repo.upsert_many([tweet.model_dump() for tweet in tweets])

      operations = []
      for tweet in tweets:
        operations.append({"index": {"_index": "tweets", "_id": tweet.id}})
        operations.append(tweet.model_dump())

      if operations:
        await self.elasticsearch.bulk(body=operations)

      for message_id in message_ids:
        await self.redis.xack("ingest:stream", "batch_workers", message_id)

      logger.info(f"Flushed {len(self.buffer)} tweets")
      self.buffer = []
      self.last_flush = asyncio.get_event_loop().time()

    except Exception as e:
      logger.error(f"Error flushing batch: {e}")
      self.buffer = []

  async def _periodic_flush(self):
    while self.is_running:
      await asyncio.sleep(self.batch_timeout)

      current_time = asyncio.get_event_loop().time()
      if current_time - self.last_flush >= self.batch_timeout and self.buffer:
        await self._flush()

  async def stop(self):
    self.is_running = False
    await self._flush()
