import asyncio
from redis.asyncio import Redis

async def main():
    redis = Redis.from_url("redis://redis:6379")
    # Create the stream and consumer group
    await redis.xgroup_create("ingest:stream", "workers", id="0", mkstream=True)
    print("Created Redis stream 'ingest:stream' and consumer group 'workers'")

if __name__ == "__main__":
    asyncio.run(main())
