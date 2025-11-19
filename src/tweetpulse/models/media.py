from typing import Dict, Any
from sqlalchemy import Column, Integer, BigInteger, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class Media(Base):
  __tablename__ = "media"

  id = Column(Integer, primary_key=True)
  tweet_id = Column(BigInteger, ForeignKey("tweets.id", ondelete="CASCADE"), nullable=False)
  url = Column(String(255), nullable=False)
  type = Column(String(20))
  alt_text = Column(Text)

  # Relationships
  tweet = relationship("Tweet", back_populates="media_items")

  def to_dict(self) -> Dict[str, Any]:
    return {
      "id": self.id,
      "tweet_id": str(self.tweet_id),
      "url": self.url,
      "type": self.type,
      "alt_text": self.alt_text
    }
