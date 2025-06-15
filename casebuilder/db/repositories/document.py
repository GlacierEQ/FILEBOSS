"""
Document repository implementation.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel
from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload, selectinload

from ....schemas.document import DocumentCreate, DocumentUpdate
from ...models import Document, DocumentStatus, DocumentType, Case, User, Tag
from .base import BaseRepository, BaseRepositoryAsync, BaseRepositorySync


class DocumentRepository(BaseRepository[Document, DocumentCreate, DocumentUpdate]):
    """
    Repository for Document model with common CRUD operations.
    """
    
    def __init__(self, db_session: Union[Session, AsyncSession]):
        super().__init__(Document, db_session)
    
    async def search(
        self,
        query: str,
        *,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[Document]:
        """
        Search documents by title, description, or content.
        
        Args:
            query: Search query string
            skip: Number of records to skip
            limit: Maximum number of records to return
            **filters: Additional filter criteria
            
        Returns:
            List[Document]: List of matching documents
        """
        search_condition = or_(
            Document.title.ilike(f"%{query}%"),
            Document.description.ilike(f"%{query}%"),
            Document.content.ilike(f"%{query}%")
        )
        
        query_obj = select(Document).where(search_condition).offset(skip).limit(limit)
        
        # Apply additional filters
        for key, value in filters.items():
            if hasattr(Document, key):
                if isinstance(value, (list, tuple)):
                    query_obj = query_obj.where(getattr(Document, key).in_(value))
                else:
                    query_obj = query_obj.where(getattr(Document, key) == value)
        
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
    ) -> List[Document]:
        """
        Get documents by case ID.
        
        Args:
            case_id: ID of the case
            skip: Number of records to skip
            limit: Maximum number of records to return
            **filters: Additional filter criteria
            
        Returns:
            List[Document]: List of documents for the case
        """
        filters["case_id"] = case_id
        return await self.get_multi(
            skip=skip,
            limit=limit,
            **filters
        )
    
    async def get_by_type(
        self, 
        doc_type: DocumentType, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Document]:
        """
        Get documents by type.
        
        Args:
            doc_type: Document type to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Document]: List of documents of the specified type
        """
        return await self.get_multi(
            document_type=doc_type,
            skip=skip,
            limit=limit
        )
    
    async def get_by_status(
        self, 
        status: DocumentStatus, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Document]:
        """
        Get documents by status.
        
        Args:
            status: Document status to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Document]: List of documents with the specified status
        """
        return await self.get_multi(
            status=status,
            skip=skip,
            limit=limit
        )


class DocumentRepositoryAsync(DocumentRepository, BaseRepositoryAsync[Document, DocumentCreate, DocumentUpdate]):
    """
    Async repository for Document model with additional async methods.
    """
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
    
    async def get_with_related(
        self, 
        document_id: str,
        load_case: bool = True,
        load_uploaded_by: bool = True,
        load_tags: bool = True
    ) -> Optional[Document]:
        """
        Get a document with related models loaded.
        
        Args:
            document_id: The ID of the document to retrieve
            load_case: Whether to load the related case
            load_uploaded_by: Whether to load the user who uploaded the document
            load_tags: Whether to load document tags
            
        Returns:
            Optional[Document]: The document with related models if found
        """
        from sqlalchemy import select
        
        query = select(Document).where(Document.id == document_id)
        
        # Add relationship loading
        if load_case:
            query = query.options(joinedload(Document.case))
        if load_uploaded_by:
            query = query.options(joinedload(Document.uploaded_by))
        if load_tags:
            query = query.options(selectinload(Document.tags))
        
        result = await self.db_session.execute(query)
        return result.unique().scalar_one_or_none()
    
    async def add_tag(self, document_id: str, tag_id: str) -> bool:
        """
        Add a tag to a document.
        
        Args:
            document_id: The ID of the document
            tag_id: The ID of the tag to add
            
        Returns:
            bool: True if the tag was added, False if it was already associated
        """
        from sqlalchemy import select, insert
        
        # Check if the tag is already associated
        query = select(document_tags).where(
            (document_tags.c.document_id == document_id) & 
            (document_tags.c.tag_id == tag_id)
        )
        
        result = await self.db_session.execute(query)
        if result.scalar_one_or_none() is not None:
            return False  # Tag already associated
        
        # Add the tag
        stmt = insert(document_tags).values(
            document_id=document_id,
            tag_id=tag_id
        )
        
        await self.db_session.execute(stmt)
        await self.db_session.commit()
        return True
    
    async def remove_tag(self, document_id: str, tag_id: str) -> bool:
        """
        Remove a tag from a document.
        
        Args:
            document_id: The ID of the document
            tag_id: The ID of the tag to remove
            
        Returns:
            bool: True if the tag was removed, False if it wasn't associated
        """
        from sqlalchemy import delete
        
        stmt = delete(document_tags).where(
            (document_tags.c.document_id == document_id) & 
            (document_tags.c.tag_id == tag_id)
        )
        
        result = await self.db_session.execute(stmt)
        await self.db_session.commit()
        return result.rowcount > 0
    
    async def get_document_versions(self, document_id: str) -> List[Document]:
        """
        Get all versions of a document.
        
        Args:
            document_id: The ID of the document (can be any version)
            
        Returns:
            List[Document]: List of document versions in chronological order
        """
        from sqlalchemy import select
        
        # First, find the root document (the original version)
        query = select(Document).where(Document.id == document_id)
        result = await self.db_session.execute(query)
        doc = result.scalar_one_or_none()
        
        if not doc:
            return []
        
        # If this is a version, find the root document
        while doc.parent_id is not None:
            query = select(Document).where(Document.id == doc.parent_id)
            result = await self.db_session.execute(query)
            doc = result.scalar_one()
        
        # Now get all versions (including the root)
        versions_query = (
            select(Document)
            .where(
                or_(
                    Document.id == doc.id,
                    Document.parent_id == doc.id
                )
            )
            .order_by(Document.created_at)
        )
        
        result = await self.db_session.execute(versions_query)
        return list(result.scalars().all())


class DocumentRepositorySync(DocumentRepository, BaseRepositorySync[Document, DocumentCreate, DocumentUpdate]):
    """
    Synchronous repository for Document model.
    """
    
    def __init__(self, db_session: Session):
        super().__init__(db_session)
