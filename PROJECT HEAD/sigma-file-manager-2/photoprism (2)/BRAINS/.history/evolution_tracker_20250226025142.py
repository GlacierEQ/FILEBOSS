import json
import os
import time
from datetime import datetime
from pathlib import Path
import sqlite3
from typing import List, Dict, Any, Optional

class EvolutionTracker:
    """
    Tracks file organization suggestions and outcomes to evolve better recommendations over time
    """
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'evolution.db')
    
    def __init__(self):
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.DB_PATH), exist_ok=True)
        
        # Initialize database
        self._init_db()
        print(f"Evolution tracker initialized. Database: {self.DB_PATH}")
        
    def _init_db(self):
        """Initialize SQLite database for tracking evolution"""
        conn = sqlite3.connect(self.DB_PATH)
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
        
        # Create patterns table for learned organization patterns
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
        
        # Create prompt evolution table
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
    
    def track_recommendation(self, src_path: str, dst_path: str, summary: Optional[str] = None) -> int:
        """
        Store a new file organization recommendation
        
        Args:
            src_path: Original file path
            dst_path: Recommended file path
            summary: Summary of file content
            
        Returns:
            id: Record ID of the recommendation
        """
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        cursor.execute(
            'INSERT INTO recommendations (src_path, dst_path, file_summary, timestamp) VALUES (?, ?, ?, ?)',
            (src_path, dst_path, summary or "", timestamp)
        )
        
        rec_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return rec_id
    
    def track_bulk_recommendations(self, recommendations: List[Dict[str, Any]]):
        """
        Store multiple file organization recommendations
        
        Args:
            recommendations: List of recommendation dictionaries with src_path, dst_path, and optional summary
        """
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        for rec in recommendations:
            cursor.execute(
                'INSERT INTO recommendations (src_path, dst_path, file_summary, timestamp) VALUES (?, ?, ?, ?)',
                (rec['src_path'], rec['dst_path'], rec.get('summary', ""), timestamp)
            )
        
        conn.commit()
        conn.close()
    
    def record_outcome(self, src_path: str, dst_path: str, accepted: bool, feedback: Optional[str] = None):
        """
        Record whether a recommendation was accepted or rejected
        
        Args:
            src_path: Original source path
            dst_path: Recommended destination path
            accepted: Whether recommendation was accepted
            feedback: Optional user feedback
        """
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        
        # Find the most recent recommendation for this file path
        cursor.execute(
            'SELECT id FROM recommendations WHERE src_path = ? AND dst_path = ? ORDER BY timestamp DESC LIMIT 1',
            (src_path, dst_path)
        )
        
        result = cursor.fetchone()
        if result:
            rec_id = result[0]
            cursor.execute(
                'UPDATE recommendations SET accepted = ?, feedback = ? WHERE id = ?',
                (1 if accepted else 0, feedback or "", rec_id)
            )
        else:
            # If no matching recommendation found, create a new record
            timestamp = datetime.now().isoformat()
            cursor.execute(
                'INSERT INTO recommendations (src_path, dst_path, timestamp, accepted, feedback) VALUES (?, ?, ?, ?, ?)',
                (src_path, dst_path, timestamp, 1 if accepted else 0, feedback or "")
            )
        
        conn.commit()
        conn.close()
    
    def extract_patterns(self):
        """
        Analyze past recommendations to extract organizational patterns
        
        Returns:
            List of organizational patterns discovered
        """
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        
        # Get all accepted recommendations
        cursor.execute('SELECT src_path, dst_path, file_summary FROM recommendations WHERE accepted = 1')
        accepted_recs = cursor.fetchall()
        
        patterns = []
        
        if len(accepted_recs) > 5:  # Need enough data to find patterns
            # Extract extension patterns
            ext_patterns = {}
            for src, dst, summary in accepted_recs:
                src_ext = Path(src).suffix.lower()
                dst_dir = str(Path(dst).parent)
                
                if src_ext not in ext_patterns:
                    ext_patterns[src_ext] = {}
                    
                if dst_dir in ext_patterns[src_ext]:
                    ext_patterns[src_ext][dst_dir] += 1
                else:
                    ext_patterns[src_ext][dst_dir] = 1
            
            # Save discovered patterns
            timestamp = datetime.now().isoformat()
            
            for ext, dirs in ext_patterns.items():
                # Find most common directory for each extension
                most_common_dir = max(dirs.items(), key=lambda x: x[1], default=(None, 0))
                
                if most_common_dir[0] and most_common_dir[1] >= 3:  # Minimum threshold
                    pattern_data = json.dumps({
                        "extension": ext,
                        "directory": most_common_dir[0],
                        "occurrences": most_common_dir[1]
                    })
                    
                    confidence = most_common_dir[1] / sum(dirs.values())
                    
                    # Check if pattern already exists
                    cursor.execute(
                        'SELECT id, uses, confidence FROM patterns WHERE pattern_type = ? AND pattern_data LIKE ?',
                        ('extension', f'%"extension": "{ext}"%')
                    )
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Update existing pattern
                        pattern_id, uses, old_confidence = existing
                        new_uses = uses + 1
                        new_confidence = (old_confidence * uses + confidence) / new_uses
                        
                        cursor.execute(
                            'UPDATE patterns SET pattern_data = ?, confidence = ?, uses = ?, updated_at = ? WHERE id = ?',
                            (pattern_data, new_confidence, new_uses, timestamp, pattern_id)
                        )
                    else:
                        # Create new pattern
                        cursor.execute(
                            'INSERT INTO patterns (pattern_type, pattern_data, confidence, uses, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
                            ('extension', pattern_data, confidence, 1, timestamp, timestamp)
                        )
                    
                    patterns.append({
                        "type": "extension",
                        "data": json.loads(pattern_data),
                        "confidence": confidence
                    })
        
        conn.commit()
        conn.close()
        
        return patterns
    
    def get_active_patterns(self, min_confidence: float = 0.7):
        """
        Get current active organizational patterns
        
        Args:
            min_confidence: Minimum confidence threshold for patterns
            
        Returns:
            List of active patterns
        """
        conn = sqlite3.connect(self.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM patterns WHERE confidence >= ? ORDER BY confidence DESC',
            (min_confidence,)
        )
        
        patterns = []
        for row in cursor.fetchall():
            patterns.append({
                "id": row['id'],
                "type": row['pattern_type'],
                "data": json.loads(row['pattern_data']),
                "confidence": row['confidence'],
                "uses": row['uses']
            })
        
        conn.close()
        return patterns
    
    def generate_evolution_report(self):
        """
        Generate a report on system evolution performance
        
        Returns:
            Dictionary containing evolution metrics and insights
        """
        conn = sqlite3.connect(self.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get basic stats
        cursor.execute('SELECT COUNT(*) as total FROM recommendations')
        total = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as accepted FROM recommendations WHERE accepted = 1')
        accepted = cursor.fetchone()['accepted']
        
        acceptance_rate = (accepted / total) if total > 0 else 0
        
        # Get pattern stats
        cursor.execute('SELECT COUNT(*) as total FROM patterns')
        pattern_count = cursor.fetchone()['total']
        
        # Get top patterns
        cursor.execute('SELECT pattern_type, pattern_data, confidence FROM patterns ORDER BY confidence DESC LIMIT 5')
        top_patterns = []
        for row in cursor.fetchall():
            top_patterns.append({
                "type": row['pattern_type'],
                "data": json.loads(row['pattern_data']),
                "confidence": row['confidence']
            })
        
        conn.close()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "total_recommendations": total,
                "accepted_recommendations": accepted,
                "acceptance_rate": acceptance_rate,
                "pattern_count": pattern_count
            },
            "top_patterns": top_patterns,
            "insights": self._generate_insights(acceptance_rate, pattern_count)
        }
    
    def _generate_insights(self, acceptance_rate, pattern_count):
        """Generate insights based on current metrics"""
        insights = []
        
        if acceptance_rate < 0.5 and pattern_count > 0:
            insights.append("Acceptance rate is low. Consider refining existing patterns.")
        elif acceptance_rate > 0.8:
            insights.append("High acceptance rate indicates good organizational suggestions.")
            
        if pattern_count < 3:
            insights.append("Few patterns detected. More user interactions needed to develop robust organization rules.")
        elif pattern_count > 10:
            insights.append("Many patterns detected. System has developed specialized organization rules.")
            
        return insights
