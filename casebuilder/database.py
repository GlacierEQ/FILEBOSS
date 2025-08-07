# casebuilder/database.py - All database configuration and setup

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Define the database URL. For local dev, we use a simple SQLite file.
# This creates a file named `casebuilder.db` in the project root.
DATABASE_URL = "sqlite+aiosqlite:///./casebuilder.db"

# Create the SQLAlchemy engine
# `connect_args` is needed for SQLite to allow it to be used in a multi-threaded async environment
engine = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a sessionmaker, which will be our factory for new database sessions
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Create a Base class for our models to inherit from
Base = declarative_base()

# Dependency to get a DB session in our API endpoints
async def get_db():
    async with SessionLocal() as session:
        yield session
