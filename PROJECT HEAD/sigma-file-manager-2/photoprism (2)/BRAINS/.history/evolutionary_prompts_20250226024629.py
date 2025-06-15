import json
import os
from typing import List, Dict, Any, Optional

from evolution_tracker import EvolutionTracker

class EvolutionaryPrompt:
    """
    Self-evolving prompting system for file organization
    that improves over time based on user feedback
    """
    
    BASE_FILE_PROMPT = """
You will be provided with list of source files and a summary of their contents. For each file, propose a new path and filename, using a directory structure that optimally organizes the files using known conventions and best practices.

If the file is already named well or matches a known convention, set the destination path to the same as the source path.

Your response must be a JSON object with the following schema:
```json
{
    "files": [
        {
            "src_path": "original file path",
            "dst_path": "new file path under proposed directory structure with proposed file name"
        }
    ]
}
```
"""
    
    def __init__(self):
        self.tracker = EvolutionTracker()
        self.patterns = []
        self.refresh_patterns()
        
    def refresh_patterns(self):
        """Refresh patterns from the evolution tracker"""
        self.patterns = self.tracker.get_active_patterns()
        
    def generate_organization_prompt(self, include_patterns: bool = True) -> str:
        """
        Generate an evolved prompt for file organization that includes
        learned patterns and conventions
        
        Args:
            include_patterns: Whether to include learned patterns
            
        Returns:
            Evolved prompt string
        """
        prompt = self.BASE_FILE_PROMPT.strip()
        
        if include_patterns and self.patterns:
            # Add pattern guidance based on learned patterns
            pattern_text = "\n\nBased on observed organization patterns, follow these guidelines:\n"
            
            # Add extension-based patterns
            ext_patterns = [p for p in self.patterns if p["type"] == "extension"]
            if ext_patterns:
                pattern_text += "\nFile extension patterns:\n"
                for pattern in ext_patterns:
                    data = pattern["data"]
                    pattern_text += f"- Files with extension '{data['extension']}' belong in directory '{data['directory']}'\n"
            
            # Add other pattern types as they're developed
            
            prompt += pattern_text
            
        return prompt
    
    def generate_watch_prompt(self, fs_events) -> str:
        """
        Generate evolved prompt for watch events
        
        Args:
            fs_events: Filesystem events data
            
        Returns:
            Watch events prompt
        """
        # Extract examples of recent successful moves
        conn = self.tracker._init_db()
        
        watch_prompt = f"""
Here are a few examples of good file naming conventions to emulate, based on the files provided:

```json
{fs_events if isinstance(fs_events, str) else json.dumps(fs_events)}
```

Include the above items in your response exactly as is, along all other proposed changes.
"""
        
        # Add examples of successful moves if available
        recent_successes = self.tracker.get_active_patterns(min_confidence=0.8)
        if recent_successes:
            watch_prompt += "\n\nThese patterns have been successful in the past:\n"
            for pattern in recent_successes[:3]:  # Top 3 patterns
                data = pattern["data"]
                if pattern["type"] == "extension":
                    watch_prompt += f"- Files with extension '{data['extension']}' → '{data['directory']}'\n"
        
        return watch_prompt.strip()
    
    def track_recommendations(self, recommendations: List[Dict[str, Any]]):
        """
        Track a batch of recommendations
        
        Args:
            recommendations: List of recommendations (each with src_path, dst_path, summary)
        """
        self.tracker.track_bulk_recommendations(recommendations)
    
    def track_outcome(self, src_path: str, dst_path: str, actual_dst: str, feedback: str = None):
        """
        Track the outcome of a recommendation
        
        Args:
            src_path: Original file path
            dst_path: Recommended destination path
            actual_dst: Where the file was actually moved to
            feedback: Optional user feedback
        """
        accepted = (dst_path == actual_dst)
        self.tracker.record_outcome(src_path, dst_path, accepted, feedback)
        
        # Refresh patterns if we have new data
        if not accepted or feedback:
            self.refresh_patterns()
    
    def evolve(self):
        """
        Actively evolve the system by analyzing past recommendations
        and extracting new organizational patterns
        
        Returns:
            New patterns that were discovered
        """
        new_patterns = self.tracker.extract_patterns()
        self.refresh_patterns()
        return new_patterns
    
    def get_evolution_report(self):
        """
        Get a report on how the system is evolving
        
        Returns:
            Report dictionary with metrics and insights
        """
        return self.tracker.generate_evolution_report()
