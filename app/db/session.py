"""Database session management."""
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from app.core.config import settings
from app.models.base import Base

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    pool_pre_ping=True,
    pool_size=settings.POOL_SIZE,
    max_overflow=settings.POOL_MAX_OVERFLOW,
    pool_recycle=settings.POOL_RECYCLE,
    pool_timeout=settings.POOL_TIMEOUT,
    echo=settings.SQL_ECHO,
    echo_pool=settings.SQL_ECHO_POOL,
)

# Session factory with thread-local scope
SessionFactory = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=True,
    class_=Session,
)

# Scoped session factory for thread safety
ScopedSession = scoped_session(SessionFactory)

# Dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """
    Dependency function that yields database sessions.
    
    Yields:
        Session: A SQLAlchemy database session.
    """
    db: Optional[Session] = None
    try:
        db = ScopedSession()
        yield db
    finally:
        if db is not None:
            db.close()

# Context manager for database sessions
@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    session = ScopedSession()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# Add event listeners for better connection handling
@event.listens_for(Engine, "engine_connect")
def ping_connection(dbapi_connection, connection_record, connection_proxy):
    """
    Ping the database connection before using it.
    
    This ensures that the connection is still alive and reconnects if necessary.
    """
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SELECT 1")
        cursor.close()
    except Exception as e:
        cursor.close()
        raise Exception("Database connection ping failed") from e


@event.listens_for(Engine, "checkout")
def check_connection(dbapi_connection, connection_record, connection_proxy):
    """Check if the connection is still valid before using it."""
    if getattr(settings, "SQLALCHEMY_ENGINE_OPTIONS", {}).get("pool_pre_ping", True):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("SELECT 1")
            cursor.close()
        except Exception as e:
            cursor.close()
            raise Exception("Database connection check failed") from e

# Initialize database
def init_db() -> None:
    """
    Initialize the database by creating all tables.
    
    This should be called during application startup.
    """
    import logging
    from app.models.permission import Permission
    from app.models.user import User
    
    # Configure logger
    logger = logging.getLogger(__name__)
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Create default permissions and admin user if they don't exist
        with session_scope() as db:
            # Create default permissions
            Permission.create_default_permissions(db)
            
            # Create admin user if it doesn't exist
            admin_email = settings.FIRST_SUPERUSER_EMAIL
            admin_password = settings.FIRST_SUPERUSER_PASSWORD
            
            if admin_email and admin_password:
                admin = db.query(User).filter(User.email == admin_email).first()
                if not admin:
                    from app.core.security import get_password_hash
                    
                    admin = User(
                        email=admin_email,
                        hashed_password=get_password_hash(admin_password),
                        full_name="Admin User",
                        is_superuser=True,
                        is_verified=True,
                        is_active=True,
                    )
                    db.add(admin)
                    db.commit()
                    db.refresh(admin)
                    logger.info(f"Created admin user: {admin_email}")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise
