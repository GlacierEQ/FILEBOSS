"""
Base models for APEX MANUS data structures.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4

T = TypeVar('T', bound='BaseModel')

class SyncStatus(str, Enum):
    """Synchronization status of a resource."""
    PENDING = "pending"
    SYNCING = "syncing"
    SYNCED = "synced"
    ERROR = "error"
    CONFLICT = "conflict"

class ResourceType(str, Enum):
    """Types of resources that can be synchronized."""
    DOCUMENT = "document"
    TASK = "task"
    NOTE = "note"
    FILE = "file"
    DATABASE = "database"
    UNKNOWN = "unknown"

class BaseResource(BaseModel):
    """
    Base resource model for all synchronized content.
    
    Attributes:
        id: Unique identifier for the resource
        resource_type: Type of the resource
        source_id: Original ID from the source system
        source_type: Type of the source system
        title: Human-readable title of the resource
        description: Optional description
        metadata: Additional metadata
        created_at: When the resource was created
        updated_at: When the resource was last updated
        sync_status: Current sync status
        version: Version number for optimistic concurrency control
    """
    id: UUID = Field(default_factory=uuid4)
    resource_type: ResourceType = ResourceType.UNKNOWN
    source_id: str
    source_type: str
    title: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    sync_status: SyncStatus = SyncStatus.PENDING
    version: int = 1
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }
    
    @validator('updated_at', pre=True, always=True)
    def set_updated_at(cls, v, values):
        return v or datetime.utcnow()
    
    def mark_synced(self) -> None:
        """Mark the resource as successfully synchronized."""
        self.sync_status = SyncStatus.SYNCED
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def mark_error(self) -> None:
        """Mark the resource as having a sync error."""
        self.sync_status = SyncStatus.ERROR
        self.updated_at = datetime.utcnow()
    
    def update_from(self, other: 'BaseResource') -> None:
        """
        Update this resource with values from another resource.
        
        Args:
            other: The resource to update from
        """
        if self.id != other.id:
            raise ValueError("Cannot update from resource with different ID")
            
        for field in self.__fields__.values():
            if field.name not in {'id', 'created_at', 'version'}:
                setattr(self, field.name, getattr(other, field.name))
        
        self.version += 1
        self.updated_at = datetime.utcnow()

class SyncResult(BaseModel):
    """Result of a synchronization operation."""
    success: bool
    resource_id: UUID
    resource_type: ResourceType
    action: str  # 'created', 'updated', 'deleted', 'skipped', 'error'
    message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SyncBatch(BaseModel):
    """A batch of synchronization results."""
    batch_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str
    target: str
    results: List[SyncResult] = Field(default_factory=list)
    stats: Dict[str, int] = Field(default_factory=dict)
    
    def add_result(self, result: SyncResult) -> None:
        """Add a sync result to the batch."""
        self.results.append(result)
        self.stats[result.action] = self.stats.get(result.action, 0) + 1
    
    @property
    def success_count(self) -> int:
        """Number of successful sync operations."""
        return sum(1 for r in self.results if r.success)
    
    @property
    def error_count(self) -> int:
        """Number of failed sync operations."""
        return sum(1 for r in self.results if not r.success)
