import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class Settings:
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/tweetpulse"
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    REDIS_URL: str = "redis://localhost:6379"
    
    TWITTER_BEARER_TOKEN: str = ""
    
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DATABASE_ECHO: bool = False
    
    STREAM_KEY: str = "ingest:stream"
    STREAM_CONSUMER_GROUP: str = "workers"
    
    def __post_init__(self):
        self.DATABASE_URL = os.getenv("DATABASE_URL", self.DATABASE_URL)
        self.ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", self.ELASTICSEARCH_URL)
        self.REDIS_URL = os.getenv("REDIS_URL", self.REDIS_URL)
        self.TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", self.TWITTER_BEARER_TOKEN)
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"
        self.HOST = os.getenv("HOST", self.HOST)
        self.PORT = int(os.getenv("PORT", str(self.PORT)))
        self.DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"
        self.STREAM_KEY = os.getenv("STREAM_KEY", self.STREAM_KEY)
        self.STREAM_CONSUMER_GROUP = os.getenv("STREAM_CONSUMER_GROUP", self.STREAM_CONSUMER_GROUP)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
