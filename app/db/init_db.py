from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import base  # noqa: F401
from app.db.session import engine, Base
from app.models.user import User
from app.core.security import get_password_hash

def init_db(db: Session) -> None:
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Create first superuser
    user = db.query(User).filter(User.email == settings.FIRST_SUPERUSER_EMAIL).first()
    if not user:
        user_in = {
            "email": settings.FIRST_SUPERUSER_EMAIL,
            "password": settings.FIRST_SUPERUSER_PASSWORD,
            "is_superuser": True,
            "is_active": True,
        }
        user = User(
            email=user_in["email"],
            hashed_password=get_password_hash(user_in["password"]),
            is_superuser=user_in["is_superuser"],
            is_active=user_in["is_active"],
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print("Superuser created:", user.email)
    else:
        print("Superuser already exists:", user.email)

if __name__ == "__main__":
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
