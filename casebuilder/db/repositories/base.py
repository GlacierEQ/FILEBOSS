"""
Base repository class with common CRUD operations.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload

from ..base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType], ABC):
    """
    Base repository class with common CRUD operations.

    Args:
        model: SQLAlchemy model class
        db_session: SQLAlchemy session (sync or async)
    """

    def __init__(self, model: Type[ModelType], db_session: Union[Session, AsyncSession]):
        self.model = model
        self.db_session = db_session

    @property
    def is_async(self) -> bool:
        """Check if the repository is using an async session."""
        return hasattr(self.db_session, "execute")

    async def get(self, id: Any, **kwargs) -> Optional[ModelType]:
        """
        Get a single record by ID.

        Args:
            id: The ID of the record to retrieve
            **kwargs: Additional query parameters

        Returns:
            Optional[ModelType]: The record if found, None otherwise
        """
        query = select(self.model).where(self.model.id == id)

        # Handle relationships
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        if self.is_async:
            result = await self.db_session.execute(query)
        else:
            result = self.db_session.execute(query)

        return result.scalar_one_or_none()

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[ModelType]:
        """
        Get multiple records with optional filtering and pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            **filters: Filter criteria

        Returns:
            List[ModelType]: List of records
        """
        query = select(self.model).offset(skip).limit(limit)

        # Apply filters
        for key, value in filters.items():
            if hasattr(self.model, key):
                if isinstance(value, (list, tuple)):
                    query = query.where(getattr(self.model, key).in_(value))
                else:
                    query = query.where(getattr(self.model, key) == value)

        if self.is_async:
            result = await self.db_session.execute(query)
        else:
            result = self.db_session.execute(query)

        return result.scalars().all()

    async def create(self, obj_in: CreateSchemaType, **kwargs) -> ModelType:
        """
        Create a new record.

        Args:
            obj_in: Pydantic model with data to create
            **kwargs: Additional attributes to set on the model

        Returns:
            ModelType: The created record
        """
        obj_in_data = obj_in.dict(exclude_unset=True)
        obj_in_data.update(kwargs)

        if self.is_async:
            # For async, we need to create the instance and add it to the session
            db_obj = self.model(**obj_in_data)
            self.db_session.add(db_obj)
            await self.db_session.commit()
            await self.db_session.refresh(db_obj)
        else:
            # For sync, we can use the session.add() pattern
            db_obj = self.model(**obj_in_data)
            self.db_session.add(db_obj)
            self.db_session.commit()
            self.db_session.refresh(db_obj)

        return db_obj

    async def update(
        self,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update a record.

        Args:
            db_obj: The database object to update
            obj_in: Pydantic model or dict with data to update

        Returns:
            ModelType: The updated record
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        if self.is_async:
            self.db_session.add(db_obj)
            await self.db_session.commit()
            await self.db_session.refresh(db_obj)
        else:
            self.db_session.add(db_obj)
            self.db_session.commit()
            self.db_session.refresh(db_obj)

        return db_obj

    async def delete(self, id: Any) -> bool:
        """
        Delete a record by ID.

        Args:
            id: The ID of the record to delete

        Returns:
            bool: True if the record was deleted, False otherwise
        """
        if self.is_async:
            result = await self.db_session.execute(
                delete(self.model).where(self.model.id == id).returning(self.model.id)
            )
            await self.db_session.commit()
            return result.scalar_one_or_none() is not None
        else:
            result = self.db_session.execute(
                delete(self.model).where(self.model.id == id).returning(self.model.id)
            )
            self.db_session.commit()
            return result.scalar_one_or_none() is not None

    async def exists(self, **filters) -> bool:
        """
        Check if a record exists matching the given filters.

        Args:
            **filters: Filter criteria

        Returns:
            bool: True if a matching record exists, False otherwise
        """
        query = select(self.model.id).limit(1)

        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        if self.is_async:
            result = await self.db_session.execute(query)
        else:
            result = self.db_session.execute(query)

        return result.scalar_one_or_none() is not None

    async def count(self, **filters) -> int:
        """
        Count records matching the given filters.

        Args:
            **filters: Filter criteria

        Returns:
            int: The number of matching records
        """
        from sqlalchemy import func

        query = select(func.count()).select_from(self.model)

        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        if self.is_async:
            result = await self.db_session.execute(query)
        else:
            result = self.db_session.execute(query)

        return result.scalar_one()


class BaseRepositoryAsync(BaseRepository[ModelType, CreateSchemaType, UpdateSchemaType], ABC):
    """
    Base repository class for async database operations.

    This is a convenience class that enforces async session usage.
    """

    def __init__(self, model: Type[ModelType], db_session: AsyncSession):
        """
        Initialize async repository with type checking and validation.

        Args:
            model: SQLAlchemy model class
            db_session: AsyncSession instance

        Raises:
            TypeError: If db_session is not an AsyncSession
            ValueError: If session is not properly initialized
        """
        if not isinstance(db_session, AsyncSession):
            raise TypeError(f"Expected AsyncSession, got {type(db_session)}")
        if not hasattr(db_session, "execute"):
            raise ValueError("Session not properly initialized - missing execute method")
        super().__init__(model, db_session)

    async def get_with_related(
        self,
        id: Any,
        *relationships: str,
        **filters
    ) -> Optional[ModelType]:
        """
        Get a record by ID with related models loaded.

        Args:
            id: The ID of the record to retrieve
            *relationships: Names of relationships to load
            **filters: Additional filter criteria

        Returns:
            Optional[ModelType]: The record with related models loaded if found
        """
        query = select(self.model).where(self.model.id == id)

        # Add relationships to load
        if relationships:
            for rel in relationships:
                if hasattr(self.model, rel):
                    query = query.options(joinedload(getattr(self.model, rel)))

        # Add additional filters
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        result = await self.db_session.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_multi_with_related(
        self,
        skip: int = 0,
        limit: int = 100,
        relationships: Optional[List[str]] = None,
        **filters
    ) -> List[ModelType]:
        """
        Get multiple records with related models loaded and optional filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            relationships: Optional list of relationship names to load
            **filters: Filter criteria

        Returns:
            List[ModelType]: List of records with related models loaded
        """
        query = select(self.model).offset(skip).limit(limit)

        # Add relationships to load
        if relationships:
            for rel in relationships:
                if hasattr(self.model, rel):
                    query = query.options(joinedload(getattr(self.model, rel)))

        # Apply filters
        for key, value in filters.items():
            if hasattr(self.model, key):
                if isinstance(value, (list, tuple)):
                    query = query.where(getattr(self.model, key).in_(value))
                else:
                    query = query.where(getattr(self.model, key) == value)

        result = await self.db_session.execute(query)
        return list(result.unique().scalars().all())


class BaseRepositorySync(BaseRepository[ModelType, CreateSchemaType, UpdateSchemaType], ABC):
    """
    Base repository class for sync database operations.

    This is a convenience class that enforces sync session usage.
    """

    def __init__(self, model: Type[ModelType], db_session: Session):
        if hasattr(db_session, "execute"):
            raise ValueError("Sync Session required for BaseRepositorySync")
        super().__init__(model, db_session)
