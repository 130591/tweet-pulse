import asyncio
import logging
import os
from pathlib import Path
from typing import Callable, List
from datetime import datetime

logger = logging.getLogger(__name__)

class BatchWriter:
  def __init__(
    self,
    session_factory: Callable,
    staging_dir: Path,
    interval_seconds: int = 300
  ):
    self.session_factory = session_factory
    self.staging_dir = staging_dir
    self.interval_seconds = interval_seconds
    self.is_running = False
    self.batch: List[dict] = []

  async def run_forever(self):
    """Run the batch writer continuously."""
    self.is_running = True

    while self.is_running:
      try:
        await asyncio.sleep(self.interval_seconds)

        if self.batch:
          await self.flush()
      except asyncio.CancelledError:
        logger.info("BatchWriter stopped")
        break
      except Exception as e:
        logger.error(f"Error in batch writer: {e}")

  async def flush(self):
    """Write the current batch to the database."""
    if not self.batch:
      return

    tweets_to_save = self.batch.copy()
    self.batch = []

    try:
      session = self.session_factory()

      for tweet_data in tweets_to_save:
        # Here you would save to your Tweet model
        # Example:
        # tweet = Tweet(**tweet_data)
        # session.add(tweet)
        logger.info(f"Would save tweet: {tweet_data.get('id', 'unknown')}")

      # session.commit()
      logger.info(f"Flushed {len(tweets_to_save)} tweets to database")

    except Exception as e:
      logger.error(f"Error saving batch to database: {e}")
      # Put the batch back if saving failed
      self.batch.extend(tweets_to_save)
    finally:
      if 'session' in locals():
        session.close()

  def add_tweet(self, tweet_data: dict):
    self.batch.append(tweet_data)

    if len(self.batch) >= 1000:
      logger.info("Batch size limit reached, consider flushing")

  def stop(self):
    self.is_running = False
