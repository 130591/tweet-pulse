from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Generic, Optional, TypeVar, List, Dict, Any
from sqlalchemy.dialects.postgresql import insert

Base = declarative_base()
T = TypeVar("T", bound=Base)

class BaseRepository(Generic[T]):
	"""
	Base repository class providing common CRUD operations.
	
	This class implements the Repository pattern for better separation of concerns,
	abstracting database operations from business logic.
	"""
	def __init__(self, session: Session, model: T):
		self.session = session
		self.model = model
	
	def create(self, **kwargs) -> T:
		"""Create a new record."""
		instance = self.model(**kwargs)
		self.session.add(instance)
		self.session.commit()
		self.session.refresh(instance)
		return instance

	async def get_by_id(self, id: str) -> Optional[T]:
		"""Get a record by its ID."""
		from sqlalchemy import select
		result = await self.session.execute(select(self.model).filter(self.model.id == id))
		return result.scalar_one_or_none()

	def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
		"""Get all records with pagination."""
		return (
			self.session.query(self.model)
			.offset(skip)
			.limit(limit)
			.all()
		)
	
	def update(self, id: str, **kwargs) -> Optional[T]:
		"""Update a record by its ID."""
		instance = self.get_by_id(id)
		if instance:
			for key, value in kwargs.items():
				if hasattr(instance, key):
					setattr(instance, key, value)
			self.session.commit()
			self.session.refresh(instance)
		return instance
	
	def delete(self, id: str) -> bool:
		"""Delete a record by its ID."""
		instance = self.get_by_id(id)
		if instance:
			self.session.delete(instance)
			self.session.commit()
			return True
		return False

	def exists(self, id: str) -> bool:
			"""Check if a record exists by its ID."""
			return self.session.query(self.model).filter(self.model.id == id).first() is not None
	
	def count(self) -> int:
			"""Count total records."""
			return self.session.query(self.model).count()
	
	def filter_by(self, **kwargs) -> List[T]:
			"""Filter records by given criteria."""
			query = self.session.query(self.model)
			for key, value in kwargs.items():
					if hasattr(self.model, key):
						query = query.filter(getattr(self.model, key) == value)
			return query.all()
	
	def find_by_criteria(self, **kwargs) -> Optional[T]:
			"""Find first record matching criteria."""
			query = self.session.query(self.model)
			for key, value in kwargs.items():
				if hasattr(self.model, key):
					query = query.filter(getattr(self.model, key) == value)
			return query.first()
	
	def bulk_create(self, records: List[Dict[str, Any]], return_defaults: bool = False) -> List[T]:
			"""Bulk insert multiple records efficiently."""
			if not records:
				return []
			
			try:
				instances = [self.model(**record) for record in records]
				self.session.bulk_save_objects(instances, return_defaults=return_defaults)
				self.session.commit()
				return instances
			except Exception as e:
					self.session.rollback()
					raise e
	
	async def upsert(self, record: Dict[str, Any] | T, conflict_fields: List[str] = None) -> T:
		"""Upsert a single record (insert or update on conflict)."""
		if isinstance(record, dict):
			data = record
		else:
			# If it's a Pydantic model or has model_dump
			data = record.model_dump() if hasattr(record, 'model_dump') else record.__dict__
		
		try:
			stmt = insert(self.model.__table__).values(data)
			
			if conflict_fields:
				# Update all fields except the conflict fields
				update_dict = {c.name: c for c in stmt.excluded if c.name not in conflict_fields}
				stmt = stmt.on_conflict_do_update(
					index_elements=conflict_fields,
					set_=update_dict
				)
			else:
				# Use primary key (id) as default conflict field
				update_dict = {c.name: c for c in stmt.excluded if c.name != 'id'}
				stmt = stmt.on_conflict_do_update(
					index_elements=['id'],
					set_=update_dict
				)
			
			await self.session.execute(stmt)
			await self.session.commit()
			
			# Return the inserted/updated record
			return await self.get_by_id(data.get('id'))
		except Exception as e:
			await self.session.rollback()
			raise e
	
	async def upsert_many(self, records: List[Dict[str, Any]], conflict_fields: List[str] = None) -> int:
		if not records:
			return 0
		
		try:
			stmt = insert(self.model.__table__).values(records)
			
			if conflict_fields:
				# Update all fields except the conflict fields
				update_dict = {c.name: c for c in stmt.excluded if c.name not in conflict_fields}
				stmt = stmt.on_conflict_do_update(
					index_elements=conflict_fields,
					set_=update_dict
				)
			else:
				# Use primary key as default conflict field
				stmt = stmt.on_conflict_do_nothing()
			
			result = await self.session.execute(stmt)
			await self.session.commit()
			return result.rowcount
		except Exception as e:
			await self.session.rollback()
			raise e