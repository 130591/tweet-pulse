from typing import Dict, Any
from sqlalchemy import Column, Integer, BigInteger, String, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class Hashtag(Base):
  __tablename__ = "hashtags"

  id = Column(Integer, primary_key=True)
  tweet_id = Column(BigInteger, ForeignKey("tweets.id", ondelete="CASCADE"), nullable=False)
  tag = Column(String(100), nullable=False)

  # Relationships
  tweet = relationship("Tweet", back_populates="hashtags")

  def to_dict(self) -> Dict[str, Any]:
    return {
      "id": self.id,
      "tweet_id": str(self.tweet_id),
      "tag": self.tag
    }
