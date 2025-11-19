from typing import Dict, Any
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Numeric, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

from .database import Base


class Sentiment(Base):
  """Modelo para análise de sentimento dos tweets"""
  __tablename__ = "sentiments"

  tweet_id = Column(BigInteger, ForeignKey("tweets.id", ondelete="CASCADE"), primary_key=True)
  label = Column(String(10), nullable=False)
  score = Column(Numeric(3, 2), nullable=False)
  model = Column(String(50), nullable=False)
  processed_at = Column(DateTime(timezone=True), default=datetime.utcnow)

  # Relationships
  tweet = relationship("Tweet", back_populates="sentiment")

  __table_args__ = (
      CheckConstraint("label IN ('POSITIVE', 'NEUTRAL', 'NEGATIVE')",
        name='valid_sentiment'),
  )

  def to_dict(self) -> Dict[str, Any]:
    return {
      "tweet_id": str(self.tweet_id),
      "label": self.label,
      "score": float(self.score) if self.score else None,
      "model": self.model,
      "processed_at": self.processed_at.isoformat() if self.processed_at else None
    }
