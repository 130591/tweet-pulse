from functools import lru_cache
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from redis.asyncio import Redis
from elasticsearch import AsyncElasticsearch

from .config import get_settings

settings = get_settings()

@lru_cache()
def get_db_session_factory():
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        pool_size=20,
        max_overflow=10
    )
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@lru_cache()
def get_redis_client() -> Redis:
    return Redis.from_url(settings.REDIS_URL, decode_responses=True)

@lru_cache()
def get_elasticsearch_client() -> AsyncElasticsearch:
    return AsyncElasticsearch([settings.ELASTICSEARCH_URL])

async def get_db_session():
    factory = get_db_session_factory()
    async with factory() as session:
        yield session