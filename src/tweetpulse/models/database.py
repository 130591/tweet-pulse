from sqlalchemy import Column, String, DateTime, Enum, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from enum import Enum as PyEnum

Base = declarative_base()

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