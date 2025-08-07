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

from ..config import settings

# Create base class for SQLAlchemy models
Base = declarative_base()

# Create database engines
engine = create_engine(
    settings.database.url,
    echo=settings.database.echo,
    # SQLite doesn't support pool_size and max_overflow in the same way as other databases
    # These parameters are removed for SQLite compatibility
)

async_engine = create_async_engine(
    settings.database.url.replace("sqlite", "sqlite+aiosqlite"),
    echo=settings.database.echo,
    # aiosqlite doesn't support pool_size and max_overflow
    # These parameters are removed for aiosqlite compatibility
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
    Base.metadata.create_all(bind=engine)


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
