"""
ElasticWorker - Indexes tweets into ElasticSearch with real-time analysis
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from redis.asyncio import Redis
from tweetpulse.elasticsearch import get_elastic_client
from tweetpulse.ingestion.consumer import StreamConsumer
from tweetpulse.ingestion.deduplication import DeduplicationService
from tweetpulse.ingestion.enrichment_factory import get_enrichment_service
from tweetpulse.core.config import get_settings
from tweetpulse.models.tweet import TweetCreate

logger = logging.getLogger(__name__)
settings = get_settings()


class ElasticWorker:
    """Worker that indexes tweets into ElasticSearch"""
    
    def __init__(
        self,
        redis: Redis,
        worker_id: str = "elastic_worker_1",
        batch_size: int = 50,
        batch_timeout: float = 5.0
    ):
        self.redis = redis
        self.worker_id = worker_id
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        
        # Services
        self.elastic = get_elastic_client()
        self.dedup_service = DeduplicationService(redis)
        self.enrichment = get_enrichment_service()
        
        # Batch buffer
        self.buffer = []
        self.last_flush = asyncio.get_event_loop().time()
        
        # Metrics
        self.total_indexed = 0
        self.total_failed = 0
        
    async def process_tweet(self, message_id: str, data: Dict[str, Any]) -> bool:
        """Process a single tweet for indexing"""
        try:
            tweet_id = data.get("id")
            
            # Check deduplication
            is_duplicate = await self.dedup_service.is_duplicate(tweet_id)
            if is_duplicate:
                logger.debug(f"Skipping duplicate tweet {tweet_id}")
                return True
            
            # Mark as seen
            await self.dedup_service.mark_as_seen(tweet_id)
            
            # Enrich tweet with analysis
            enriched_tweet = await self._enrich_tweet(data)
            
            # Add to batch buffer
            self.buffer.append(enriched_tweet)
            
            # Check if we should flush
            if len(self.buffer) >= self.batch_size:
                await self._flush_batch()
                
            return True
            
        except Exception as e:
            logger.error(f"Error processing tweet {data.get('id')}: {e}")
            self.total_failed += 1
            return False
    
    async def _enrich_tweet(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich tweet with sentiment analysis and entity extraction"""
        try:
            # Create TweetCreate object
            tweet = TweetCreate(
                id=data.get("id"),
                text=data.get("text"),
                author_id=data.get("author_id"),
                created_at=data.get("created_at"),
                lang=data.get("lang", "en"),
                retweet_count=int(data.get("retweet_count", 0)),
                reply_count=int(data.get("reply_count", 0)),
                like_count=int(data.get("like_count", 0)),
                quote_count=int(data.get("quote_count", 0))
            )
            
            # Enrich with sentiment and entities
            enriched = await self.enrichment.enrich_tweet(tweet)
            
            # Convert to dict for ElasticSearch
            doc = enriched.model_dump()
            
            # Add metadata
            doc["processed_at"] = datetime.utcnow().isoformat()
            doc["worker_id"] = self.worker_id
            doc["source"] = data.get("source", "twitter")
            
            # Extract keywords from text (simple approach)
            keywords = self._extract_keywords(doc["text"])
            doc["keywords"] = keywords
            
            return doc
            
        except Exception as e:
            logger.error(f"Error enriching tweet: {e}")
            # Return basic document if enrichment fails
            return {
                **data,
                "processed_at": datetime.utcnow().isoformat(),
                "worker_id": self.worker_id,
                "enrichment_failed": True
            }
    
    def _extract_keywords(self, text: str) -> list:
        """Extract keywords from tweet text (simple implementation)"""
        # Extract hashtags
        import re
        hashtags = re.findall(r'#\w+', text)
        
        # Extract mentions
        mentions = re.findall(r'@\w+', text)
        
        # Combine and clean
        keywords = [tag.lower() for tag in hashtags + mentions]
        
        return list(set(keywords))  # Remove duplicates
    
    async def _flush_batch(self):
        """Flush batch to ElasticSearch"""
        if not self.buffer:
            return
            
        try:
            # Bulk index to ElasticSearch
            result = await self.elastic.bulk_index_tweets(self.buffer)
            
            # Update metrics
            self.total_indexed += len(self.buffer)
            logger.info(f"Indexed batch of {len(self.buffer)} tweets to ElasticSearch")
            
            # Clear buffer
            self.buffer = []
            self.last_flush = asyncio.get_event_loop().time()
            
        except Exception as e:
            logger.error(f"Failed to flush batch to ElasticSearch: {e}")
            self.total_failed += len(self.buffer)
            self.buffer = []  # Clear anyway to avoid memory issues
    
    async def _periodic_flush(self):
        """Periodically flush batches based on timeout"""
        while True:
            await asyncio.sleep(self.batch_timeout)
            
            current_time = asyncio.get_event_loop().time()
            if current_time - self.last_flush >= self.batch_timeout and self.buffer:
                logger.debug(f"Timeout flush: {len(self.buffer)} tweets")
                await self._flush_batch()
    
    async def start(self):
        """Start the ElasticWorker"""
        logger.info(f"Starting ElasticWorker {self.worker_id}")
        
        # Ensure ElasticSearch indices exist
        await self.elastic.ensure_indices()
        
        # Create consumer
        consumer = StreamConsumer(
            redis=self.redis,
            stream_key=settings.STREAM_KEY or "ingest:stream",
            group_name="elastic_workers",
            consumer_name=self.worker_id,
            processor=self.process_tweet
        )
        
        # Start periodic flush task
        flush_task = asyncio.create_task(self._periodic_flush())
        
        try:
            # Start consuming
            await consumer.start()
            
        except KeyboardInterrupt:
            logger.info("ElasticWorker interrupted by user")
        except Exception as e:
            logger.error(f"ElasticWorker error: {e}")
            raise
        finally:
            # Final flush
            await self._flush_batch()
            
            # Cancel flush task
            flush_task.cancel()
            
            # Close connections
            await self.elastic.close()
            
            # Log metrics
            logger.info(
                f"ElasticWorker {self.worker_id} stopped. "
                f"Total indexed: {self.total_indexed}, Failed: {self.total_failed}"
            )


async def main():
    """Main entry point for ElasticWorker"""
    import os
    
    # Get worker ID from environment or use default
    worker_id = os.getenv("WORKER_ID", "elastic_worker_1")
    
    # Connect to Redis
    redis = await Redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    # Create and start worker
    worker = ElasticWorker(
        redis=redis,
        worker_id=worker_id,
        batch_size=int(os.getenv("BATCH_SIZE", "50")),
        batch_timeout=float(os.getenv("BATCH_TIMEOUT", "5.0"))
    )
    
    try:
        await worker.start()
    finally:
        await redis.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())
