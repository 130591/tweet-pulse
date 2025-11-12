import asyncio
import signal
import logging
from pathlib import Path
from typing import Optional, Any

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from tweetpulse.core.config import settings
from tweetpulse.models.database import Base
from tweetpulse.ingestion.pipeline import IngestionPipeline

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("tweetpulse.worker")

engine = create_async_engine(settings.DATABASE_URL)
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False)

pipeline: Optional[IngestionPipeline] = None
shutdown_event = asyncio.Event()


async def init_db() -> AsyncSession:
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
  return async_session()


async def close_db() -> None:
  await engine.dispose()


def signal_handler(signum, frame):
  logger.info(f"\nReceived signal {signum}, shutting down...")
  shutdown_event.set()


async def main():
  """Main loop do worker"""
  global pipeline

  # Setup signal handlers
  signal.signal(signal.SIGTERM, signal_handler)
  signal.signal(signal.SIGINT, signal_handler)

  logger.info("=" * 80)
  logger.info("Starting TweetPulse Ingestion Worker")
  logger.info("=" * 80)

  db = None
  pipeline_task = None

  try:
    db = await init_db()
    logger.info("✓ Database initialized")

    pipeline = IngestionPipeline(
        keywords=settings.TWITTER_KEYWORDS.split(","),
        staging_dir=Path(settings.STAGING_DIR),
        num_workers=settings.NUM_WORKERS,
    )

    logger.info(f"✓ Pipeline configured:")
    logger.info(f"  - Keywords: {settings.TWITTER_KEYWORDS}")
    logger.info(f"  - Workers: {settings.NUM_WORKERS}")
    logger.info(f"  - Staging: {settings.STAGING_DIR}")
    logger.info("=" * 80)

    pipeline_task = asyncio.create_task(pipeline.start())

    await shutdown_event.wait()

    logger.info("\nInitiating graceful shutdown...")

    if pipeline:
      await pipeline.stop()

    if pipeline_task:
      await asyncio.wait_for(pipeline_task, timeout=30)

  except asyncio.TimeoutError:
    logger.error("Pipeline shutdown timed out, forcing...")
    if pipeline_task:
      pipeline_task.cancel()

  except Exception as e:
    logger.error(f"Error in worker: {e}", exc_info=True)
    raise

  finally:
    if db:
      await db.close()
    await close_db()
    logger.info("✓ Worker shutdown complete")

if __name__ == "__main__":
  asyncio.run(main())
