from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import declarative_mixin

@declarative_mixin
class BaseMixin:
    """Base mixin for all models"""
    __name__: str
    
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower() + 's'
    
    # Common columns
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def to_dict(self):
        """Convert model instance to dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
