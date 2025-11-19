import asyncio
import logging
from pathlib import Path
from typing import List, Optional

from redis import Redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from tweetpulse.core.config import get_settings
from .connector import TwitterStreamConnector
from .consumer import StreamConsumer
from .batch_writer import BatchWriter
from .deduplication import BloomDeduplicator
from .enrichment_factory import create_enricher, get_enricher_info
from .storage import Storage

logger = logging.getLogger(__name__)
settings = get_settings()

class IngestionPipeline:
  def __init__(
    self,
    keywords: List[str],
    staging_dir: Path,
    num_workers: int = 3,
    redis_client: Optional[Redis] = None,
    database_url: Optional[str] = None
  ):
    self.keywords = keywords
    self.staging_dir = Path(staging_dir)
    self.num_workers = num_workers
    self.is_running = False
    self.tasks = []

    self.redis = redis_client or Redis.from_url(settings.REDIS_URL)
    self.database_url = database_url or settings.DATABASE_URL

    self.connector = TwitterStreamConnector(
      redis=self.redis,
      keywords=self.keywords,
      stream_key="ingest:stream"
    )

    # Initialize processing components
    self.deduplicator = BloomDeduplicator(redis=self.redis, key="dedup:bloom")
    
    # Create enricher based on environment (auto-selects lite for dev, full for prod)
    self.enricher = create_enricher()
    
    # Log which enricher is being used
    enricher_info = get_enricher_info()
    logger.info(f"🔧 Using {enricher_info['version'].upper()} enricher: {enricher_info['model']} ({enricher_info['reason']})")
    
    self.storage = Storage(
      redis=self.redis,
      staging_dir=self.staging_dir
    )

  def get_session(self) -> Session:
    engine = create_engine(self.database_url)
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
      logger.debug(f"Tweet {tweet_id} added to batch")
    else:
      logger.warning(f"batch_writer not available for tweet {tweet_id}")

    logger.info(f"Processed tweet: {tweet_id}")

  async def start(self):
    if self.is_running:
      logger.info("Pipeline is already running")
      return

    self.is_running = True
    logger.info("Starting ingestion pipeline")

    # Start connector (synchronous, just initializes)
    self.connector.start()

    # Initialize batch writer BEFORE consumers (so it's available in process_tweet)
    self.batch_writer = BatchWriter(
      session_factory=self.get_session,
      staging_dir=self.staging_dir,
      batch_size=settings.BATCH_SIZE,
      max_wait_seconds=settings.MAX_BATCH_WAIT_SECONDS,
      max_retries=3,
      redis_client=self.redis
    )

    writer_task = asyncio.create_task(self.batch_writer.run_forever())
    self.tasks.append(writer_task)

    # Start consumers (they will use batch_writer in process_tweet)
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

    # Clean up any stale distributed locks
    try:
      from ..core.distributed.locking import DistributedLockManager
      lock_manager = DistributedLockManager(self.redis)
      await lock_manager.cleanup_stale_locks()
      logger.info("Cleaned up stale distributed locks")
    except Exception as e:
      logger.warning(f"Failed to cleanup distributed locks: {e}")

    logger.info("Pipeline stopped")