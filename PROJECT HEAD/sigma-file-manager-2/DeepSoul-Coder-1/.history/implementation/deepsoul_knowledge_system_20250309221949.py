"""
DeepSoul Knowledge System - Components for knowledge acquisition, storage, and recommendation
"""
import os
import sys
import json
import time
import torch
import logging
import sqlite3
import hashlib
from pathlib import Path
from typing import Dict, List, Union, Optional, Tuple, Any
from dataclasses import dataclass, field
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import OOM protection utilities
from implementation.oom_protected_execution import oom_protected, MemoryEfficientContext
from utils.tensor_optimization import optimize_tensor

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DeepSoul-KnowledgeSystem")

@dataclass
class CodeKnowledgeItem:
    """Representation of a code-related knowledge item"""
    item_id: str
    content: str
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    
    def __post_init__(self):
        # Generate item ID if not provided
        if not self.item_id:
            self.item_id = hashlib.md5(self.content.encode()).hexdigest()

class KnowledgeStore:
    """Persistent storage for knowledge items using SQLite"""
    
    def __init__(self, db_path: str = "knowledge_store.db"):
        """Initialize knowledge store with SQLite database"""
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Establish connection to SQLite database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            logger.info(f"Connected to knowledge store: {self.db_path}")
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
    
    def _create_tables(self):
        """Create necessary tables in the database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_items (
                    item_id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    source TEXT,
                    metadata TEXT,
                    embedding BLOB
                )
            """)
            self.conn.commit()
            logger.info("Knowledge store tables created")
        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
    
    def add_item(self, item: CodeKnowledgeItem) -> bool:
        """Add a knowledge item to the store"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO knowledge_items (item_id, content, source, metadata, embedding)
                VALUES (?, ?, ?, ?, ?)
            """, (item.item_id, item.content, item.source, json.dumps(item.metadata), 
                  json.dumps(item.embedding) if item.embedding else None))
            self.conn.commit()
            logger.info(f"Added knowledge item: {item.item_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding knowledge item: {str(e)}")
            return False
    
    def get_item(self, item_id: str) -> Optional[CodeKnowledgeItem]:
        """Retrieve a knowledge item by ID"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT item_id, content, source, metadata, embedding FROM knowledge_items WHERE item_id = ?", (item_id,))
            row = cursor.fetchone()
            if row:
                item_id, content, source, metadata, embedding = row
                return CodeKnowledgeItem(
                    item_id=item_id,
                    content=content,
                    source=source,
                    metadata=json.loads(metadata) if metadata else {},
                    embedding=json.loads(embedding) if embedding else None
                )
            return None
        except Exception as e:
            logger.error(f"Error retrieving knowledge item: {str(e)}")
            return None
    
    def search_items(self, query: str, limit: int = 10) -> List[CodeKnowledgeItem]:
        """Search for knowledge items containing the query"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT item_id, content, source, metadata, embedding
                FROM knowledge_items
                WHERE content LIKE ?
                LIMIT ?
            """, (f"%{query}%", limit))
            rows = cursor.fetchall()
            
            items = []
            for row in rows:
                item_id, content, source, metadata, embedding = row
                items.append(CodeKnowledgeItem(
                    item_id=item_id,
                    content=content,
                    source=source,
                    metadata=json.loads(metadata) if metadata else {},
                    embedding=json.loads(embedding) if embedding else None
                ))
            return items
        except Exception as e:
            logger.error(f"Error searching knowledge items: {str(e)}")
            return []
    
    def get_all_items(self) -> List[CodeKnowledgeItem]:
        """Retrieve all knowledge items from the store"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT item_id, content, source, metadata, embedding FROM knowledge_items")
            rows = cursor.fetchall()
            
            items = []
            for row in rows:
                item_id, content, source, metadata, embedding = row
                items.append(CodeKnowledgeItem(
                    item_id=item_id,
                    content=content,
                    source=source,
                    metadata=json.loads(metadata) if metadata else {},
                    embedding=json.loads(embedding) if embedding else None
                ))
            return items
        except Exception as e:
            logger.error(f"Error retrieving all knowledge items: {str(e)}")
            return []
    
    def delete_item(self, item_id: str) -> bool:
        """Delete a knowledge item from the store"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM knowledge_items WHERE item_id = ?", (item_id,))
            self.conn.commit()
            logger.info(f"Deleted knowledge item: {item_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting knowledge item: {str(e)}")
            return False
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Knowledge store connection closed")

class KnowledgeAcquisition:
    """Acquire knowledge from various sources and store it in the knowledge store"""
    
    def __init__(self, knowledge_store: KnowledgeStore, model=None, tokenizer=None):
        """Initialize knowledge acquisition system"""
        self.knowledge_store = knowledge_store
        self.model = model
        self.tokenizer = tokenizer
    
    @oom_protected(retry_on_cpu=True)
    def ingest_file(self, file_path: str) -> List[str]:
        """Ingest knowledge items from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split content into smaller chunks (e.g., by paragraph)
            chunks = content.split("\n\n")
            
            item_ids = []
            for chunk in chunks:
                item = CodeKnowledgeItem(content=chunk, source=file_path)
                
                # Generate embedding if model is available
                if self.model is not None and self.tokenizer is not None:
                    item.embedding = self._generate_embedding(chunk)
                
                # Add to knowledge store
                if self.knowledge_store.add_item(item):
                    item_ids.append(item.item_id)
            
            logger.info(f"Ingested {len(item_ids)} knowledge items from {file_path}")
            return item_ids
        except Exception as e:
            logger.error(f"Error ingesting file: {str(e)}")
            return []
    
    @oom_protected(retry_on_cpu=True)
    def ingest_repository(self, repo_path: str) -> List[str]:
        """Ingest knowledge items from a code repository"""
        try:
            repo_path = Path(repo_path)
            item_ids = []
            
            # Iterate through all files in the repository
            for file_path in repo_path.glob("**/*"):
                if file_path.is_file() and file_path.suffix in [".py", ".js", ".java", ".c", ".cpp", ".txt", ".md"]:
                    ids = self.ingest_file(str(file_path))
                    item_ids.extend(ids)
            
            logger.info(f"Ingested {len(item_ids)} knowledge items from repository: {repo_path}")
            return item_ids
        except Exception as e:
            logger.error(f"Error ingesting repository: {str(e)}")
            return []
    
    @oom_protected(retry_on_cpu=True)
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a given text using the model"""
        try:
            # Tokenize and move to device
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(self.model.device)
            
            # Generate embedding
            with torch.no_grad():
                outputs = self.model(**inputs)
                
                # Extract embedding (mean of last hidden state)
                embedding = outputs.last_hidden_state.mean(dim=1).cpu().tolist()[0]
            
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None

class KnowledgeRecommendation:
    """Recommend relevant knowledge items based on a query"""
    
    def __init__(self, knowledge_store: KnowledgeStore, model=None, tokenizer=None):
        """Initialize knowledge recommendation system"""
        self.knowledge_store = knowledge_store
        self.model = model
        self.tokenizer = tokenizer
    
    @oom_protected(retry_on_cpu=True)
    def recommend_items(self, query: str, limit: int = 5) -> List[CodeKnowledgeItem]:
        """Recommend knowledge items based on a query"""
        try:
            # Generate embedding for the query
            query_embedding = self._generate_embedding(query)
            if not query_embedding:
                logger.warning("Could not generate embedding for query")
                return []
            
            # Get all knowledge items
            items = self.knowledge_store.get_all_items()
            
            # Calculate cosine similarity between query and each item
            scores = []
            for item in items:
                if item.embedding:
                    similarity = cosine_similarity([query_embedding], [item.embedding])[0][0]
                    scores.append((item, similarity))
            
            # Sort by similarity score
            scores.sort(key=lambda x: x[1], reverse=True)
            
            # Return top items
            return [item for item, _ in scores[:limit]]
        except Exception as e:
            logger.error(f"Error recommending knowledge items: {str(e)}")
            return []
    
    @oom_protected(retry_on_cpu=True)
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a given text using the model"""
        try:
            # Tokenize and move to device
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(self.model.device)
            
            # Generate embedding
            with torch.no_grad():
                outputs = self.model(**inputs)
                
                # Extract embedding (mean of last hidden state)
                embedding = outputs.last_hidden_state.mean(dim=1).cpu().tolist()[0]
            
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None

def demo_knowledge_system():
    """Demonstrate the knowledge system components"""
    # Create knowledge store
    knowledge_store = KnowledgeStore("demo_knowledge.db")
    
    # Create knowledge acquisition system
    acquisition = KnowledgeAcquisition(knowledge_store)
    
    # Ingest a file
    acquisition.ingest_file("demo_knowledge.txt")
    
    # Create knowledge recommendation system
    recommendation = KnowledgeRecommendation(knowledge_store)
    
    # Search for items
    results = recommendation.recommend_items("code optimization techniques")
    
    # Print results
    print("Recommended items:")
    for item in results:
        print(f"- {item.content[:50]}...")
    
    # Close the knowledge store
    knowledge_store.close()

if __name__ == "__main__":
    demo_knowledge_system()