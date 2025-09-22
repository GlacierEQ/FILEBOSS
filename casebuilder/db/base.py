"""Database configuration and session management helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL, make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, declarative_base, sessionmaker

try:  # pragma: no cover - optional configuration module
    from casebuilder.config import settings as app_settings  # type: ignore
except Exception:  # pragma: no cover - settings module may not exist
    app_settings = None  # type: ignore

try:  # pragma: no cover - optional configuration module
    from casebuilder.core.config import settings as core_settings  # type: ignore
except Exception:  # pragma: no cover
    core_settings = None  # type: ignore


Base = declarative_base()


def _resolve_database_url() -> str:
    """Resolve the database URL from environment or configuration."""

    for key in ("DATABASE_URL", "DATABASE_URI"):
        value = os.getenv(key)
        if value:
            return value

    if app_settings is not None:
        database_settings = getattr(app_settings, "database", None)
        if database_settings and getattr(database_settings, "url", None):
            return database_settings.url

    if core_settings is not None:
        for attr in ("DATABASE_URL", "DATABASE_URI"):
            if hasattr(core_settings, attr):
                return getattr(core_settings, attr)

    return "sqlite+aiosqlite:///./casebuilder.db"


def _ensure_sqlite_directory(url: URL) -> None:
    """Ensure directories exist for SQLite database files."""

    if url.drivername.startswith("sqlite") and url.database:
        db_path = Path(url.database)
        if not db_path.is_absolute():
            db_path = Path.cwd() / db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)


def _build_async_url(url: URL) -> URL:
    """Return an async-compatible SQLAlchemy URL."""

    driver = url.drivername
    if driver.startswith("sqlite") and "aiosqlite" not in driver:
        return url.set(drivername="sqlite+aiosqlite")
    if driver.startswith("postgresql") and "asyncpg" not in driver:
        return url.set(drivername="postgresql+asyncpg")
    if driver.startswith("mysql") and "asyncmy" not in driver and "aiomysql" not in driver:
        return url.set(drivername="mysql+asyncmy")
    return url


def _build_sync_url(url: URL) -> URL:
    """Return a sync-compatible SQLAlchemy URL."""

    driver = url.drivername
    if driver.endswith("+aiosqlite"):
        return url.set(drivername="sqlite")
    if driver.endswith("+asyncpg"):
        return url.set(drivername="postgresql")
    if driver.endswith("+asyncmy"):
        return url.set(drivername="mysql+pymysql")
    if driver.endswith("+aiomysql"):
        return url.set(drivername="mysql")
    return url


DATABASE_URL = _resolve_database_url()
_base_url = make_url(DATABASE_URL)
async_url = _build_async_url(_base_url)
sync_url = _build_sync_url(_base_url)

_ensure_sqlite_directory(sync_url)

async_connect_args = (
    {"check_same_thread": False} if async_url.drivername.startswith("sqlite") else {}
)
sync_connect_args = {"check_same_thread": False} if sync_url.drivername.startswith("sqlite") else {}

async_engine: AsyncEngine = create_async_engine(
    str(async_url),
    echo=False,
    future=True,
    connect_args=async_connect_args,
)

engine: Engine = create_engine(
    str(sync_url),
    echo=False,
    future=True,
    connect_args=sync_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session."""

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Compatibility wrapper returning an async session generator."""

    async for session in get_async_session():
        yield session


def get_db() -> Generator[Session, None, None]:
    """Provide a synchronous database session."""

    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Create database tables for registered models."""

    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


__all__ = [
    "Base",
    "DATABASE_URL",
    "engine",
    "async_engine",
    "SessionLocal",
    "AsyncSessionLocal",
    "get_db",
    "get_async_db",
    "get_async_session",
    "init_db",
]
