"""User model for authentication and authorization."""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.models.base import Base
from app.models.permission import Permission


# Association table for user-group many-to-many relationship
user_group = Table(
    "user_group",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
    Column("group_id", UUID(as_uuid=True), ForeignKey("group.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)


class User(Base):
    """User account model for authentication and authorization."""
    
    __tablename__ = "users"
    
    # Authentication fields
    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        doc="User's email address, used for login",
    )
    hashed_password = Column(
        String(255),
        nullable=False,
        doc="Hashed password using bcrypt",
    )
    is_active = Column(
        Boolean(),
        default=True,
        nullable=False,
        doc="Whether the user account is active",
    )
    is_superuser = Column(
        Boolean(),
        default=False,
        nullable=False,
        doc="Whether the user has superuser privileges",
    )
    is_verified = Column(
        Boolean(),
        default=False,
        nullable=False,
        doc="Whether the user's email has been verified",
    )
    
    # Profile fields
    full_name = Column(
        String(255),
        nullable=True,
        doc="User's full name",
    )
    
    # Timestamps for security-related events
    last_login = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of the user's last login",
    )
    password_changed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when the password was last changed",
    )
    
    # Relationships
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary="user_permission",
        back_populates="users",
        lazy="selectin",
    )
    
    groups: Mapped[List["Group"]] = relationship(
        "Group",
        secondary=user_group,
        back_populates="users",
        lazy="selectin",
    )
    
    # Files and directories owned by this user
    files: Mapped[List["File"]] = relationship("File", back_populates="owner")
    directories: Mapped[List["Directory"]] = relationship("Directory", back_populates="owner")
    
    # Methods
    def __str__(self) -> str:
        """String representation of the user."""
        return self.email
    
    @property
    def is_authenticated(self) -> bool:
        """Check if the user is authenticated."""
        return self.is_active
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if the user has a specific permission."""
        if self.is_superuser:
            return True
            
        return any(perm.name == permission_name for perm in self.permissions) or any(
            perm.name == permission_name 
            for group in self.groups 
            for perm in group.permissions
        )
    
    def has_any_permission(self, *permission_names: str) -> bool:
        """Check if the user has any of the specified permissions."""
        if self.is_superuser:
            return True
            
        user_permissions = {perm.name for perm in self.permissions}
        group_permissions = {
            perm.name 
            for group in self.groups 
            for perm in group.permissions
        }
        all_permissions = user_permissions.union(group_permissions)
        
        return any(perm in all_permissions for perm in permission_names)
    
    def update_last_login(self) -> None:
        """Update the last login timestamp."""
        self.last_login = datetime.utcnow()
    
    def update_password(self, hashed_password: str) -> None:
        """Update the user's password and set the password changed timestamp."""
        self.hashed_password = hashed_password
        self.password_changed_at = datetime.utcnow()


class Group(Base):
    """Group model for role-based access control."""
    
    __tablename__ = "groups"
    
    name = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        doc="Name of the group",
    )
    description = Column(
        String(255),
        nullable=True,
        doc="Description of the group's purpose",
    )
    
    # Relationships
    users: Mapped[List[User]] = relationship(
        "User",
        secondary=user_group,
        back_populates="groups",
        lazy="selectin",
    )
    
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary="group_permission",
        back_populates="groups",
        lazy="selectin",
    )
    
    def __str__(self) -> str:
        """String representation of the group."""
        return self.name
