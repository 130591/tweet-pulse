from typing import List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime

from ..models.tweet import Tweet
from ..models.sentiment import Sentiment
from ..models.entity import Entity
from ..models.hashtag import Hashtag


class TweetRepository(BaseRepository[Tweet]):
  def __init__(self, session: AsyncSession):
    super().__init__(session, Tweet)

  async def get_by_id(self, tweet_id: int) -> Optional[Tweet]:
    result = await self.session.execute(
        select(Tweet)
        .where(Tweet.id == tweet_id)
        .options(
          selectinload(Tweet.profile),
          selectinload(Tweet.sentiment),
          selectinload(Tweet.entities),
          selectinload(Tweet.hashtags),
          selectinload(Tweet.mentions),
          selectinload(Tweet.media_items)
        )
    )
    return result.scalar_one_or_none()

  async def get_by_profile(self, profile_id: int, limit: int = 100) -> List[Tweet]:
    result = await self.session.execute(
      select(Tweet)
      .where(Tweet.profile_id == profile_id)
      .order_by(Tweet.created_at.desc())
      .limit(limit)
    )
    return result.scalars().all()

  async def create(self, tweet_data: dict) -> Tweet:
    tweet = Tweet(**tweet_data)
    self.session.add(tweet)
    await self.session.flush()
    return tweet

  async def upsert(self, tweet_data: dict) -> Tweet:
      existing = await self.get_by_id(tweet_data.get('id'))
      if existing:
          for key, value in tweet_data.items():
              if key not in ['id']:
                  setattr(existing, key, value)
          return existing
      else:
          return await self.create(tweet_data)

  async def get_by_date_range(
      self,
      start_date: datetime,
      end_date: datetime,
      limit: int = 1000
  ) -> List[Tweet]:
    result = await self.session.execute(
      select(Tweet)
      .where(and_(
        Tweet.created_at >= start_date,
        Tweet.created_at <= end_date
      ))
      .order_by(Tweet.created_at.desc())
      .limit(limit)
    )
    return result.scalars().all()

  async def get_with_sentiment(self, sentiment_label: str, limit: int = 100) -> List[Tweet]:
    result = await self.session.execute(
      select(Tweet)
      .join(Sentiment)
      .where(Sentiment.label == sentiment_label)
      .order_by(Tweet.created_at.desc())
      .limit(limit)
    )
    return result.scalars().all()

  async def get_top_by_engagement(self, limit: int = 10) -> List[Tweet]:
    result = await self.session.execute(
      select(Tweet)
      .order_by(
        (Tweet.retweet_count + Tweet.like_count + Tweet.reply_count + Tweet.quote_count).desc()
      )
      .limit(limit)
    )
    return result.scalars().all()

  async def get_by_hashtag(self, tag: str, limit: int = 100) -> List[Tweet]:
    result = await self.session.execute(
      select(Tweet)
      .join(Hashtag)
      .where(Hashtag.tag == tag)
      .order_by(Tweet.created_at.desc())
      .limit(limit)
    )
    return result.scalars().all()

  async def count_by_profile(self, profile_id: int) -> int:
    result = await self.session.execute(
      select(func.count()).select_from(Tweet).where(Tweet.profile_id == profile_id)
    )
    return result.scalar()

  async def get_threads(self, parent_tweet_id: int) -> List[Tweet]:
    result = await self.session.execute(
      select(Tweet)
      .where(Tweet.parent_tweet_id == parent_tweet_id)
      .order_by(Tweet.created_at.asc())
    )
    return result.scalars().all()