"""
Evidence repository implementation.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel
from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload, selectinload

from casebuilder.schemas.evidence import EvidenceCreate, EvidenceUpdate
from ..models import Evidence, EvidenceStatus, EvidenceType, Case, Document, Tag
from .base import BaseRepository, BaseRepositoryAsync, BaseRepositorySync


class EvidenceRepository(BaseRepository[Evidence, EvidenceCreate, EvidenceUpdate]):
    """
    Repository for Evidence model with common CRUD operations.
    """
    
    def __init__(self, db_session: Union[Session, AsyncSession]):
        super().__init__(Evidence, db_session)
    
    async def search(
        self,
        query: str,
        *,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[Evidence]:
        """
        Search evidence by title, description, or notes.
        
        Args:
            query: Search query string
            skip: Number of records to skip
            limit: Maximum number of records to return
            **filters: Additional filter criteria
            
        Returns:
            List[Evidence]: List of matching evidence items
        """
        search_condition = or_(
            Evidence.title.ilike(f"%{query}%"),
            Evidence.description.ilike(f"%{query}%"),
            Evidence.notes.ilike(f"%{query}%")
        )
        
        query_obj = select(Evidence).where(search_condition).offset(skip).limit(limit)
        
        # Apply additional filters
        for key, value in filters.items():
            if hasattr(Evidence, key):
                if isinstance(value, (list, tuple)):
                    query_obj = query_obj.where(getattr(Evidence, key).in_(value))
                else:
                    query_obj = query_obj.where(getattr(Evidence, key) == value)
        
        if self.is_async:
            result = await self.db_session.execute(query_obj)
        else:
            result = self.db_session.execute(query_obj)
            
        return result.scalars().all()
    
    async def get_by_case(
        self, 
        case_id: str, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        **filters
    ) -> List[Evidence]:
        """
        Get evidence by case ID.
        
        Args:
            case_id: ID of the case
            skip: Number of records to skip
            limit: Maximum number of records to return
            **filters: Additional filter criteria
            
        Returns:
            List[Evidence]: List of evidence for the case
        """
        filters["case_id"] = case_id
        return await self.get_multi(
            skip=skip,
            limit=limit,
            **filters
        )
    
    async def get_by_type(
        self, 
        evidence_type: EvidenceType, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Evidence]:
        """
        Get evidence by type.
        
        Args:
            evidence_type: Evidence type to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Evidence]: List of evidence of the specified type
        """
        return await self.get_multi(
            evidence_type=evidence_type,
            skip=skip,
            limit=limit
        )
    
    async def get_by_status(
        self, 
        status: EvidenceStatus, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Evidence]:
        """
        Get evidence by status.
        
        Args:
            status: Evidence status to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Evidence]: List of evidence with the specified status
        """
        return await self.get_multi(
            status=status,
            skip=skip,
            limit=limit
        )


class EvidenceRepositoryAsync(EvidenceRepository, BaseRepositoryAsync[Evidence, EvidenceCreate, EvidenceUpdate]):
    """
    Async repository for Evidence model with additional async methods.
    """
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
    
    async def get_with_related(
        self, 
        evidence_id: str,
        load_case: bool = True,
        load_document: bool = True,
        load_timeline_events: bool = False
    ) -> Optional[Evidence]:
        """
        Get an evidence item with related models loaded.
        
        Args:
            evidence_id: The ID of the evidence to retrieve
            load_case: Whether to load the related case
            load_document: Whether to load the related document
            load_timeline_events: Whether to load related timeline events
            
        Returns:
            Optional[Evidence]: The evidence with related models if found
        """
        from sqlalchemy import select
        
        query = select(Evidence).where(Evidence.id == evidence_id)
        
        # Add relationship loading
        if load_case:
            query = query.options(joinedload(Evidence.case))
        if load_document:
            query = query.options(joinedload(Evidence.document))
        if load_timeline_events:
            query = query.options(selectinload(Evidence.timeline_events))
        
        result = await self.db_session.execute(query)
        return result.unique().scalar_one_or_none()
    
    async def add_to_timeline(
        self, 
        evidence_id: str, 
        timeline_event_id: str
    ) -> bool:
        """
        Add an evidence item to a timeline event.
        
        Args:
            evidence_id: The ID of the evidence
            timeline_event_id: The ID of the timeline event
            
        Returns:
            bool: True if the evidence was added to the timeline event
        """
        from sqlalchemy import select, insert
        
        # Check if the relationship already exists
        query = select(timeline_event_evidence).where(
            (timeline_event_evidence.c.evidence_id == evidence_id) & 
            (timeline_event_evidence.c.timeline_event_id == timeline_event_id)
        )
        
        result = await self.db_session.execute(query)
        if result.scalar_one_or_none() is not None:
            return True  # Already associated
        
        # Add the relationship
        stmt = insert(timeline_event_evidence).values(
            evidence_id=evidence_id,
            timeline_event_id=timeline_event_id
        )
        
        await self.db_session.execute(stmt)
        await self.db_session.commit()
        return True
    
    async def remove_from_timeline(
        self, 
        evidence_id: str, 
        timeline_event_id: str
    ) -> bool:
        """
        Remove an evidence item from a timeline event.
        
        Args:
            evidence_id: The ID of the evidence
            timeline_event_id: The ID of the timeline event
            
        Returns:
            bool: True if the evidence was removed from the timeline event
        """
        from sqlalchemy import delete
        
        stmt = delete(timeline_event_evidence).where(
            (timeline_event_evidence.c.evidence_id == evidence_id) & 
            (timeline_event_evidence.c.timeline_event_id == timeline_event_id)
        )
        
        result = await self.db_session.execute(stmt)
        await self.db_session.commit()
        return result.rowcount > 0
    
    async def get_chain_of_custody(self, evidence_id: str) -> List[Dict[str, Any]]:
        """
        Get the chain of custody for an evidence item.
        
        Args:
            evidence_id: The ID of the evidence
            
        Returns:
            List[Dict[str, Any]]: List of custody events in chronological order
        """
        from sqlalchemy import select
        
        query = select(Evidence).where(Evidence.id == evidence_id)
        result = await self.db_session.execute(query)
        evidence = result.scalar_one_or_none()
        
        if not evidence:
            return []
        
        # The chain of custody is stored as a JSON field
        return evidence.chain_of_custody or []
    
    async def add_custody_event(
        self, 
        evidence_id: str, 
        event: Dict[str, Any],
        user_id: str
    ) -> bool:
        """
        Add a custody event to an evidence item's chain of custody.
        
        Args:
            evidence_id: The ID of the evidence
            event: The custody event data
            user_id: The ID of the user making the change
            
        Returns:
            bool: True if the event was added
        """
        from sqlalchemy import select, update
        
        # Get the current chain of custody
        query = select(Evidence).where(Evidence.id == evidence_id)
        result = await self.db_session.execute(query)
        evidence = result.scalar_one_or_none()
        
        if not evidence:
            return False
        
        # Initialize chain of custody if it doesn't exist
        if evidence.chain_of_custody is None:
            evidence.chain_of_custody = []
        
        # Add the new event with timestamp and user
        event.update({
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id
        })
        
        evidence.chain_of_custody.append(event)
        
        # Update the evidence record
        stmt = (
            update(Evidence)
            .where(Evidence.id == evidence_id)
            .values(chain_of_custody=evidence.chain_of_custody)
        )
        
        await self.db_session.execute(stmt)
        await self.db_session.commit()
        return True


class EvidenceRepositorySync(EvidenceRepository, BaseRepositorySync[Evidence, EvidenceCreate, EvidenceUpdate]):
    """
    Synchronous repository for Evidence model.
    """
    
    def __init__(self, db_session: Session):
        super().__init__(db_session)
