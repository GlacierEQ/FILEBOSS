""
Base Model

This module contains the base SQLAlchemy model and database session configuration.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from typing import Generator
import os

from ...config import settings

# Create database engine
DATABASE_URL = settings.DATABASE_URL or "sqlite:///./casebuilder.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create scoped session factory
SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

# Base class for all models
Base = declarative_base()

def get_db() -> Generator:
    """Dependency to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    ""
    Initialize the database by creating all tables.
    
    This should be called during application startup.
    ""
    from . import (  # noqa: F401
        case,
        file,
        tag
    )
    
    Base.metadata.create_all(bind=engine)
