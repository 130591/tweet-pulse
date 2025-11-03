from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from .base import BaseRepository
from ..models.database import Tweet

class TweetRepository(BaseRepository[Tweet]):
	"""
	Repository for Tweet entity with specific operations.
	"""
	
	def __init__(self, session: Session):
		super().__init__(session, Tweet)
	
	def get_by_author(self, author_id: str) -> List[Tweet]:
		"""Get tweets by author ID."""
		return self.filter_by(author_id=author_id)
	
	def get_tweets_with_sentiment(self) -> List[Tweet]:
		"""Get tweets that have sentiment analysis."""
		return self.session.query(Tweet).filter(
			Tweet.sentiment.isnot(None)
		).all()
	
	def get_tweets_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Tweet]:
		"""Get tweets within a date range."""
		return self.session.query(Tweet).filter(
			Tweet.created_at.between(start_date, end_date)
		).all()
	
	def get_top_tweets_by_likes(self, limit: int = 10) -> List[Tweet]:
		"""Get top tweets ordered by likes."""
		return self.session.query(Tweet).order_by(
			Tweet.like_count.desc()
		).limit(limit).all()

	def get_tweets_by_sentiment(self, sentiment: str) -> List[Tweet]:
		"""Get tweets by sentiment type."""
		return self.filter_by(sentiment=sentiment)
	
	def get_tweets_above_confidence(self, threshold: float) -> List[Tweet]:
		"""Get tweets with confidence above threshold."""
		return self.session.query(Tweet).filter(
			Tweet.confidence >= threshold
		).all()
	
	def count_by_author(self, author_id: str) -> int:
		"""Count tweets by author."""
		return self.session.query(Tweet).filter(
			Tweet.author_id == author_id
		).count()