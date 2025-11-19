from typing import Dict, Any
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class ProfileSnapshot(Base):
  """Modelo para snapshots históricos de perfis"""
  __tablename__ = "profile_snapshots"

  id = Column(Integer, primary_key=True)
  profile_id = Column(BigInteger, ForeignKey("twitter_profiles.id", ondelete="CASCADE"), nullable=False)
  captured_at = Column(DateTime(timezone=True), default=datetime.utcnow)
  followers_count = Column(Integer)
  following_count = Column(Integer)
  tweet_count = Column(Integer)
  location = Column(String(100))

  # Relationships
  profile = relationship("TwitterProfile", back_populates="snapshots")

  def to_dict(self) -> Dict[str, Any]:
      return {
        "id": self.id,
        "profile_id": self.profile_id,
        "captured_at": self.captured_at.isoformat() if self.captured_at else None,
        "followers_count": self.followers_count,
        "following_count": self.following_count,
        "tweet_count": self.tweet_count,
        "location": self.location
      }
