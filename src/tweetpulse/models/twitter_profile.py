from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from .database import Base


class TwitterProfile(Base):
  __tablename__ = "twitter_profiles"

  id = Column(BigInteger, primary_key=True)
  username = Column(String(50), nullable=False)
  name = Column(String(100))
  is_protected = Column(Boolean, nullable=False, default=False)
  created_at = Column(DateTime(timezone=True))
  last_updated = Column(DateTime(timezone=True), default=datetime.utcnow)

  # Relationships
  tweets = relationship("Tweet", back_populates="profile", cascade="all, delete-orphan")
  snapshots = relationship("ProfileSnapshot", back_populates="profile", cascade="all, delete-orphan")
  mentions_received = relationship("Mention", back_populates="mentioned_profile")

  def to_dict(self) -> Dict[str, Any]:
    return {
      "id": self.id,
      "username": self.username,
      "name": self.name,
      "is_protected": self.is_protected,
      "created_at": self.created_at.isoformat() if self.created_at else None,
      "last_updated": self.last_updated.isoformat() if self.last_updated else None
    }
