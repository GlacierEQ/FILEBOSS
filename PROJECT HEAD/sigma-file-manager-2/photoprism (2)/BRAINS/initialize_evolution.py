#!/usr/bin/env python
"""
Initialize the Evolution System for Sorting Hat

This script creates necessary directories and database files for the evolution system.
"""
import os
import json
import sqlite3
from pathlib import Path

# Define constants
EVOLUTION_DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
EVOLUTION_DB_PATH = os.path.join(EVOLUTION_DB_DIR, 'evolution.db')
SAFE_PATH = os.path.join(os.path.expanduser("~"), "OrganizeFolder")

def create_directories():
    """Create necessary directories for the evolution system"""
    directories = [
        EVOLUTION_DB_DIR,
        SAFE_PATH
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def initialize_database():
    """Initialize the SQLite database for evolution tracking"""
    conn = sqlite3.connect(EVOLUTION_DB_PATH)
    cursor = conn.cursor()
    
    # Create recommendations table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        src_path TEXT NOT NULL,
        dst_path TEXT NOT NULL,
        file_summary TEXT,
        timestamp TEXT NOT NULL,
        accepted INTEGER DEFAULT 0,
        feedback TEXT
    )
    ''')
    
    # Create patterns table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pattern_type TEXT NOT NULL,
        pattern_data TEXT NOT NULL,
        confidence REAL DEFAULT 0.0,
        uses INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    ''')
    
    # Create prompt versions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prompt_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prompt_text TEXT NOT NULL,
        effectiveness REAL DEFAULT 0.0,
        created_at TEXT NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✓ Initialized database: {EVOLUTION_DB_PATH}")

def add_default_patterns():
    """Add default patterns to kickstart the evolution process"""
    conn = sqlite3.connect(EVOLUTION_DB_PATH)
    cursor = conn.cursor()
    
    default_patterns = [
        {
            "pattern_type": "extension",
            "pattern_data": json.dumps({
                "extension": ".jpg",
                "directory": "images",
                "occurrences": 5
            }),
            "confidence": 0.9,
            "uses": 5
        },
        {
            "pattern_type": "extension",
            "pattern_data": json.dumps({
                "extension": ".png",
                "directory": "images",
                "occurrences": 4
            }),
            "confidence": 0.8,
            "uses": 4
        },
        {
            "pattern_type": "extension",
            "pattern_data": json.dumps({
                "extension": ".pdf",
                "directory": "documents",
                "occurrences": 3
            }),
            "confidence": 0.7,
            "uses": 3
        }
    ]
    
    from datetime import datetime
    timestamp = datetime.now().isoformat()
    
    for pattern in default_patterns:
        cursor.execute(
            '''
            INSERT INTO patterns 
            (pattern_type, pattern_data, confidence, uses, created_at, updated_at) 
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (
                pattern["pattern_type"],
                pattern["pattern_data"],
                pattern["confidence"],
                pattern["uses"],
                timestamp,
                timestamp
            )
        )
    
    conn.commit()
    conn.close()
    print(f"✓ Added default patterns to database")

if __name__ == "__main__":
    print("Initializing Evolution System for Sorting Hat...")
    create_directories()
    initialize_database()
    add_default_patterns()
    print("\nInitialization complete! The evolution system is ready to use.")
    print(f"\nSafe operating folder: {SAFE_PATH}")
    print(f"Evolution database: {EVOLUTION_DB_PATH}")
    print("\nTo start the server, run: uvicorn server:app --reload")
