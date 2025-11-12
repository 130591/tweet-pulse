from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .database import Base


class Tweet(Base):
    __tablename__ = "tweets"
    
    id = Column(String, primary_key=True)
    text = Column(String, nullable=False)
    author_id = Column(String, nullable=False)
    author_name = Column(String)
    author_username = Column(String)
    
    created_at = Column(DateTime, nullable=False)
    ingested_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    
    retweet_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    quote_count = Column(Integer, default=0)
    
    lang = Column(String)
    
    sentiment_label = Column(String)
    sentiment_score = Column(Float)
    
    entities = Column(JSON, default=list)
    keywords = Column(JSON, default=list)
    
    source = Column(String, default="twitter")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "author_id": self.author_id,
            "author_name": self.author_name,
            "author_username": self.author_username,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "ingested_at": self.ingested_at.isoformat() if self.ingested_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "retweet_count": self.retweet_count,
            "reply_count": self.reply_count,
            "like_count": self.like_count,
            "quote_count": self.quote_count,
            "lang": self.lang,
            "sentiment_label": self.sentiment_label,
            "sentiment_score": self.sentiment_score,
            "entities": self.entities or [],
            "keywords": self.keywords or [],
            "source": self.source,
            "total_engagement": self.retweet_count + self.reply_count + self.like_count + self.quote_count
        }


class TweetCreate:
    def __init__(
        self,
        id: str,
        text: str,
        author_id: str,
        created_at: str,
        **kwargs
    ):
        self.id = id
        self.text = text
        self.author_id = author_id
        self.created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00')) if isinstance(created_at, str) else created_at
        
        self.author_name = kwargs.get('author_name')
        self.author_username = kwargs.get('author_username')
        self.retweet_count = kwargs.get('retweet_count', 0)
        self.reply_count = kwargs.get('reply_count', 0)
        self.like_count = kwargs.get('like_count', 0)
        self.quote_count = kwargs.get('quote_count', 0)
        self.lang = kwargs.get('lang', 'en')
        self.sentiment_label = kwargs.get('sentiment_label')
        self.sentiment_score = kwargs.get('sentiment_score')
        self.entities = kwargs.get('entities', [])
        self.keywords = kwargs.get('keywords', [])
        
    def model_dump(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "author_id": self.author_id,
            "author_name": self.author_name,
            "author_username": self.author_username,
            "created_at": self.created_at,
            "retweet_count": self.retweet_count,
            "reply_count": self.reply_count,
            "like_count": self.like_count,
            "quote_count": self.quote_count,
            "lang": self.lang,
            "sentiment_label": self.sentiment_label,
            "sentiment_score": self.sentiment_score,
            "entities": self.entities,
            "keywords": self.keywords
        }
