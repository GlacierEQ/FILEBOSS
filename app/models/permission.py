"""Permission model for fine-grained access control."""
from typing import List, Optional

from sqlalchemy import Column, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


# Association table for user-permission many-to-many relationship
user_permission = Table(
    "user_permission",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", UUID(as_uuid=True), ForeignKey("permission.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)

# Association table for group-permission many-to-many relationship
group_permission = Table(
    "group_permission",
    Base.metadata,
    Column("group_id", UUID(as_uuid=True), ForeignKey("group.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", UUID(as_uuid=True), ForeignKey("permission.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)


class Permission(Base):
    """Permission model for fine-grained access control."""
    
    __tablename__ = "permissions"
    
    name = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique name of the permission (e.g., 'files:read')",
    )
    
    description = Column(
        Text,
        nullable=True,
        doc="Human-readable description of what this permission allows",
    )
    
    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_permission,
        back_populates="permissions",
        lazy="selectin",
    )
    
    groups: Mapped[List["Group"]] = relationship(
        "Group",
        secondary=group_permission,
        back_populates="permissions",
        lazy="selectin",
    )
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint('name', name='uq_permission_name'),
    )
    
    def __str__(self) -> str:
        """String representation of the permission."""
        return self.name
    
    @classmethod
    def create_default_permissions(cls, db: Session) -> None:
        """Create default permissions if they don't exist."""
        default_permissions = [
            # File permissions
            ("files:read", "Read access to files"),
            ("files:write", "Write access to files"),
            ("files:delete", "Delete files"),
            ("files:share", "Share files with others"),
            ("files:download", "Download files"),
            ("files:upload", "Upload files"),
            
            # Directory permissions
            ("directories:list", "List directory contents"),
            ("directories:create", "Create directories"),
            ("directories:delete", "Delete directories"),
            ("directories:rename", "Rename directories"),
            ("directories:move", "Move directories"),
            ("directories:share", "Share directories"),
            
            # User management
            ("users:read", "View user information"),
            ("users:create", "Create new users"),
            ("users:edit", "Edit user information"),
            ("users:delete", "Delete users"),
            ("users:manage_roles", "Manage user roles and permissions"),
            
            # Admin permissions
            ("admin:all", "Full administrative access"),
            ("admin:audit", "View audit logs"),
            ("admin:settings", "Modify system settings"),
            
            # WebSocket permissions
            ("websocket:connect", "Connect to WebSocket"),
            ("websocket:notifications", "Receive notifications"),
            ("websocket:file_events", "Receive file system events"),
        ]
        
        for name, description in default_permissions:
            permission = db.query(cls).filter_by(name=name).first()
            if not permission:
                permission = cls(name=name, description=description)
                db.add(permission)
        
        db.commit()


# Create a function to check if a user has a specific permission
def has_permission(user: Optional[User], permission_name: str) -> bool:
    """Check if a user has a specific permission."""
    if not user:
        return False
    return user.has_permission(permission_name)


# Create a function to check if a user has any of the specified permissions
def has_any_permission(user: Optional[User], *permission_names: str) -> bool:
    """Check if a user has any of the specified permissions."""
    if not user:
        return False
    return user.has_any_permission(*permission_names)
