from sqlalchemy import Boolean, Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import BaseMixin
from app.db.session import Base

class User(Base, BaseMixin):
    """User model for authentication and authorization"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    items = relationship("Item", back_populates="owner")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"

class Item(Base, BaseMixin):
    """Example item model"""
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, index=True, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    owner = relationship("User", back_populates="items")
    
    def __repr__(self):
        return f"<Item(id={self.id}, title='{self.title}')>"
