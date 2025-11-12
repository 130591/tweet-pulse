from tweetpulse.ingestion.storage import Storage
from redis.asyncio import Redis
from pathlib import Path


async def create_storage(
    redis_url: str,
    staging_dir: Path,
    **kwargs
) -> Storage:
  """
  Factory function to create Storage.

  Args:
      redis_url: Redis connection URL
      staging_dir: Directory for staging files
      **kwargs: Additional arguments for Storage

  Returns:
      Storage instance

  Example:
      storage = await create_storage(
          redis_url="redis://localhost:6379",
          staging_dir=Path("./staging"),
          buffer_limit=500,
      )
  """

  redis = await Redis.from_url(redis_url, decode_responses=True)

  return Storage(
      redis=redis,
      staging_dir=staging_dir,
      **kwargs
  )
