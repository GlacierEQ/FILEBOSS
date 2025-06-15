"""
Natural Language Bridge Module

This module integrates the Natural Language Organizer with the core Sorting Hat system,
allowing various components to access the NL functionality.
"""
import os
import sys
import json
import asyncio
import logging
from typing import Dict, Any, Optional, List, Union

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import natural language organizer
try:
    from natural_language_organizer import NaturalLanguageOrganizer, handle_natural_language_command
except ImportError:
    raise ImportError("Natural Language Organizer module not found. Please check installation.")

# Import log manager if available
try:
    from log_manager import get_logger
    logger = get_logger("nl_bridge")
except ImportError:
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s')
    logger = logging.getLogger("nl_bridge")

class NLBridge:
    """Bridge class that connects Natural Language Organizer with other Sorting Hat components"""
    
    def __init__(self):
        """Initialize the NL Bridge"""
        self.organizer = NaturalLanguageOrganizer()
        
    async def process_instruction(self, 
                               instruction: str, 
                               path: Optional[str] = None,
                               metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a natural language instruction and return results
        
        Args:
            instruction: The natural language instruction
            path: Optional path to operate on
            metadata: Optional metadata to include with the request
            
        Returns:
            Dictionary with organization results
        """
        if not instruction:
            return {"success": False, "message": "Empty instruction provided", "files_moved": 0}
            
        logger.info(f"Processing instruction: '{instruction}' for path: {path}")
        
        try:
            # Call the organizer
            result = await self.organizer.organize(instruction, path)
            
            # Track the operation in history
            if metadata:
                await self._record_operation(instruction, result, metadata)
                
            return result
        except Exception as e:
            error_msg = f"Error processing natural language instruction: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "files_moved": 0,
                "error": str(e)
            }
    
    async def _record_operation(self, instruction: str, result: Dict[str, Any], metadata: Dict[str, Any]):
        """Record the operation in history for learning and evolution"""
        try:
            # Build the operation record
            operation = {
                "timestamp": metadata.get("timestamp"),
                "instruction": instruction,
                "success": result.get("success", False),
                "files_moved": result.get("files_moved", 0),
                "user": metadata.get("user", "anonymous"),
                "session_id": metadata.get("session_id"),
                "source": metadata.get("source", "api")
            }
            
            # Save to evolution database if the function exists
            if hasattr(self, "record_to_evolution") and callable(self.record_to_evolution):
                await self.record_to_evolution(operation)
            else:
                # Save to local history
                history_file = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "data",
                    "nl_history.jsonl"
                )
                
                os.makedirs(os.path.dirname(history_file), exist_ok=True)
                
                with open(history_file, "a") as f:
                    f.write(json.dumps(operation) + "\n")
        except Exception as e:
            logger.error(f"Error recording operation history: {e}")
    
    def get_examples(self, category: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Get example natural language instructions
        
        Args:
            category: Optional category to filter examples
            
        Returns:
            List of example instructions with descriptions
        """
        # Base examples
        examples = [
            {
                "category": "basic",
                "instruction": "Move all PDFs to the Documents folder and organize them by date",
                "description": "Sorts PDF files into Documents with date-based naming"
            },
            {
                "category": "photos",
                "instruction": "Find images in Downloads and sort them into Photos by year and month",
                "description": "Creates a year/month structure for photos"
            },
            {
                "category": "code",
                "instruction": "Organize code files by language into the Programming folder",
                "description": "Separates code files by language type"
            },
            {
                "category": "cleanup",
                "instruction": "Move large video files older than 30 days to the Archive folder",
                "description": "Archives old video files to free up space"
            },
            {
                "category": "projects",
                "instruction": "Create folders for my projects and move related files into them",
                "description": "Groups related files into project folders"
            },
            {
                "category": "documents",
                "instruction": "Sort documents by type and put them in separate folders",
                "description": "Organizes documents by their file type"
            },
            {
                "category": "music",
                "instruction": "Organize music files by artist and album",
                "description": "Creates artist/album hierarchy for music"
            },
            {
                "category": "downloads",
                "instruction": "Clean up my downloads folder by moving files to appropriate locations",
                "description": "General cleanup of downloads folder by file type"
            }
        ]
        
        # Filter by category if specified
        if category:
            return [ex for ex in examples if ex["category"] == category]
        
        return examples

# Create a singleton instance
_bridge = NLBridge()

async def process_instruction(instruction: str, 
                           path: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Process a natural language instruction (singleton bridge function)
    
    Args:
        instruction: The natural language instruction
        path: Optional path to operate on
        metadata: Optional metadata to include with the request
        
    Returns:
        Dictionary with organization results
    """
    return await _bridge.process_instruction(instruction, path, metadata)

def get_examples(category: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Get example natural language instructions (singleton bridge function)
    
    Args:
        category: Optional category to filter examples
        
    Returns:
        List of example instructions with descriptions
    """
    return _bridge.get_examples(category)
