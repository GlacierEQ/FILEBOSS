"""
Case repository implementation.
"""
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel
from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload, selectinload

from ...schemas.case import CaseCreate, CaseUpdate
from ..models import Case, CaseStatus, User
from .base import BaseRepository, BaseRepositoryAsync, BaseRepositorySync


class CaseRepository(BaseRepository[Case, CaseCreate, CaseUpdate]):
    """
    Repository for Case model with common CRUD operations.
    """
    
    def __init__(self, db_session: Union[Session, AsyncSession]):
        super().__init__(Case, db_session)
    
    async def search(
        self,
        query: str,
        *,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[Case]:
        """
        Search cases by title, description, or case number.
        
        Args:
            query: Search query string
            skip: Number of records to skip
            limit: Maximum number of records to return
            **filters: Additional filter criteria
            
        Returns:
            List[Case]: List of matching cases
        """
        search_condition = or_(
            Case.title.ilike(f"%{query}%"),
            Case.description.ilike(f"%{query}%"),
            Case.case_number.ilike(f"%{query}%")
        )
        
        query_obj = select(Case).where(search_condition).offset(skip).limit(limit)
        
        # Apply additional filters
        for key, value in filters.items():
            if hasattr(Case, key):
                if isinstance(value, (list, tuple)):
                    query_obj = query_obj.where(getattr(Case, key).in_(value))
                else:
                    query_obj = query_obj.where(getattr(Case, key) == value)
        
        if self.is_async:
            result = await self.db_session.execute(query_obj)
        else:
            result = self.db_session.execute(query_obj)
            
        return result.scalars().all()
    
    async def get_by_status(
        self, 
        status: CaseStatus, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Case]:
        """
        Get cases by status.
        
        Args:
            status: Case status to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Case]: List of cases with the specified status
        """
        return await self.get_multi(
            status=status,
            skip=skip,
            limit=limit
        )
    
    async def get_by_owner(
        self, 
        owner_id: str, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Case]:
        """
        Get cases owned by a specific user.
        
        Args:
            owner_id: ID of the owner
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Case]: List of cases owned by the user
        """
        return await self.get_multi(
            owner_id=owner_id,
            skip=skip,
            limit=limit
        )
    
    async def get_by_participant(
        self, 
        user_id: str, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Case]:
        """
        Get cases where a user is a participant.
        
        Args:
            user_id: ID of the participant
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Case]: List of cases where the user is a participant
        """
        from sqlalchemy import select
        from sqlalchemy.orm import aliased
        
        # Create an alias for the association table
        cp = aliased(case_participants)
        
        # Build the query
        query = (
            select(Case)
            .join(cp, Case.id == cp.c.case_id)
            .where(cp.c.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        
        if self.is_async:
            result = await self.db_session.execute(query)
        else:
            result = self.db_session.execute(query)
            
        return result.scalars().all()


class CaseRepositoryAsync(CaseRepository, BaseRepositoryAsync[Case, CaseCreate, CaseUpdate]):
    """
    Async repository for Case model with additional async methods.
    """
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
    
    async def get_with_participants(
        self, 
        case_id: str, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> Optional[Case]:
        """
        Get a case with its participants loaded.
        
        Args:
            case_id: The ID of the case to retrieve
            skip: Number of participants to skip
            limit: Maximum number of participants to return
            
        Returns:
            Optional[Case]: The case with participants if found
        """
        from sqlalchemy import select
        from sqlalchemy.orm import aliased
        
        # Create an alias for the association table
        cp = aliased(case_participants)
        
        # Build the query
        query = (
            select(Case)
            .options(selectinload(Case.participants))
            .where(Case.id == case_id)
        )
        
        result = await self.db_session.execute(query)
        return result.unique().scalar_one_or_none()
    
    async def add_participant(
        self, 
        case_id: str, 
        user_id: str, 
        role: str = "collaborator"
    ) -> bool:
        """
        Add a participant to a case.
        
        Args:
            case_id: The ID of the case
            user_id: The ID of the user to add as a participant
            role: The role of the participant
            
        Returns:
            bool: True if the participant was added, False if they were already a participant
        """
        from sqlalchemy import insert
        
        # Check if the participant already exists
        query = select(case_participants).where(
            (case_participants.c.case_id == case_id) & 
            (case_participants.c.user_id == user_id)
        )
        
        result = await self.db_session.execute(query)
        if result.scalar_one_or_none() is not None:
            return False  # Participant already exists
        
        # Add the participant
        stmt = insert(case_participants).values(
            case_id=case_id,
            user_id=user_id,
            role=role
        )
        
        await self.db_session.execute(stmt)
        await self.db_session.commit()
        return True
    
    async def remove_participant(self, case_id: str, user_id: str) -> bool:
        """
        Remove a participant from a case.
        
        Args:
            case_id: The ID of the case
            user_id: The ID of the user to remove as a participant
            
        Returns:
            bool: True if the participant was removed, False if they weren't a participant
        """
        from sqlalchemy import delete
        
        stmt = delete(case_participants).where(
            (case_participants.c.case_id == case_id) & 
            (case_participants.c.user_id == user_id)
        )
        
        result = await self.db_session.execute(stmt)
        await self.db_session.commit()
        return result.rowcount > 0


class CaseRepositorySync(CaseRepository, BaseRepositorySync[Case, CaseCreate, CaseUpdate]):
    """
    Synchronous repository for Case model.
    """
    
    def __init__(self, db_session: Session):
        super().__init__(db_session)
