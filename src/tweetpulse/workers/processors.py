import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from .models.tweet import Tweet, TweetCreate
from .repositories.tweet_repository import TweetRepository
from .ingestion.deduplication import DeduplicationService
from .ingestion.enrichment_lite import LiteEnrichmentService
from .core.dependencies import get_redis_client, get_elasticsearch_client, get_db_session_factory

logger = logging.getLogger(__name__)


class TweetProcessorWorker:
    def __init__(self, worker_id: str = "worker_1"):
      self.worker_id = worker_id
      self.is_running = False
      self.redis = get_redis_client()
      self.elasticsearch = get_elasticsearch_client()
      self.db_factory = get_db_session_factory()
      self.dedup_service = DeduplicationService(self.redis)
      self.enrichment_service = LiteEnrichmentService()
    
    async def process_tweet(self, data: Dict[str, Any]) -> bool:
      tweet_id = data.get("id")
      
      if await self.dedup_service.is_duplicate(tweet_id):
        return False
      
      tweet = TweetCreate(
        id=tweet_id,
        text=data.get("text"),
        author_id=data.get("author_id"),
        created_at=data.get("created_at"),
        **data
      )
      
      enriched = await self.enrichment_service.enrich_tweet(tweet)
      
      async with self.db_factory() as session:
        repo = TweetRepository(session)
        await repo.upsert(enriched)
      
      await self.elasticsearch.index(
        index="tweets",
        id=tweet_id,
        body=enriched.model_dump()
      )
      
      await self.dedup_service.mark_as_seen(tweet_id)
      
      return True
    
    async def start(self):
        self.is_running = True
        logger.info(f"Worker {self.worker_id} started")
        
        try:
            while self.is_running:
                messages = await self.redis.xreadgroup(
                    groupname="workers",
                    consumername=self.worker_id,
                    streams={"ingest:stream": ">"},
                    count=10,
                    block=1000
                )
                
                if messages:
                    for stream_name, stream_messages in messages.items():
                        for message_id, data in stream_messages:
                            try:
                                await self.process_tweet(data)
                                await self.redis.xack("ingest:stream", "workers", message_id)
                            except Exception as e:
                                logger.error(f"Error processing tweet: {e}")
        
        except KeyboardInterrupt:
            logger.info(f"Worker {self.worker_id} interrupted")
        finally:
            self.is_running = False
            logger.info(f"Worker {self.worker_id} stopped")
    
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
                    for stream_name, stream_messages in messages.items():
                        for message_id, data in stream_messages:
                            self.buffer.append((message_id, data))
                            
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
                tweet = TweetCreate(
                    id=data.get("id"),
                    text=data.get("text"),
                    author_id=data.get("author_id"),
                    created_at=data.get("created_at"),
                    **data
                )
                tweets.append(tweet)
                message_ids.append(message_id)
            
            async with self.db_factory() as session:
                repo = TweetRepository(session)
                await repo.upsert_many([t.model_dump() for t in tweets])
            
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
