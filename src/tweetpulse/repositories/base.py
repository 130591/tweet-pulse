from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Generic, Optional, TypeVar, List

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
    
    def get_by_id(self, id: str) -> Optional[T]:
        """Get a record by its ID."""
        return self.session.query(self.model).filter(self.model.id == id).first()
    
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