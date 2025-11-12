from sqlalchemy import Column, String, DateTime, Enum, Float, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from typing import AsyncGenerator
import os

Base = declarative_base()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost:5432/tweetpulse")

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False)

# Create async session factory
SessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Dependency for FastAPI


async def get_db() -> AsyncGenerator[AsyncSession, None]:
  async with SessionLocal() as session:
    try:
      yield session
      await session.commit()
    except Exception:
      await session.rollback()
      raise
    finally:
      await session.close()


class SentimentType(str, PyEnum):
  POSITIVE = "positive"
  NEGATIVE = "negative"
  NEUTRAL = "neutral"


class Tweet(Base):
  __tablename__ = "tweets"

  id = Column(String, primary_key=True)
  content = Column(String(280), nullable=False)
  author_id = Column(String, nullable=False)
  created_at = Column(DateTime, nullable=False)

  sentiment = Column(Enum(SentimentType), nullable=True)
  confidence = Column(Float, nullable=True)
  retweet_count = Column(Integer, index=True)
  like_count = Column(Integer, index=True)
  reply_count = Column(Integer)
  quote_count = Column(Integer)
  bookmark_count = Column(Integer)
  impression_count = Column(Integer)
