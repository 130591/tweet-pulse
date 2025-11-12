import asyncio
import logging
import os

from tweetpulse.workers import TweetProcessorWorker, BatchProcessorWorker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
  worker_type = os.getenv("WORKER_TYPE", "processor")
  worker_id = os.getenv("WORKER_ID", f"{worker_type}_1")

  if worker_type == "batch":
    batch_size = int(os.getenv("BATCH_SIZE", "100"))
    batch_timeout = float(os.getenv("BATCH_TIMEOUT", "10.0"))

    worker = BatchProcessorWorker(
        worker_id=worker_id,
        batch_size=batch_size,
        batch_timeout=batch_timeout
    )
  else:
    worker = TweetProcessorWorker(worker_id=worker_id)

  try:
    await worker.start()
  except KeyboardInterrupt:
    logger.info(f"Stopping {worker_id}")
    await worker.stop()


if __name__ == "__main__":
  asyncio.run(main())
