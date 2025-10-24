import asyncio
import signal
import logging
from pathlib import Path

from core.config import get_settings
from database.engine import init_db, close_db
from cache.redis_client import init_cache, close_cache
from ingestion.pipeline import IngestionPipeline

settings = get_settings()
logger = logging.getLogger(__name__)

# Global para signal handling
pipeline: IngestionPipeline = None
shutdown_event = asyncio.Event()

def signal_handler(signum, frame):
  """Handler para SIGTERM/SIGINT"""
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
  
  try:
    await init_db()
    await init_cache()
    logger.info("✓ Infrastructure initialized")
    
    pipeline = IngestionPipeline(
      keywords=settings.TWITTER_KEYWORDS.split(","),
      staging_dir=settings.STAGING_DIR,
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
    await pipeline.stop()
    
    await asyncio.wait_for(pipeline_task, timeout=30)
      
  except asyncio.TimeoutError:
    logger.error("Pipeline shutdown timed out, forcing...")
    pipeline_task.cancel()
      
  except Exception as e:
    logger.error(f"Error in worker: {e}")
    raise
      
  finally:
    await close_db()
    await close_cache()
    logger.info("✓ Worker shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())