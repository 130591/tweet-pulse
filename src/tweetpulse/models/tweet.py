from typing import Dict, Any
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Integer, DateTime, ForeignKey, Text, CheckConstraint
from sqlalchemy.orm import relationship

from .database import Base


class Tweet(Base):
  __tablename__ = "tweets"

  id = Column(BigInteger, primary_key=True)
  profile_id = Column(BigInteger, ForeignKey("twitter_profiles.id", ondelete="CASCADE"), nullable=False)
  parent_tweet_id = Column(BigInteger, ForeignKey("tweets.id", ondelete="SET NULL"))
  content = Column(Text, nullable=False)
  language = Column(String(10))

  created_at = Column(DateTime(timezone=True), nullable=False)
  ingested_at = Column(DateTime(timezone=True), default=datetime.utcnow)
  processed_at = Column(DateTime(timezone=True))

  retweet_count = Column(Integer, default=0)
  reply_count = Column(Integer, default=0)
  like_count = Column(Integer, default=0)
  quote_count = Column(Integer, default=0)

  # Relationships
  profile = relationship("TwitterProfile", back_populates="tweets")
  parent_tweet = relationship("Tweet", remote_side=[id], backref="replies")
  entities = relationship("Entity", back_populates="tweet", cascade="all, delete-orphan")
  hashtags = relationship("Hashtag", back_populates="tweet", cascade="all, delete-orphan")
  mentions = relationship("Mention", back_populates="tweet", cascade="all, delete-orphan")
  media_items = relationship("Media", back_populates="tweet", cascade="all, delete-orphan")
  sentiment = relationship("Sentiment", back_populates="tweet", uselist=False, cascade="all, delete-orphan")

  __table_args__ = (
      CheckConstraint('retweet_count >= 0 AND reply_count >= 0 AND like_count >= 0 AND quote_count >= 0',
                      name='positive_counts'),
  )

  def to_dict(self) -> Dict[str, Any]:
    return {
        "id": str(self.id),
        "profile_id": str(self.profile_id),
        "parent_tweet_id": str(self.parent_tweet_id) if self.parent_tweet_id else None,
        "content": self.content,
        "language": self.language,
        "created_at": self.created_at.isoformat() if self.created_at else None,
        "ingested_at": self.ingested_at.isoformat() if self.ingested_at else None,
        "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        "retweet_count": self.retweet_count,
        "reply_count": self.reply_count,
        "like_count": self.like_count,
        "quote_count": self.quote_count,
        "total_engagement": self.retweet_count + self.reply_count + self.like_count + self.quote_count,
        "profile": self.profile.to_dict() if self.profile else None,
        "sentiment": self.sentiment.to_dict() if self.sentiment else None,
        "entities": [e.to_dict() for e in self.entities] if self.entities else [],
        "hashtags": [h.to_dict() for h in self.hashtags] if self.hashtags else [],
        "mentions": [m.to_dict() for m in self.mentions] if self.mentions else [],
        "media": [m.to_dict() for m in self.media_items] if self.media_items else []
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
    self.created_at = datetime.fromisoformat(created_at.replace(
        'Z', '+00:00')) if isinstance(created_at, str) else created_at

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
