"""
Database session management and dependency injection.
"""
from typing import AsyncGenerator, Generator

from sqlalchemy.ext.asyncio import AsyncSession

from .base import SessionLocal, AsyncSessionLocal


def get_db() -> Generator:
    """
    Dependency function that yields database sessions.
    
    Yields:
        Session: A SQLAlchemy database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async dependency function that yields async database sessions.
    
    Yields:
        AsyncSession: An async SQLAlchemy database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class DatabaseManager:
    """
    A context manager for database sessions.
    
    Example:
        with DatabaseManager() as db:
            # Use the database session
            result = db.query(...)
    """
    
    def __init__(self, async_session: bool = False):
        """
        Initialize the database manager.
        
        Args:
            async_session: If True, use an async session.
        """
        self.async_session = async_session
        self.session = None
    
    def __enter__(self):
        """Enter the context and return a database session."""
        if self.async_session:
            raise RuntimeError("Use 'async with' for async sessions")
        self.session = SessionLocal()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and close the session."""
        if self.session is not None:
            if exc_type is not None:
                self.session.rollback()
            self.session.close()
    
    async def __aenter__(self):
        """Asynchronously enter the context and return an async database session."""
        if not self.async_session:
            raise RuntimeError("Use 'with' for sync sessions")
        self.session = AsyncSessionLocal()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Asynchronously exit the context and close the session."""
        if self.session is not None:
            if exc_type is not None:
                await self.session.rollback()
            await self.session.close()
