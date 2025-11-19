from typing import Dict, Any
from sqlalchemy import Column, Integer, BigInteger, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class Mention(Base):
  __tablename__ = "mentions"

  id = Column(Integer, primary_key=True)
  tweet_id = Column(BigInteger, ForeignKey("tweets.id", ondelete="CASCADE"), nullable=False)
  mentioned_profile_id = Column(BigInteger, ForeignKey("twitter_profiles.id", ondelete="CASCADE"), nullable=False)

  # Relationships
  tweet = relationship("Tweet", back_populates="mentions")
  mentioned_profile = relationship("TwitterProfile", back_populates="mentions_received")

  def to_dict(self) -> Dict[str, Any]:
    return {
      "id": self.id,
      "tweet_id": str(self.tweet_id),
      "mentioned_profile_id": str(self.mentioned_profile_id),
      "mentioned_profile": self.mentioned_profile.to_dict() if self.mentioned_profile else None
    }
