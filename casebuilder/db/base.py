"""
Database base configuration and session management.
"""
import contextlib
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession, 
    async_sessionmaker, 
    create_async_engine
)
from sqlalchemy.orm import declarative_base, sessionmaker

from ..core.config import settings

# Create base class for SQLAlchemy models
Base = declarative_base()

# Create database engines
# For SQLite, we need to use a file-based database
sqlite_url = settings.DATABASE_URI
if sqlite_url.startswith("sqlite"):
    # Ensure the SQLite database is created in a known location
    sqlite_url = sqlite_url.replace("sqlite:///", "sqlite:///./")
    
engine = create_engine(
    sqlite_url,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False} if "sqlite" in sqlite_url else {}
)

# For async operations
async_sqlite_url = sqlite_url.replace("sqlite", "sqlite+aiosqlite")
async_engine = create_async_engine(
    async_sqlite_url,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False} if "sqlite" in async_sqlite_url else {}
)

# Session factories
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Dependency to get DB session
def get_db() -> Generator:
    """Get a synchronous database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get an asynchronous database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Initialize database tables
def init_db() -> None:
    """Initialize the database by creating all tables."""
    # Import models to ensure they are registered with SQLAlchemy
    from . import models  # noqa: F401
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create the SQLite database file if it doesn't exist
    if "sqlite" in settings.DATABASE_URI:
        import os
        from pathlib import Path
        
        # Ensure the directory exists
        db_path = settings.DATABASE_URI.split("///")[-1]
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f"Created database directory: {db_dir}")
            
        print(f"Database will be created at: {os.path.abspath(db_path)}")


# Async context manager for database sessions
@contextlib.asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session with auto-commit/rollback."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
