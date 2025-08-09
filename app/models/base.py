"""Base database models and mixins."""
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.core.config import settings


@as_declarative()
class Base:
    """Base model class with common fields and methods."""
    
    # Common fields
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        unique=True,
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="Timestamp of when the record was created",
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp of when the record was last updated",
    )
    
    # Table naming convention
    @declared_attr
    def __tablename__(cls) -> str:
        ""
        Generate table name from class name.
        Converts CamelCase class name to snake_case table name.
        """
        return "".join(
            [
                f"{'_' + c.lower() if c.isupper() else c}"
                for c in cls.__name__
            ]
        ).lstrip("_")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns  # type: ignore
        }
    
    def update(self, **kwargs) -> None:
        """Update model attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"


# Update timestamps before insert and update
@event.listens_for(Session, 'before_flush')
def before_flush(session: Session, *args: Any, **kwargs: Any) -> None:
    """Update timestamps on models before they are flushed to the database."""
    for instance in session.new:
        if hasattr(instance, 'created_at') and not instance.created_at:
            instance.created_at = datetime.utcnow()
        if hasattr(instance, 'updated_at'):
            instance.updated_at = datetime.utcnow()
    
    for instance in session.dirty:
        if hasattr(instance, 'updated_at'):
            instance.updated_at = datetime.utcnow()
