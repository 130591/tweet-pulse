#!/usr/bin/env python3
"""
Redis Streams Setup Script
Creates consumer groups required for TweetPulse workers
"""
import asyncio
import os
import sys
from redis import asyncio as aioredis


async def setup_redis_streams():
  """Create consumer groups for Redis Streams"""
  redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
  
  print(f"Connecting to Redis at {redis_url}...")
  redis_client = await aioredis.from_url(redis_url, decode_responses=True)
  
  stream_key = "ingest:stream"
  groups = ["workers", "batch_workers"]
  
  try:
    # Check if stream exists, if not create it with a dummy message
    exists = await redis_client.exists(stream_key)
    if not exists:
        print(f"Stream '{stream_key}' does not exist. Creating it...")
        await redis_client.xadd(stream_key, {"init": "setup"})
        print(f"✓ Stream '{stream_key}' created")
    else:
        print(f"✓ Stream '{stream_key}' already exists")
    
    # Create consumer groups
    for group_name in groups:
        try:
            await redis_client.xgroup_create(
                name=stream_key,
                groupname=group_name,
                id="0",  # Start from beginning
                mkstream=True
            )
            print(f"✓ Consumer group '{group_name}' created")
        except aioredis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                print(f"✓ Consumer group '{group_name}' already exists")
            else:
                raise
    
    print("\n✅ Redis Streams setup completed successfully!")
      
  except Exception as e:
      print(f"\n❌ Error setting up Redis Streams: {e}", file=sys.stderr)
      sys.exit(1)
  finally:
      await redis_client.aclose()


if __name__ == "__main__":
    asyncio.run(setup_redis_streams())
