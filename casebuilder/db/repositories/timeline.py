"""
Timeline event repository implementation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel
from sqlalchemy import and_, delete, insert, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload, selectinload

from ...models import TimelineEventCreate, TimelineEventUpdate
from ..models import TimelineEvent, TimelineEventType, timeline_event_evidence
from .base import BaseRepository, BaseRepositoryAsync, BaseRepositorySync


class TimelineEventRepository(
    BaseRepository[TimelineEvent, TimelineEventCreate, TimelineEventUpdate]
):
    """
    Repository for TimelineEvent model with common CRUD operations.
    """

    def __init__(self, db_session: Union[Session, AsyncSession]):
        super().__init__(TimelineEvent, db_session)

    async def search(
        self, query: str, *, skip: int = 0, limit: int = 100, **filters
    ) -> List[TimelineEvent]:
        """
        Search timeline events by title or description.

        Args:
            query: Search query string
            skip: Number of records to skip
            limit: Maximum number of records to return
            **filters: Additional filter criteria

        Returns:
            List[TimelineEvent]: List of matching timeline events
        """
        search_condition = or_(
            TimelineEvent.title.ilike(f"%{query}%"), TimelineEvent.description.ilike(f"%{query}%")
        )

        query_obj = select(TimelineEvent).where(search_condition).offset(skip).limit(limit)

        # Apply additional filters
        for key, value in filters.items():
            if hasattr(TimelineEvent, key):
                if isinstance(value, (list, tuple)):
                    query_obj = query_obj.where(getattr(TimelineEvent, key).in_(value))
                else:
                    query_obj = query_obj.where(getattr(TimelineEvent, key) == value)

        if self.is_async:
            result = await self.db_session.execute(query_obj)
        else:
            result = self.db_session.execute(query_obj)

        return result.scalars().all()

    async def get_by_case(
        self, case_id: str, *, skip: int = 0, limit: int = 100, **filters
    ) -> List[TimelineEvent]:
        """
        Get timeline events by case ID.

        Args:
            case_id: ID of the case
            skip: Number of records to skip
            limit: Maximum number of records to return
            **filters: Additional filter criteria

        Returns:
            List[TimelineEvent]: List of timeline events for the case
        """
        filters["case_id"] = case_id
        return await self.get_multi(skip=skip, limit=limit, **filters)

    async def get_by_type(
        self, event_type: TimelineEventType, *, skip: int = 0, limit: int = 100
    ) -> List[TimelineEvent]:
        """
        Get timeline events by type.

        Args:
            event_type: Event type to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[TimelineEvent]: List of timeline events of the specified type
        """
        return await self.get_multi(event_type=event_type, skip=skip, limit=limit)

    async def get_upcoming_events(
        self, *, days_ahead: int = 7, skip: int = 0, limit: int = 100
    ) -> List[TimelineEvent]:
        """
        Get upcoming timeline events within the specified number of days.

        Args:
            days_ahead: Number of days to look ahead
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[TimelineEvent]: List of upcoming timeline events
        """
        from sqlalchemy import select
        from datetime import datetime, timedelta

        now = datetime.utcnow()
        end_date = now + timedelta(days=days_ahead)

        query = (
            select(TimelineEvent)
            .where(TimelineEvent.event_date.between(now, end_date))
            .order_by(TimelineEvent.event_date)
            .offset(skip)
            .limit(limit)
        )

        if self.is_async:
            result = await self.db_session.execute(query)
        else:
            result = self.db_session.execute(query)

        return result.scalars().all()


class TimelineEventRepositoryAsync(
    TimelineEventRepository,
    BaseRepositoryAsync[TimelineEvent, TimelineEventCreate, TimelineEventUpdate],
):
    """
    Async repository for TimelineEvent model with additional async methods.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)

    async def get_with_related(
        self,
        event_id: str,
        load_case: bool = True,
        load_created_by: bool = True,
        load_evidence: bool = False,
    ) -> Optional[TimelineEvent]:
        """
        Get a timeline event with related models loaded.

        Args:
            event_id: The ID of the timeline event to retrieve
            load_case: Whether to load the related case
            load_created_by: Whether to load the user who created the event
            load_evidence: Whether to load related evidence

        Returns:
            Optional[TimelineEvent]: The timeline event with related models if found
        """
        from sqlalchemy import select

        query = select(TimelineEvent).where(TimelineEvent.id == event_id)

        # Add relationship loading
        if load_case:
            query = query.options(joinedload(TimelineEvent.case))
        if load_created_by:
            query = query.options(joinedload(TimelineEvent.created_by))
        if load_evidence:
            query = query.options(selectinload(TimelineEvent.evidence))

        result = await self.db_session.execute(query)
        return result.unique().scalar_one_or_none()

    async def add_evidence(self, event_id: str, evidence_id: str) -> bool:
        """
        Add evidence to a timeline event.

        Args:
            event_id: The ID of the timeline event
            evidence_id: The ID of the evidence to add

        Returns:
            bool: True if the evidence was added to the timeline event
        """
        # Check if the relationship already exists
        query = select(timeline_event_evidence).where(
            (timeline_event_evidence.c.timeline_event_id == event_id)
            & (timeline_event_evidence.c.evidence_id == evidence_id)
        )

        result = await self.db_session.execute(query)
        if result.scalar_one_or_none() is not None:
            return True  # Already associated

        # Add the relationship
        stmt = insert(timeline_event_evidence).values(
            timeline_event_id=event_id, evidence_id=evidence_id
        )

        await self.db_session.execute(stmt)
        await self.db_session.commit()
        return True

    async def remove_evidence(self, event_id: str, evidence_id: str) -> bool:
        """
        Remove evidence from a timeline event.

        Args:
            event_id: The ID of the timeline event
            evidence_id: The ID of the evidence to remove

        Returns:
            bool: True if the evidence was removed from the timeline event
        """
        stmt = delete(timeline_event_evidence).where(
            (timeline_event_evidence.c.timeline_event_id == event_id)
            & (timeline_event_evidence.c.evidence_id == evidence_id)
        )

        result = await self.db_session.execute(stmt)
        await self.db_session.commit()
        return result.rowcount > 0

    async def get_timeline_for_case(
        self,
        case_id: str,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[TimelineEventType]] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TimelineEvent]:
        """
        Get a timeline of events for a case with optional filtering.

        Args:
            case_id: The ID of the case
            start_date: Optional start date filter
            end_date: Optional end date filter
            event_types: Optional list of event types to include
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[TimelineEvent]: List of timeline events matching the criteria
        """
        from sqlalchemy import select

        query = select(TimelineEvent).where(TimelineEvent.case_id == case_id)

        # Apply date filters
        if start_date:
            query = query.where(TimelineEvent.event_date >= start_date)
        if end_date:
            query = query.where(TimelineEvent.event_date <= end_date)

        # Apply event type filter
        if event_types:
            query = query.where(TimelineEvent.event_type.in_(event_types))

        # Order by date and apply pagination
        query = query.order_by(TimelineEvent.event_date).offset(skip).limit(limit)

        # Execute the query
        result = await self.db_session.execute(query)
        return list(result.scalars().all())


class TimelineEventRepositorySync(
    TimelineEventRepository,
    BaseRepositorySync[TimelineEvent, TimelineEventCreate, TimelineEventUpdate],
):
    """
    Synchronous repository for TimelineEvent model.
    """

    def __init__(self, db_session: Session):
        super().__init__(db_session)
