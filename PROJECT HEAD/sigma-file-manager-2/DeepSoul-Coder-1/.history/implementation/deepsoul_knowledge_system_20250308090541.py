"""
DeepSoul Knowledge System - Knowledge acquisition, storage, and retrieval for code intelligence
"""
import os
import json
import sqlite3
import numpy as np
import torch
from pathlib import Path
from typing import Dict, List, Union, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
from transformers import PreTrainedTokenizer, PreTrainedModel
from git import Repo
import requests
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DeepSoul-Knowledge")

@dataclass
class KnowledgeSource:
    """Knowledge source metadata"""
    source_type: str  # 'repo', 'doc', 'web', 'local', etc.
    uri: str  # Path or URL to the source
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 0.8  # Confidence score (0-1)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "source_type": self.source_type,
            "uri": self.uri,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
            "tags": self.tags,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeSource":
        """Create from dictionary representation"""
        source = cls(
            source_type=data["source_type"],
            uri=data["uri"],
            confidence=data["confidence"],
            tags=data["tags"],
            metadata=data["metadata"]
        )
        source.timestamp = datetime.fromisoformat(data["timestamp"])
        return source

@dataclass
class CodeKnowledgeItem:
    """A single unit of code knowledge"""
    content: str  # The actual knowledge content (code, explanation, etc.)
    language: str  # Programming language
    sources: List[KnowledgeSource]  # Where this knowledge came from
    embedding: Optional[np.ndarray] = None  # Vector representation
    item_type: str = "code"  # Type of knowledge: 'code', 'pattern', 'concept', 'api', etc.
    complexity: float = 0.5  # Complexity score (0-1)
    relevance_score: float = 1.0  # Relevance score for ranking
    relationship_ids: List[str] = field(default_factory=list)  # IDs of related knowledge
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def id(self) -> str:
        """Generate a deterministic ID based on content"""
        return hashlib.sha256(self.content.encode('utf-8')).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "content": self.content,
            "language": self.language,
            "sources": [s.to_dict() for s in self.sources],
            "embedding": self.embedding.tolist() if self.embedding is not None else None,
            "item_type": self.item_type,
            "complexity": self.complexity,
            "relevance_score": self.relevance_score,
            "relationship_ids": self.relationship_ids,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodeKnowledgeItem":
        """Create from dictionary representation"""
        item = cls(
            content=data["content"],
            language=data["language"],
            sources=[KnowledgeSource.from_dict(s) for s in data["sources"]],
            item_type=data["item_type"],
            complexity=data["complexity"],
            relevance_score=data["relevance_score"],
            relationship_ids=data["relationship_ids"],
            metadata=data["metadata"]
        )
        if data["embedding"] is not None:
            item.embedding = np.array(data["embedding"])
        item.timestamp = datetime.fromisoformat(data["timestamp"])
        return item

class KnowledgeStore:
    """Storage system for code knowledge"""
    
    def __init__(self, db_path: str = "knowledge_store.db"):
        """Initialize the knowledge store"""
        self.db_path = db_path
        self.embeddings_path = db_path + ".embeddings.npy"
        self._setup_database()
    
    def _setup_database(self):
        """Set up the SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_items (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            language TEXT NOT NULL,
            item_type TEXT NOT NULL,
            complexity REAL,
            relevance_score REAL,
            timestamp TEXT,
            metadata TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            knowledge_id TEXT,
            source_type TEXT NOT NULL,
            uri TEXT NOT NULL,
            timestamp TEXT,
            confidence REAL,
            tags TEXT,
            metadata TEXT,
            FOREIGN KEY (knowledge_id) REFERENCES knowledge_items (id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id TEXT,
            to_id TEXT,
            relationship_type TEXT,
            strength REAL,
            FOREIGN KEY (from_id) REFERENCES knowledge_items (id),
            FOREIGN KEY (to_id) REFERENCES knowledge_items (id)
        )
        ''')
        
        conn.commit()
        conn.close()
        
        # Initialize embeddings storage if not exists
        if not os.path.exists(self.embeddings_path):
            np.save(self.embeddings_path, {})
    
    def add_item(self, item: CodeKnowledgeItem) -> bool:
        """Add a knowledge item to the store"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if item already exists
            cursor.execute("SELECT id FROM knowledge_items WHERE id = ?", (item.id,))
            if cursor.fetchone():
                # Update existing item
                cursor.execute('''
                UPDATE knowledge_items 
                SET content = ?, language = ?, item_type = ?, complexity = ?,
                    relevance_score = ?, timestamp = ?, metadata = ?
                WHERE id = ?
                ''', (
                    item.content, item.language, item.item_type, item.complexity,
                    item.relevance_score, item.timestamp.isoformat(), json.dumps(item.metadata),
                    item.id
                ))
                
                # Delete old sources
                cursor.execute("DELETE FROM sources WHERE knowledge_id = ?", (item.id,))
            else:
                # Insert new item
                cursor.execute('''
                INSERT INTO knowledge_items 
                (id, content, language, item_type, complexity, relevance_score, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item.id, item.content, item.language, item.item_type, item.complexity,
                    item.relevance_score, item.timestamp.isoformat(), json.dumps(item.metadata)
                ))
            
            # Insert sources
            for source in item.sources:
                cursor.execute('''
                INSERT INTO sources 
                (knowledge_id, source_type, uri, timestamp, confidence, tags, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item.id, source.source_type, source.uri, source.timestamp.isoformat(),
                    source.confidence, json.dumps(source.tags), json.dumps(source.metadata)
                ))
            
            # Insert relationships
            for rel_id in item.relationship_ids:
                cursor.execute('''
                INSERT INTO relationships 
                (from_id, to_id, relationship_type, strength)
                VALUES (?, ?, ?, ?)
                ''', (
                    item.id, rel_id, "related", 1.0
                ))
            
            # Save embedding if available
            if item.embedding is not None:
                # Load existing embeddings
                embeddings = np.load(self.embeddings_path, allow_pickle=True).item()
                embeddings[item.id] = item.embedding
                np.save(self.embeddings_path, embeddings)
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error adding knowledge item: {str(e)}")
            return False
    
    def get_item(self, item_id: str) -> Optional[CodeKnowledgeItem]:
        """Get a knowledge item by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dictionary access on rows
            cursor = conn.cursor()
            
            # Get knowledge item
            cursor.execute("SELECT * FROM knowledge_items WHERE id = ?", (item_id,))
            item_row = cursor.fetchone()
            
            if not item_row:
                return None
            
            # Get sources
            cursor.execute("SELECT * FROM sources WHERE knowledge_id = ?", (item_id,))
            source_rows = cursor.fetchall()
            
            # Get relationships
            cursor.execute("SELECT to_id FROM relationships WHERE from_id = ?", (item_id,))
            rel_rows = cursor.fetchall()
            
            conn.close()
            
            # Load embedding if available
            try:
                embeddings = np.load(self.embeddings_path, allow_pickle=True).item()
                embedding = embeddings.get(item_id)
            except (FileNotFoundError, KeyError):
                embedding = None
            
            # Convert to object
            sources = []
    for s in source_rows:
        sources.append(KnowledgeSource(
            source_type=s["source_type"],
            uri=s["uri"],
            confidence=s["confidence"],
            tags=json.loads(s["tags"]),
            metadata=json.loads(s["metadata"])
        ))
        sources[-1].timestamp = datetime.fromisoformat(s["timestamp"])
    
    item = CodeKnowledgeItem(
        content=item_row["content"],
        language=item_row["language"],
        sources=sources,
        embedding=embedding,
        item_type=item_row["item_type"],
        complexity=item_row["complexity"],
        relevance_score=item_row["relevance_score"],
        relationship_ids=[r["to_id"] for r in rel_rows],
        metadata=json.loads(item_row["metadata"])
    )
            item.timestamp = datetime.fromisoformat(item_row["timestamp"])
            
            return item
            
        except Exception as e:
            logger.error(f"Error getting knowledge item: {str(e)}")
            return None
    
    def search(self, query: str, language: Optional[str] = None, 
               limit: int = 10, embedding: Optional[np.ndarray] = None) -> List[CodeKnowledgeItem]:
        """
        Search the knowledge store
        
        Args:
            query: Search query string
            language: Optionally filter by programming language
            limit: Maximum results to return
            embedding: Query embedding for semantic search
            
        Returns:
            List of matching knowledge items
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Start building query
            sql = "SELECT id FROM knowledge_items WHERE content LIKE ?"
            params = [f"%{query}%"]
            
            # Add language filter if specified
            if language:
                sql += " AND language = ?"
                params.append(language)
            
            # Limit results
            sql += " ORDER BY relevance_score DESC LIMIT ?"
            params.append(limit)
            
            # Execute query
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            
            # Get items by ID
            items = [self.get_item(row["id"]) for row in rows]
            items = [item for item in items if item is not None]
            
            # If embedding is provided, perform semantic search
            if embedding is not None and isinstance(embedding, np.ndarray):
                # Load all embeddings
                try:
                    all_embeddings = np.load(self.embeddings_path, allow_pickle=True).item()
                    
                    # Calculate similarity for each item
                    item_similarities = []
                    for item in items:
                        if item.id in all_embeddings:
                            item_emb = all_embeddings[item.id]
                            similarity = np.dot(embedding, item_emb) / (
                                np.linalg.norm(embedding) * np.linalg.norm(item_emb)
                            )
                            item_similarities.append((item, similarity))
                    
                    # Sort by similarity
                    item_similarities.sort(key=lambda x: x[1], reverse=True)
                    items = [item for item, _ in item_similarities]
                except (FileNotFoundError, KeyError):
                    pass
            
            return items
            
        except Exception as e:
            logger.error(f"Error searching knowledge store: {str(e)}")
            return []

class KnowledgeAcquisition:
    """Knowledge acquisition system for DeepSoul"""
    
    def __init__(self, knowledge_store: KnowledgeStore, model: Optional[PreTrainedModel] = None,
                 tokenizer: Optional[PreTrainedTokenizer] = None):
        """Initialize the knowledge acquisition system"""
        self.knowledge_store = knowledge_store
        self.model = model
        self.tokenizer = tokenizer
    
    def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text using the model"""
        if self.model is None or self.tokenizer is None:
            raise ValueError("Model and tokenizer are required for embedding generation")
        
        # Tokenize and get model embedding
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs, output_hidden_states=True)
            # Use last hidden state of [CLS] token as embedding
            embedding = outputs.hidden_states[-1][0, 0].cpu().numpy()
        
        # Normalize
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding
    
    def _extract_code_chunks(self, content: str, language: str) -> List[str]:
        """Extract code chunks from content"""
        # Simple extraction for now - can be improved with proper parsing
        try:
            chunks = []
            lines = content.split('\n')
            current_chunk = []
            
            for line in lines:
                # If line is empty and we have a chunk, complete it
                if not line.strip() and current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                elif line.strip():
                    current_chunk.append(line)
            
            # Add final chunk if exists
            if current_chunk:
                chunks.append('\n'.join(current_chunk))
            
            return chunks
        except Exception as e:
            logger.error(f"Error extracting code chunks: {str(e)}")
            return []
    
    def _assess_code_quality(self, code: str, language: str) -> float:
        """Assess code quality (0-1)"""
        # Simple heuristic-based quality assessment
        quality_score = 0.5
        
        # Length-based assessment
        if len(code) < 10:
            quality_score -= 0.2
        elif len(code) > 1000:
            quality_score -= 0.1
        
        # Comment presence assessment
        comment_markers = {
            'python': ['#'],
            'javascript': ['//', '/*'],
            'java': ['//', '/*'],
            'c': ['//', '/*'],
            'cpp': ['//', '/*'],
            'ruby': ['#'],
            'go': ['//'],
            'rust': ['//'],
            'php': ['//', '#', '/*']
        }
        
        markers = comment_markers.get(language.lower(), ['#', '//'])
        has_comments = any(marker in code for marker in markers)
        if has_comments:
            quality_score += 0.1
        
        # Function/class presence assessment (simple heuristic)
        function_patterns = {
            'python': ['def ', 'class '],
            'javascript': ['function', 'class', '=>'],
            'java': ['class', 'void', 'public', 'private'],
            'c': ['void', 'int', 'char', 'struct'],
            'cpp': ['void', 'int', 'class', 'template'],
            'ruby': ['def ', 'class '],
            'go': ['func', 'type'],
            'rust': ['fn ', 'struct', 'impl'],
            'php': ['function', 'class']
        }
        
        patterns = function_patterns.get(language.lower(), ['def', 'class', 'function'])
        has_functions = any(pattern in code for pattern in patterns)
        if has_functions:
            quality_score += 0.1
        
        # Constrain to valid range
        return max(0.1, min(0.9, quality_score))
    
    def ingest_file(self, file_path: str, language: Optional[str] = None) -> List[str]:
        """
        Ingest knowledge from a file
        
        Args:
            file_path: Path to the file
            language: Programming language (if None, try to determine from file extension)
            
        Returns:
            List of added knowledge item IDs
        """
        try:
            # Determine language if not provided
            if language is None:
                ext = os.path.splitext(file_path)[1].lower()
                language_map = {
                    '.py': 'python',
                    '.js': 'javascript',
                    '.ts': 'typescript',
                    '.java': 'java',
                    '.c': 'c',
                    '.cpp': 'cpp',
                    '.cs': 'csharp',
                    '.rb': 'ruby',
                    '.go': 'go',
                    '.rs': 'rust',
                    '.php': 'php',
                    '.html': 'html',
                    '.css': 'css',
                    '.sh': 'bash'
                }
                language = language_map.get(ext, 'unknown')
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Create knowledge source
            source = KnowledgeSource(
                source_type='local',
                uri=file_path,
                confidence=0.9,
                tags=[language, 'file'],
                metadata={'path': file_path, 'size': len(content)}
            )
            
            # Extract code chunks
            chunks = self._extract_code_chunks(content, language)
            
            # Create knowledge items for each chunk
            item_ids = []
            for chunk in chunks:
                if len(chunk.strip()) < 10:  # Skip very small chunks
                    continue
                    
                # Assess quality
                quality = self._assess_code_quality(chunk, language)
                
                # Generate embedding if model available
                embedding = None
                if self.model is not None and self.tokenizer is not None:
                    try:
                        embedding = self._generate_embedding(chunk)
                    except Exception as e:
                        logger.error(f"Error generating embedding: {str(e)}")
                
                # Create knowledge item
                item = CodeKnowledgeItem(
                    content=chunk,
                    language=language,
                    sources=[source],
                    embedding=embedding,
                    item_type='code',
                    complexity=quality,
                    relevance_score=quality
                )
                
                # Add to knowledge store
                if self.knowledge_store.add_item(item):
                    item_ids.append(item.id)
            
            return item_ids
            
        except Exception as e:
            logger.error(f"Error ingesting file: {str(e)}")
            return []
    
    def ingest_repository(self, repo_path: str, recursive: bool = True) -> List[str]:
        """
        Ingest knowledge from a repository
        
        Args:
            repo_path: Path to the repository
            recursive: Whether to recursively ingest subdirectories
            
        Returns:
            List of added knowledge item IDs
        """
        try:
            all_item_ids = []
            repo_path = Path(repo_path)
            
            # Try to get repository information
            repo_metadata = {}
            try:
                repo = Repo(repo_path)
                repo_metadata = {
                    "remote_url": next((remote.url for remote in repo.remotes), None),
                    "active_branch": repo.active_branch.name,
                    "last_commit": str(repo.head.commit),
                    "commit_date": repo.head.commit.committed_datetime.isoformat()
                }
            except:
                pass
            
            # Walk through repository
            for root, dirs, files in os.walk(repo_path):
                # Skip hidden directories (including .git)
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                # Process each file
                for file in files:
                    # Skip hidden files and non-code files
                    if file.startswith('.'):
                        continue
                        
                    file_path = os.path.join(root, file)
                    
                    # Skip binary files and large files
                    try:
                        if os.path.getsize(file_path) > 1000000:  # 1MB
                            continue
                            
                        # Check if file is text
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            f.read(1024)  # Just read a bit to check if it's text
                    except:
                        continue
                    
                    # Ingest file
                    item_ids = self.ingest_file(file_path)
                    all_item_ids.extend(item_ids)
                
                # Stop recursion if requested
                if not recursive:
                    break
            
            return all_item_ids
            
        except Exception as e:
            logger.error(f"Error ingesting repository: {str(e)}")
            return []
    
    def ingest_documentation(self, url: str, language: str) -> List[str]:
        """
        Ingest knowledge from a documentation webpage
        
        Args:
            url: URL of the documentation
            language: Programming language
            
        Returns:
            List of added knowledge item IDs
        """
        try:
            # Fetch documentation
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract code blocks (very basic approach - would need to be improved)
            code_blocks = soup.find_all('code')
            code_blocks.extend(soup.find_all('pre'))
            
            # Create knowledge source
            source = KnowledgeSource(
                source_type='web',
                uri=url,
                confidence=0.7,
                tags=[language, 'documentation'],
                metadata={'title': soup.title.text if soup.title else url}
            )
            
            # Create knowledge items for each code block
            item_ids = []
            for block in code_blocks:
                code = block.text.strip()
                if len(code) < 20:  # Skip very small snippets
                    continue
                
                # Generate embedding if model available
                embedding = None
                if self.model is not None and self.tokenizer is not None:
                    try:
                        embedding = self._generate_embedding(code)
                    except Exception as e:
                        logger.error(f"Error generating embedding: {str(e)}")
                
                # Create knowledge item
                item = CodeKnowledgeItem(
                    content=code,
                    language=language,
                    sources=[source],
                    embedding=embedding,
                    item_type='snippet',
                    complexity=0.6,  # Default value for web snippets
                    relevance_score=0.7
                )
                
                # Add to knowledge store
                if self.knowledge_store.add_item(item):
                    item_ids.append(item.id)
            
            return item_ids
            
        except Exception as e:
            logger.error(f"Error ingesting documentation: {str(e)}")
            return []


class KnowledgeRecommendation:
    """Knowledge recommendation system for code completion and generation"""
    
    def __init__(self, knowledge_store: KnowledgeStore, model: Optional[PreTrainedModel] = None,
                 tokenizer: Optional[PreTrainedTokenizer] = None):
        """Initialize the knowledge recommendation system"""
        self.knowledge_store = knowledge_store
        self.model = model
        self.tokenizer = tokenizer
        self.acquisition = KnowledgeAcquisition(knowledge_store, model, tokenizer)
    
    def recommend_for_code(self, code_context: str, language: str, 
                          limit: int = 5) -> List[CodeKnowledgeItem]:
        """
        Recommend knowledge items for the given code context
        
        Args:
            code_context: Current code context
            language: Programming language
            limit: Maximum number of recommendations
            
        Returns:
            List of recommended knowledge items
        """
        # Generate embedding for code context if model available
        embedding = None
        if self.model is not None and self.tokenizer is not None:
            try:
                embedding = self.acquisition._generate_embedding(code_context)
            except Exception as e:
                logger.error(f"Error generating embedding: {str(e)}")
        
        # Extract keywords for search
        # This is a simple approach - can be enhanced with proper code parsing
        keywords = []
        for line in code_context.split('\n'):
            line = line.strip()
            if line and not line.startswith(('#', '//', '/*', '*')):
                # Extract potential function names, class names, etc.
                for token in line.split():
                    token = token.strip('();{}[],."\':')
                    if token and len(token) > 3 and token.isalnum():
                        keywords.append(token)
        
        # Get unique keywords sorted by length (descending)
        unique_keywords = sorted(set(keywords), key=len, reverse=True)
        
        # Use the longest keyword for search, or first part of code if no keywords
        query = unique_keywords[0] if unique_keywords else code_context[:50]
        
        # Search knowledge store
        results = self.knowledge_store.search(
            query=query,
            language=language,
            limit=limit * 2,  # Get more than needed for filtering
            embedding=embedding
        )
        
        # Filter and rank results
        if len(results) == 0:
            return []
            
        # Calculate relevance scores based on code context similarity
        ranked_results = []
        for item in results:
            # Calculate lexical similarity (simple token overlap)
            context_tokens = set(code_context.lower().split())
            item_tokens = set(item.content.lower().split())
            token_overlap = len(context_tokens.intersection(item_tokens)) / len(context_tokens) if context_tokens else 0
            
            # Combined score (with embedding similarity already factored in from search)
            relevance = token_overlap * 0.5 + item.relevance_score * 0.5
            ranked_results.append((item, relevance))
        
        # Sort by relevance and return top recommendations
        ranked_results.sort(key=lambda x: x[1], reverse=True)
        return [item for item, _ in ranked_results[:limit]]


# Example usage
def demo():
    """Demonstration of the knowledge system"""
    print("Initializing knowledge system...")
    store = KnowledgeStore("demo_knowledge.db")
    acquisition = KnowledgeAcquisition(store)
    
    # Create a sample knowledge item
    source = KnowledgeSource(
        source_type="example",
        uri="demo",
        confidence=1.0,
        tags=["python", "demo"]
    )
    
    item = CodeKnowledgeItem(
        content="""def fibonacci(n):
    """" Calculate the Fibonacci sequence up to n """
    a, b = 0, 1
    result = []
    while a < n:
        result.append(a)
        a, b = b, a + b
    return result""",
        language="python",
        sources=[source],
        item_type="function"
    )
    
    # Add to store
    print("Adding sample item to store...")
    store.add_item(item)
    
    # Retrieve the item
    print("Retrieving item...")
    retrieved = store.get_item(item.id)
    print(f"Retrieved content: {retrieved.content[:50]}...")
    
    # Search for items
    print("Searching for 'fibonacci'...")
    results = store.search("fibonacci")
    print(f"Found {len(results)} results")
    
    # Clean up
    print("Demo completed.")
    
if __name__ == "__main__":
    demo()
