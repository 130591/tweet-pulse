from typing import Dict, Any
from sqlalchemy import Column, Integer, BigInteger, String, Numeric, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

from .database import Base


class Entity(Base):
  __tablename__ = "entities"

  id = Column(Integer, primary_key=True)
  tweet_id = Column(BigInteger, ForeignKey("tweets.id", ondelete="CASCADE"), nullable=False)
  text = Column(String(100), nullable=False)
  type = Column(String(20), nullable=False)
  score = Column(Numeric(5, 4))

  # Relationships
  tweet = relationship("Tweet", back_populates="entities")

  __table_args__ = (
    CheckConstraint("type IN ('PERSON', 'ORG', 'LOCATION', 'PRODUCT', 'EVENT')",
    name='valid_entity_type'),
  )

  def to_dict(self) -> Dict[str, Any]:
    return {
      "id": self.id,
      "tweet_id": str(self.tweet_id),
      "text": self.text,
      "type": self.type,
      "score": float(self.score) if self.score else None
    }
