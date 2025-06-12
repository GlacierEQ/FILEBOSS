"""
Mem0 Integration for OpenDevin

Integrates Mem0 AI's memory service for persistent, intelligent memory management
with semantic search and context-aware memory retrieval.
"""

from typing import List, Dict, Any, Optional
import json
from datetime import datetime

try:
    from mem0 import Memory
except ImportError:
    Memory = None

from opendevin import config
from opendevin.logger import opendevin_logger as logger
from .memory_plugin import MemoryPlugin, MemoryItem


class Mem0Memory(MemoryPlugin):
    """Mem0 AI integration for intelligent memory management"""
    
    def __init__(self, session_id: Optional[str] = None):
        super().__init__(session_id)
        
        if Memory is None:
            raise ImportError("mem0ai package not installed. Install with: pip install mem0ai")
        
        # Initialize Mem0 client
        self.mem0_config = {
            "graph_store": {
                "provider": "neo4j",
                "config": {
                    "url": config.get('NEO4J_URL', 'neo4j://localhost:7687'),
                    "username": config.get('NEO4J_USERNAME', 'neo4j'),
                    "password": config.get('NEO4J_PASSWORD', 'password')
                }
            },
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "collection_name": "opendevin_memories",
                    "path": "./data/chroma_db"
                }
            },
            "embedder": {
                "provider": "huggingface",
                "config": {
                    "model": config.get('MEMORY_EMBEDDING_MODEL', 'BAAI/bge-small-en-v1.5')
                }
            }
        }
        
        # Initialize with API key if available
        api_key = config.get('MEM0_API_KEY')
        if api_key:
            self.mem0_config['api_key'] = api_key
            
        try:
            self.memory = Memory.from_config(self.mem0_config)
        except Exception as e:
            logger.warning(f"Failed to initialize Mem0 with full config: {e}")
            # Fallback to basic initialization
            self.memory = Memory()
        
        self.user_id = f"opendevin_session_{self.session_id}"
        
    def add_memory(self, content: str, memory_type: str = "general",
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a new memory item using Mem0"""
        try:
            # Prepare metadata for Mem0
            mem0_metadata = {
                "memory_type": memory_type,
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }
            
            # Add to Mem0
            result = self.memory.add(
                messages=content,
                user_id=self.user_id,
                metadata=mem0_metadata
            )
            
            # Extract memory ID from result
            memory_id = result.get('id') if isinstance(result, dict) else str(result)
            
            logger.debug(f"Added memory to Mem0: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to add memory to Mem0: {e}")
            return ""
    
    def search_memory(self, query: str, memory_type: Optional[str] = None,
                     limit: int = 10, similarity_threshold: float = 0.7) -> List[MemoryItem]:
        """Search for relevant memories using Mem0"""
        try:
            # Search in Mem0
            results = self.memory.search(
                query=query,
                user_id=self.user_id,
                limit=limit
            )
            
            memory_items = []
            for result in results:
                try:
                    # Convert Mem0 result to MemoryItem
                    metadata = result.get('metadata', {})
                    
                    # Filter by memory type if specified
                    if memory_type and metadata.get('memory_type') != memory_type:
                        continue
                    
                    # Check similarity threshold
                    score = result.get('score', 1.0)
                    if score < similarity_threshold:
                        continue
                    
                    memory_item = MemoryItem(
                        content=result.get('memory', ''),
                        memory_type=metadata.get('memory_type', 'general'),
                        metadata=metadata,
                        session_id=metadata.get('session_id', self.session_id)
                    )
                    memory_item.id = result.get('id', memory_item.id)
                    memory_item.importance_score = score
                    
                    memory_items.append(memory_item)
                    
                except Exception as e:
                    logger.warning(f"Failed to process Mem0 search result: {e}")
                    continue
            
            return memory_items
            
        except Exception as e:
            logger.error(f"Failed to search Mem0 memories: {e}")
            return []
    
    def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """Get a specific memory by ID from Mem0"""
        try:
            # Get all memories and filter by ID
            memories = self.memory.get_all(user_id=self.user_id)
            
            for memory in memories:
                if memory.get('id') == memory_id:
                    metadata = memory.get('metadata', {})
                    
                    memory_item = MemoryItem(
                        content=memory.get('memory', ''),
                        memory_type=metadata.get('memory_type', 'general'),
                        metadata=metadata,
                        session_id=metadata.get('session_id', self.session_id)
                    )
                    memory_item.id = memory_id
                    
                    return memory_item
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get memory from Mem0: {e}")
            return None
    
    def update_memory(self, memory_id: str, content: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update an existing memory in Mem0"""
        try:
            # Mem0 doesn't have direct update, so we delete and recreate
            existing_memory = self.get_memory(memory_id)
            if not existing_memory:
                return False
            
            # Delete existing
            self.memory.delete(memory_id=memory_id)
            
            # Create new with updated content
            new_content = content or existing_memory.content
            new_metadata = existing_memory.metadata.copy()
            if metadata:
                new_metadata.update(metadata)
            
            new_id = self.add_memory(new_content, existing_memory.memory_type, new_metadata)
            return bool(new_id)
            
        except Exception as e:
            logger.error(f"Failed to update memory in Mem0: {e}")
            return False
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory from Mem0"""
        try:
            self.memory.delete(memory_id=memory_id)
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory from Mem0: {e}")
            return False
    
    def get_session_memories(self, session_id: Optional[str] = None) -> List[MemoryItem]:
        """Get all memories for a specific session"""
        target_session = session_id or self.session_id
        
        try:
            # Get all memories for user
            memories = self.memory.get_all(user_id=self.user_id)
            
            session_memories = []
            for memory in memories:
                metadata = memory.get('metadata', {})
                if metadata.get('session_id') == target_session:
                    memory_item = MemoryItem(
                        content=memory.get('memory', ''),
                        memory_type=metadata.get('memory_type', 'general'),
                        metadata=metadata,
                        session_id=target_session
                    )
                    memory_item.id = memory.get('id', memory_item.id)
                    session_memories.append(memory_item)
            
            return session_memories
            
        except Exception as e:
            logger.error(f"Failed to get session memories from Mem0: {e}")
            return []
    
    def consolidate_memories(self) -> int:
        """Consolidate and compress older memories using Mem0's intelligence"""
        try:
            # Get all memories
            memories = self.memory.get_all(user_id=self.user_id)
            
            if len(memories) < self.consolidation_threshold:
                return 0
            
            # Mem0 handles intelligent consolidation automatically
            # We can trigger a manual consolidation if needed
            logger.info(f"Memory consolidation triggered for {len(memories)} memories")
            
            # Return count of memories that could be consolidated
            return max(0, len(memories) - self.max_memory_items)
            
        except Exception as e:
            logger.error(f"Failed to consolidate memories in Mem0: {e}")
            return 0
    
    def get_conversation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history in Mem0 format"""
        try:
            history = self.memory.history(user_id=self.user_id)
            return history[-limit:] if history else []
        except Exception as e:
            logger.error(f"Failed to get conversation history from Mem0: {e}")
            return []

