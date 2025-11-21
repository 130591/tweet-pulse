import asyncio
import logging
import time
from pathlib import Path
from typing import Callable, List, Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from redis.asyncio import Redis

from ..repositories.tweet_repository import TweetRepository
from ..models.tweet import Tweet
from ..models.database import SentimentType
from ..core.config import get_settings
from ..core.distributed.locking import RedisLock

logger = logging.getLogger(__name__)
settings = get_settings()

class BatchWriter:
  """Thread-safe batch writer for efficient database writes.

  Implements best practices for distributed systems:
  - Configurable batch size
  - Automatic flush on batch size or timeout
  - Thread-safe operations with asyncio.Lock
  - Distributed locking for multi-instance safety
  - Retry logic with exponential backoff
  - Proper error handling and metrics
  """

  def __init__(
    self,
    session_factory: Callable[[], Session],
    staging_dir: Path,
    batch_size: int = 100,
    max_wait_seconds: int = 60,
    max_retries: int = 3,
    redis_client: Optional[Redis] = None
  ):
    self.session_factory = session_factory
    self.staging_dir = staging_dir
    self.batch_size = batch_size
    self.max_wait_seconds = max_wait_seconds
    self.max_retries = max_retries
    self.redis = redis_client

    self.is_running = False
    self.batch: List[Dict[str, Any]] = []
    self._lock = asyncio.Lock()
    self._last_flush_time = time.time()

    # Metrics
    self.total_processed = 0
    self.total_failed = 0
    self.total_batches_written = 0

  @contextmanager
  def get_session_with_repo(self):
    """Context manager for database session with repository."""
    session = None
    try:
      session = self.session_factory()
      repo = TweetRepository(session)
      yield session, repo
    finally:
      if session:
        session.close()
  
  async def run_forever(self):
    """Run the batch writer continuously with timeout-based flushing."""
    self.is_running = True
    logger.info(f"BatchWriter started: batch_size={self.batch_size}, max_wait={self.max_wait_seconds}s")
    
    while self.is_running:
      try:
        # Calculate time until next flush
        time_since_last_flush = time.time() - self._last_flush_time
        time_until_flush = max(0, self.max_wait_seconds - time_since_last_flush)
        
        # Wait with timeout
        await asyncio.sleep(min(1, time_until_flush))  # Check every second
        
        # Check if we should flush
        async with self._lock:
          should_flush = (
            len(self.batch) >= self.batch_size or
            (len(self.batch) > 0 and time.time() - self._last_flush_time >= self.max_wait_seconds)
          )
        
        if should_flush:
          await self.flush()
      
      except asyncio.CancelledError:
        # Final flush before stopping
        if self.batch:
          logger.info("Performing final flush before shutdown")
          await self.flush()
        logger.info(f"BatchWriter stopped. Total processed: {self.total_processed}, Failed: {self.total_failed}")
        break
      except Exception as e:
        logger.error(f"Unexpected error in batch writer: {e}", exc_info=True)

  async def flush(self) -> bool:
    """Flush the current batch to the database with retry logic and distributed locking."""
    async with self._lock:
      if not self.batch:
        return True

      # Take a copy and clear the batch
      tweets_to_save = self.batch.copy()
      self.batch = []
      batch_size = len(tweets_to_save)

    lock_key = f"batch_writer_flush:{self.batch_size}"
    distributed_lock = RedisLock(self.redis, lock_key, timeout_seconds=30)

    try:
      lock_acquired = await distributed_lock.acquire()
      if not lock_acquired:
        logger.warning(f"Failed to acquire distributed lock for batch flush, retrying...")
        # Put tweets back in batch for next flush attempt
        async with self._lock:
          self.batch = tweets_to_save + self.batch
          self.total_failed += batch_size
        return False

      logger.debug(f"Distributed lock acquired for batch flush: {batch_size} tweets")

      for attempt in range(self.max_retries):
        try:
          success = await self._write_batch_to_db(tweets_to_save)
          if success:
            self.total_processed += batch_size
            self.total_batches_written += 1
            self._last_flush_time = time.time()
            logger.info(
              f"Successfully flushed batch: size={batch_size}, "
              f"total_processed={self.total_processed}, "
              f"batches_written={self.total_batches_written}"
            )
            return True
        except Exception as e:
          logger.error(
            f"Attempt {attempt + 1}/{self.max_retries} failed for batch of {batch_size}: {e}"
          )
          if attempt < self.max_retries - 1:
            await asyncio.sleep(2 ** attempt)

            if attempt >= 1:
              await distributed_lock.extend(additional_seconds=15)

      logger.error(f"Failed to write batch after {self.max_retries} attempts")
      async with self._lock:
        self.batch = tweets_to_save + self.batch
        self.total_failed += batch_size
      return False

    finally:
      await distributed_lock.release()
  
  async def _write_batch_to_db(self, tweets: List[Dict[str, Any]]) -> bool:
    loop = asyncio.get_event_loop()
    
    def blocking_db_write():
      with self.get_session_with_repo() as (session, repo):
        try:
          records = []
          for tweet_data in tweets:
            record = {
              'id': tweet_data.get('id'),
              'content': tweet_data.get('text', '')[:280],  # Truncate to 280 chars
              'author_id': tweet_data.get('author_id'),
              'created_at': self._parse_timestamp(tweet_data.get('created_at')),
              'retweet_count': tweet_data.get('public_metrics', {}).get('retweet_count', 0),
              'like_count': tweet_data.get('public_metrics', {}).get('like_count', 0),
              'reply_count': tweet_data.get('public_metrics', {}).get('reply_count', 0),
              'quote_count': tweet_data.get('public_metrics', {}).get('quote_count', 0),
              'bookmark_count': tweet_data.get('public_metrics', {}).get('bookmark_count', 0),
              'impression_count': tweet_data.get('public_metrics', {}).get('impression_count', 0),
            }
            
            # Add sentiment if available
            if 'sentiment' in tweet_data:
              record['sentiment'] = SentimentType(tweet_data['sentiment'])
              record['confidence'] = tweet_data.get('confidence')
            
            records.append(record)
          
          # Use upsert to handle duplicates gracefully
          affected_rows = repo.upsert_many(records, conflict_fields=['id'])
          logger.debug(f"Database upsert affected {affected_rows} rows for {len(records)} records")
          return True
          
        except SQLAlchemyError as e:
          logger.error(f"Database error during batch write: {e}")
          session.rollback()
          raise
        except Exception as e:
          logger.error(f"Unexpected error during batch write: {e}")
          session.rollback()
          raise
    
    # Run database write in thread pool to avoid blocking
    return await loop.run_in_executor(None, blocking_db_write)
  
  def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
    """Parse Twitter timestamp to datetime."""
    if not timestamp_str:
      return None
    try:
      # Twitter uses ISO 8601 format
      return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
      logger.warning(f"Failed to parse timestamp: {timestamp_str}")
      return None

  async def add_tweet(self, tweet_data: Dict[str, Any]) -> None:
    """Add a tweet to the batch. Triggers flush if batch is full."""
    async with self._lock:
      self.batch.append(tweet_data)
      batch_full = len(self.batch) >= self.batch_size
    
    # Trigger flush if batch is full (without holding the lock)
    if batch_full:
      logger.debug(f"Batch size {self.batch_size} reached, triggering flush")
      asyncio.create_task(self.flush())

  def stop(self) -> None:
    """Stop the batch writer."""
    self.is_running = False
  
  async def get_metrics(self) -> Dict[str, Any]:
    """Get current metrics."""
    async with self._lock:
      current_batch_size = len(self.batch)
    
    return {
      'total_processed': self.total_processed,
      'total_failed': self.total_failed,
      'total_batches_written': self.total_batches_written,
      'current_batch_size': current_batch_size,
      'batch_size_limit': self.batch_size,
      'max_wait_seconds': self.max_wait_seconds,
      'time_since_last_flush': time.time() - self._last_flush_time
    }
