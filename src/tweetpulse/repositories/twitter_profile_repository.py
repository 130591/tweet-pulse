from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from ..models.twitter_profile import TwitterProfile
from ..models.profile_snapshot import ProfileSnapshot


class TwitterProfileRepository:
  def __init__(self, session: AsyncSession):
    self.session = session

  async def get_by_id(self, profile_id: int) -> Optional[TwitterProfile]:
    result = await self.session.execute(
      select(TwitterProfile).where(TwitterProfile.id == profile_id)
    )
    return result.scalar_one_or_none()

  async def get_by_username(self, username: str) -> Optional[TwitterProfile]:
    result = await self.session.execute(
      select(TwitterProfile).where(TwitterProfile.username == username)
    )
    return result.scalar_one_or_none()

  async def create(self, profile_data: dict) -> TwitterProfile:
    profile = TwitterProfile(**profile_data)
    self.session.add(profile)
    await self.session.flush()
    return profile

  async def upsert(self, profile_data: dict) -> TwitterProfile:
    existing = await self.get_by_id(profile_data.get('id'))
    if existing:
      for key, value in profile_data.items():
        setattr(existing, key, value)
      existing.last_updated = datetime.utcnow()
      return existing
    else:
        return await self.create(profile_data)

  async def create_snapshot(self, profile_id: int, snapshot_data: dict) -> ProfileSnapshot:
    snapshot = ProfileSnapshot(
      profile_id=profile_id,
      **snapshot_data
    )
    self.session.add(snapshot)
    await self.session.flush()
    return snapshot

  async def get_latest_snapshot(self, profile_id: int) -> Optional[ProfileSnapshot]:
    result = await self.session.execute(
      select(ProfileSnapshot)
      .where(ProfileSnapshot.profile_id == profile_id)
      .order_by(ProfileSnapshot.captured_at.desc())
      .limit(1)
    )
    return result.scalar_one_or_none()

  async def get_snapshots(
    self,
    profile_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
  ) -> List[ProfileSnapshot]:
    query = select(ProfileSnapshot).where(ProfileSnapshot.profile_id == profile_id)
    
    if start_date:
        query = query.where(ProfileSnapshot.captured_at >= start_date)
    if end_date:
        query = query.where(ProfileSnapshot.captured_at <= end_date)
    
    query = query.order_by(ProfileSnapshot.captured_at.asc())
    
    result = await self.session.execute(query)
    return result.scalars().all()

  async def get_active_profiles(self, days: int = 7) -> List[TwitterProfile]:
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    result = await self.session.execute(
        select(TwitterProfile)
        .where(TwitterProfile.last_updated >= cutoff_date)
    )
    return result.scalars().all()
