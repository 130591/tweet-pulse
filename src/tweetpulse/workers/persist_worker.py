"""
PersistWorker - Persists tweets to PostgreSQL with aggregations
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from tweetpulse.ingestion.consumer import StreamConsumer
from tweetpulse.ingestion.deduplication import DeduplicationService
from tweetpulse.ingestion.batch_writer import BatchWriter
from tweetpulse.repositories.tweet_repository import TweetRepository
from tweetpulse.models.tweet import TweetCreate, Tweet
from tweetpulse.models.database import get_engine
from tweetpulse.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PersistWorker:
    """Worker that persists tweets to PostgreSQL with aggregations"""
    
    def __init__(
        self,
        redis: Redis,
        worker_id: str = "persist_worker_1",
        batch_size: int = 100,
        batch_timeout: float = 10.0,
        enable_aggregations: bool = True
    ):
        self.redis = redis
        self.worker_id = worker_id
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.enable_aggregations = enable_aggregations
        
        # Database
        self.engine = None
        self.async_session = None
        self.batch_writer = None
        
        # Services
        self.dedup_service = DeduplicationService(redis)
        
        # Metrics
        self.total_persisted = 0
        self.total_failed = 0
        
        # Aggregation buffer
        self.aggregation_buffer = defaultdict(lambda: {
            "total_tweets": 0,
            "total_reach": 0,
            "sentiment_counts": {"positive": 0, "negative": 0, "neutral": 0},
            "entities": defaultdict(int),
            "keywords": defaultdict(int)
        })
        self.last_aggregation_flush = datetime.utcnow()
        
    async def initialize(self):
        """Initialize database connections and services"""
        # Create engine and session
        self.engine = await get_engine()
        AsyncSessionLocal = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        self.async_session = AsyncSessionLocal
        
        # Initialize batch writer
        self.batch_writer = BatchWriter(
            redis=self.redis,
            batch_size=self.batch_size,
            max_batch_wait_seconds=self.batch_timeout
        )
        await self.batch_writer.start()
        
        logger.info(f"PersistWorker {self.worker_id} initialized")
    
    async def process_tweet(self, message_id: str, data: Dict[str, Any]) -> bool:
        """Process a single tweet for persistence"""
        try:
            tweet_id = data.get("id")
            
            # Check deduplication
            is_duplicate = await self.dedup_service.is_duplicate(tweet_id)
            if is_duplicate:
                logger.debug(f"Skipping duplicate tweet {tweet_id}")
                return True
            
            # Mark as seen
            await self.dedup_service.mark_as_seen(tweet_id)
            
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
                quote_count=int(data.get("quote_count", 0)),
                
                # Include enrichment data if available
                sentiment_label=data.get("sentiment", {}).get("label"),
                sentiment_score=data.get("sentiment", {}).get("score"),
                entities=data.get("entities", [])
            )
            
            # Add to batch writer
            await self.batch_writer.add_tweet(tweet)
            
            # Update aggregations if enabled
            if self.enable_aggregations:
                await self._update_aggregations(tweet, data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing tweet {data.get('id')}: {e}")
            self.total_failed += 1
            return False
    
    async def _update_aggregations(self, tweet: TweetCreate, data: Dict[str, Any]):
        """Update in-memory aggregations"""
        try:
            # Determine time bucket (hourly)
            created_at = datetime.fromisoformat(tweet.created_at.replace('Z', '+00:00'))
            hour_bucket = created_at.replace(minute=0, second=0, microsecond=0)
            bucket_key = hour_bucket.isoformat()
            
            # Update aggregations
            agg = self.aggregation_buffer[bucket_key]
            agg["total_tweets"] += 1
            agg["total_reach"] += (
                tweet.retweet_count + 
                tweet.reply_count + 
                tweet.like_count + 
                tweet.quote_count
            )
            
            # Sentiment
            sentiment_label = tweet.sentiment_label or "neutral"
            agg["sentiment_counts"][sentiment_label] += 1
            
            # Entities
            for entity in tweet.entities or []:
                entity_key = f"{entity.get('type')}:{entity.get('text')}"
                agg["entities"][entity_key] += 1
            
            # Keywords (hashtags and mentions)
            import re
            hashtags = re.findall(r'#\w+', tweet.text)
            mentions = re.findall(r'@\w+', tweet.text)
            
            for keyword in hashtags + mentions:
                agg["keywords"][keyword.lower()] += 1
                
        except Exception as e:
            logger.error(f"Error updating aggregations: {e}")
    
    async def _flush_aggregations(self):
        """Flush aggregations to database"""
        if not self.aggregation_buffer:
            return
            
        try:
            async with self.async_session() as session:
                # Here you would save aggregations to a dedicated table
                # For now, we'll just log them
                for bucket_key, agg_data in self.aggregation_buffer.items():
                    logger.info(
                        f"Aggregation for {bucket_key}: "
                        f"{agg_data['total_tweets']} tweets, "
                        f"Reach: {agg_data['total_reach']}, "
                        f"Sentiment: {dict(agg_data['sentiment_counts'])}"
                    )
                    
                    # TODO: Save to aggregations table
                    # await self._save_aggregation(session, bucket_key, agg_data)
                
                await session.commit()
            
            # Clear buffer
            self.aggregation_buffer.clear()
            self.last_aggregation_flush = datetime.utcnow()
            logger.info("Flushed aggregations to database")
            
        except Exception as e:
            logger.error(f"Failed to flush aggregations: {e}")
    
    async def _periodic_aggregation_flush(self):
        """Periodically flush aggregations"""
        while True:
            await asyncio.sleep(60)  # Flush every minute
            
            if self.enable_aggregations:
                time_since_flush = datetime.utcnow() - self.last_aggregation_flush
                if time_since_flush > timedelta(minutes=1):
                    await self._flush_aggregations()
    
    async def start(self):
        """Start the PersistWorker"""
        logger.info(f"Starting PersistWorker {self.worker_id}")
        
        # Initialize services
        await self.initialize()
        
        # Create consumer
        consumer = StreamConsumer(
            redis=self.redis,
            stream_key=settings.STREAM_KEY or "ingest:stream",
            group_name="persist_workers",
            consumer_name=self.worker_id,
            processor=self.process_tweet
        )
        
        # Start periodic aggregation flush if enabled
        agg_task = None
        if self.enable_aggregations:
            agg_task = asyncio.create_task(self._periodic_aggregation_flush())
        
        try:
            # Start consuming
            await consumer.start()
            
        except KeyboardInterrupt:
            logger.info("PersistWorker interrupted by user")
        except Exception as e:
            logger.error(f"PersistWorker error: {e}")
            raise
        finally:
            # Stop batch writer
            await self.batch_writer.stop()
            
            # Final aggregation flush
            if self.enable_aggregations:
                await self._flush_aggregations()
                if agg_task:
                    agg_task.cancel()
            
            # Close database
            if self.engine:
                await self.engine.dispose()
            
            # Log metrics
            logger.info(
                f"PersistWorker {self.worker_id} stopped. "
                f"Total persisted: {self.batch_writer.total_processed}, "
                f"Failed: {self.total_failed}"
            )


async def main():
    """Main entry point for PersistWorker"""
    import os
    
    # Get worker ID from environment or use default
    worker_id = os.getenv("WORKER_ID", "persist_worker_1")
    
    # Connect to Redis
    redis = await Redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    # Create and start worker
    worker = PersistWorker(
        redis=redis,
        worker_id=worker_id,
        batch_size=int(os.getenv("BATCH_SIZE", "100")),
        batch_timeout=float(os.getenv("BATCH_TIMEOUT", "10.0")),
        enable_aggregations=os.getenv("ENABLE_AGGREGATIONS", "true").lower() == "true"
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
