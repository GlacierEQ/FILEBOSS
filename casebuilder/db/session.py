"""
Database Session Management

This module handles database connections and session management.
"""
import logging
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    async_scoped_session,
)
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

from ..core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create base class for SQLAlchemy models
Base = declarative_base()

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URI,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
)

# Create session factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Create scoped session factory
async_scoped_session_factory = async_scoped_session(
    session_factory=async_session_factory,
    scopefunc=lambda: None,  # Will be set by FastAPI dependency
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function that yields db sessions.
    
    Yields:
        AsyncSession: An async database session
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database error: {e}", exc_info=True)
            raise
        finally:
            await session.close()

async def get_scoped_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a scoped database session.
    
    Yields:
        AsyncSession: A scoped async database session
    """
    session = async_scoped_session_factory()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Database error: {e}", exc_info=True)
        raise
    finally:
        await session.close()

async def init_db() -> None:
    """Initialize the database."""
    logger.info("Initializing database...")
    
    # Import models to ensure they are registered with SQLAlchemy
    from ..models import Base  # noqa: F401
    
    async with engine.begin() as conn:
        # Create tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database initialized successfully")

async def close_db() -> None:
    """Close database connections."""
    logger.info("Closing database connections...")
    if engine:
        await engine.dispose()
    logger.info("Database connections closed")
