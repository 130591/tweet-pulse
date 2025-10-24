import asyncio
import logging
from pathlib import Path
from typing import List

from redis import Redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from tweetpulse.core.config import get_settings
from .connector import TwitterStreamConnector
from .consumer import StreamConsumer
from .batch_writer import BatchWriter
from .deduplication import BloomDeduplicator
from .enrichment import TweetEnricher
from .storage import Storage

logger = logging.getLogger(__name__)
settings = get_settings()

class IngestionPipeline:
  def __init__(
      self,
      keywords: List[str],
      staging_dir: Path,
      num_workers: int = 3
  ):
    self.keywords = keywords
    self.staging_dir = Path(staging_dir)
    self.num_workers = num_workers
    self.is_running = False
    self.tasks = []

    # Initialize components
    self.redis = Redis.from_url(settings.REDIS_URL)
    self.connector = TwitterStreamConnector(
      redis=self.redis,
      keywords=self.keywords,
      stream_key="ingest:stream"
    )
    
    # Initialize processing components
    self.deduplicator = BloomDeduplicator(redis=self.redis, key="dedup:bloom")
    self.enricher = TweetEnricher()
    self.storage = Storage(
      redis=self.redis,
      staging_dir=self.staging_dir
    )

  def get_session(self) -> Session:
    """Get a synchronous database session."""
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()

  async def process_tweet(self, fields: dict):
    """Process a single tweet through the pipeline."""
    tweet_id = fields.get('id')

    if await self.deduplicator.is_duplicate(tweet_id):
      logger.debug(f"Duplicate tweet: {tweet_id}")
      return
    
    # Enrich the tweet with additional processing
    enriched = await self.enricher.enrich(fields)
    
    # Store in staging (Redis/filesystem)
    await self.storage.store(enriched)
    
    # Add to batch for database write
    if hasattr(self, 'batch_writer'):
      await self.batch_writer.add_tweet(enriched)

    logger.info(f"Processed tweet: {tweet_id}")

  async def start(self):
    if self.is_running:
      logger.info("Pipeline is already running")
      return

    self.is_running = True
    logger.info("Starting ingestion pipeline")

    # Start connector
    connector_task = asyncio.create_task(self.connector.start())
    self.tasks.append(connector_task)

    # Start consumers
    for i in range(self.num_workers):
      consumer = StreamConsumer(
        redis=self.redis,
        stream_key="ingest:stream",
        group_name="workers",
        consumer_name=f"worker-{i}",
        processor=self.process_tweet
      )
      consumer_task = asyncio.create_task(consumer.start())
      self.tasks.append(consumer_task)

    # Start batch writer with proper configuration
    self.batch_writer = BatchWriter(
      session_factory=self.get_session,
      staging_dir=self.staging_dir,
      batch_size=settings.BATCH_SIZE,
      max_wait_seconds=settings.MAX_BATCH_WAIT_SECONDS,
      max_retries=3
    )

    writer_task = asyncio.create_task(self.batch_writer.run_forever())
    self.tasks.append(writer_task)

    logger.info("Pipeline started with %d workers", self.num_workers)
    logger.info(f"Monitoring keywords: {self.keywords}")
    logger.info(f"Staging directory: {self.staging_dir}")

  async def stop(self):
    if not self.is_running:
      logger.info("Pipeline is not running")
      return

    self.is_running = False
    logger.info("Stopping ingestion pipeline")

    for task in self.tasks:
      task.cancel()

    await asyncio.gather(*self.tasks, return_exceptions=True)

    if hasattr(self, 'connector'):
      self.connector.close()
    if hasattr(self, 'batch_writer'):
      self.batch_writer.stop()
      # Wait for final flush
      await self.batch_writer.flush()

    logger.info("Pipeline stopped")