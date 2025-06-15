"""
Initialize required databases for DeepSoul Coder
"""
import os
import sys
import logging
import sqlite3
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("DeepSoul-DBInit")

# Database paths
DATA_DIR = os.environ.get("DATA_DIR", "./data")
KNOWLEDGE_DB = os.path.join(DATA_DIR, "knowledge_store.db")

def init_knowledge_db():
    """Initialize the knowledge store database"""
    try:
        os.makedirs(os.path.dirname(KNOWLEDGE_DB), exist_ok=True)
        
        conn = sqlite3.connect(KNOWLEDGE_DB)
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
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_language ON knowledge_items (language)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_type ON knowledge_items (item_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sources_knowledge_id ON sources (knowledge_id)')
        
        conn.commit()
        conn.close()
        logger.info(f"Knowledge database initialized at {KNOWLEDGE_DB}")
        
    except Exception as e:
        logger.error(f"Error initializing knowledge database: {str(e)}")
        raise

def main():
    """Main initialization function"""
    # Create required directories
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Initialize database
    init_knowledge_db()
    
    # Add future database initializations here
    
    logger.info("Database initialization completed successfully")

if __name__ == "__main__":
    main()
