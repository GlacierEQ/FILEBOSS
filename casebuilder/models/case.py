""
Case and Subcase Models

This module contains the SQLAlchemy models for cases and subcases.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, Integer, Boolean, Table
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base

class Case(Base):
    """Model representing a case in the system."""
    
    __tablename__ = "cases"
    
    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="open")  # open, closed, archived
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(128), nullable=True)
    assigned_to = Column(String(128), nullable=True)
    
    # Relationships
    subcases = relationship("Subcase", back_populates="case", cascade="all, delete-orphan")
    files = relationship("File", back_populates="case")
    
    def __repr__(self):
        return f"<Case(id='{self.id}', title='{self.title}')>"


class Subcase(Base):
    """Model representing a subcase within a case."""
    
    __tablename__ = "subcases"
    
    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="open")  # open, in_progress, closed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    case = relationship("Case", back_populates="subcases")
    files = relationship("File", back_populates="subcase")
    
    def __repr__(self):
        return f"<Subcase(id='{self.id}', title='{self.title}', case_id='{self.case_id}')>"
