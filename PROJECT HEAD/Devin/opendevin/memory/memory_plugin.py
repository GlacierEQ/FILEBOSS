"""
MemoryPlugin: Base class for memory system plugins

Provides a standardized interface for different memory backends
and plugin functionalities like auto-summarization, contextual recall,
learning adaptation, and memory consolidation.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from opendevin import config

class MemoryItem:
    """Represents a single memory item with metadata"""
    
    def __init__(self, content: str, memory_type: str = "general",
                 metadata: Optional[Dict[str, Any]] = None,
                 session_id: Optional[str] = None):
        self.id = str(uuid.uuid4())
        self.content = content
        self.memory_type = memory_type
        self.metadata = metadata or {}
        self.session_id = session_id
        self.created_at = datetime.now()
        self.accessed_count = 0
        self.last_accessed = None
        self.importance_score = 1.0
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'memory_type': self.memory_type,
            'metadata': self.metadata,
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'accessed_count': self.accessed_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'importance_score': self.importance_score
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        item = cls(
            content=data['content'],
            memory_type=data['memory_type'],
            metadata=data['metadata'],
            session_id=data['session_id']
        )
        item.id = data['id']
        item.created_at = datetime.fromisoformat(data['created_at'])
        item.accessed_count = data['accessed_count']
        if data['last_accessed']:
            item.last_accessed = datetime.fromisoformat(data['last_accessed'])
        item.importance_score = data['importance_score']
        return item


class MemoryPlugin(ABC):
    """Abstract base class for memory plugins"""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.config = config
        self.auto_summarization = config.get('MEMORY_AUTO_SUMMARIZATION', 'true').lower() == 'true'
        self.contextual_recall = config.get('MEMORY_CONTEXTUAL_RECALL', 'true').lower() == 'true'
        self.learning_adaptation = config.get('MEMORY_LEARNING_ADAPTATION', 'true').lower() == 'true'
        self.memory_consolidation = config.get('MEMORY_CONSOLIDATION', 'true').lower() == 'true'
        self.max_memory_items = int(config.get('MAX_MEMORY_ITEMS', 10000))
        self.consolidation_threshold = int(config.get('MEMORY_CONSOLIDATION_THRESHOLD', 1000))
        
    @abstractmethod
    def add_memory(self, content: str, memory_type: str = "general",
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a new memory item"""
        pass
    
    @abstractmethod
    def search_memory(self, query: str, memory_type: Optional[str] = None,
                     limit: int = 10, similarity_threshold: float = 0.7) -> List[MemoryItem]:
        """Search for relevant memories"""
        pass
    
    @abstractmethod
    def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """Get a specific memory by ID"""
        pass
    
    @abstractmethod
    def update_memory(self, memory_id: str, content: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update an existing memory"""
        pass
    
    @abstractmethod
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory"""
        pass
    
    @abstractmethod
    def get_session_memories(self, session_id: Optional[str] = None) -> List[MemoryItem]:
        """Get all memories for a specific session"""
        pass
    
    @abstractmethod
    def consolidate_memories(self) -> int:
        """Consolidate and compress older memories"""
        pass

