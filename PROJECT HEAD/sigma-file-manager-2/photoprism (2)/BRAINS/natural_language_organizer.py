#!/usr/bin/env python
"""
Natural Language Organizer for Sorting Hat

This module enables users to organize files using plain English commands.
It parses natural language instructions, extracts organization rules and
executes them with the core Sorting Hat engine.

Examples of natural language commands:
- "Move all PDFs to the Documents folder and name them by date"
- "Create folders for photos by year and month, then organize all images"
- "Find all code files and sort them by language in the Programming folder"
"""
import os
import sys
import re
import json
import time
import asyncio
import inspect
import logging
from typing import Dict, List, Tuple, Set, Optional, Any, Union
from pathlib import Path

try:
    import groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# Set up logging with the centralized log manager
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from log_manager import get_logger
    logger = get_logger("natural_organizer", separate_file=True)
except ImportError:
    # Fall back to standard logging if log_manager is not available
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("natural_organizer")

# Import safe path utilities
try:
    from safe_paths import SafePaths
except ImportError:
    # Fall back to basic path safety if SafePaths is not available
    class SafePaths:
        DEFAULT_SAFE_PATH = os.path.join(os.path.expanduser("~"), "OrganizeFolder")
        
        @staticmethod
        def is_github_path(path):
            if not path:
                return False
            norm_path = os.path.normpath(str(path)).lower()
            return "github" in norm_path
        
        @staticmethod
        def get_safe_path(path=None):
            if path and os.path.exists(path) and not SafePaths.is_github_path(path):
                return path
            if not os.path.exists(SafePaths.DEFAULT_SAFE_PATH):
                os.makedirs(SafePaths.DEFAULT_SAFE_PATH, exist_ok=True)
            return SafePaths.DEFAULT_SAFE_PATH

# Define file type mapping for natural language references
FILE_TYPE_MAPPING = {
    # Documents
    "document": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt"],
    "pdf": [".pdf"],
    "word": [".doc", ".docx"],
    "text": [".txt", ".md", ".log"],
    
    # Images
    "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"],
    "photo": [".jpg", ".jpeg", ".png", ".heic"],
    "screenshot": [".png", ".jpg", ".jpeg"],
    
    # Audio/Video
    "video": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv"],
    "audio": [".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a"],
    "music": [".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a"],
    
    # Code
    "code": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".h", ".php", ".go", ".rb"],
    "python": [".py", ".ipynb"],
    "javascript": [".js", ".jsx", ".ts", ".tsx"],
    "web": [".html", ".css", ".js", ".php"],
    
    # Data
    "data": [".csv", ".json", ".xml", ".xlsx", ".xls"],
    "spreadsheet": [".xlsx", ".xls", ".csv", ".ods"],
    "database": [".db", ".sqlite", ".sql"],
    
    # Archives
    "archive": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "compressed": [".zip", ".rar", ".7z", ".tar.gz", ".tgz"],
    
    # Executables
    "executable": [".exe", ".msi", ".app", ".dmg"],
    "installer": [".exe", ".msi", ".pkg", ".deb", ".rpm"],
    
    # Generic
    "download": ["*"]  # Special case - handled differently
}

# Time-related keywords for parsing
TIME_KEYWORDS = {
    "today": 0,
    "yesterday": 1,
    "last week": 7,
    "last month": 30,
    "recent": 7,
    "old": 90,
    "older than": None,  # Special case - needs a number
    "newer than": None,  # Special case - needs a number
    "this year": None,  # Special case - current year
    "last year": None,  # Special case - previous year
}

class NLOrganizationRule:
    """Represents a single organization rule parsed from natural language"""
    
    def __init__(self):
        self.file_types = set()         # Extensions to match
        self.source_path = None         # Where to look for files
        self.destination_path = None    # Where to move files
        self.name_pattern = None        # How to rename files
        self.date_filter = None         # Time-based filter
        self.content_filter = None      # Content-based filter
        self.size_filter = None         # Size-based filter
        self.priority = 1               # Rule priority (higher = more specific)
        self.recursive = False          # Whether to search recursively
        
    def to_dict(self) -> Dict:
        """Convert rule to dictionary representation"""
        return {
            "file_types": list(self.file_types),
            "source_path": self.source_path,
            "destination_path": self.destination_path,
            "name_pattern": self.name_pattern,
            "date_filter": self.date_filter,
            "content_filter": self.content_filter,
            "size_filter": self.size_filter,
            "priority": self.priority,
            "recursive": self.recursive
        }
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'NLOrganizationRule':
        """Create rule from dictionary representation"""
        rule = cls()
        rule.file_types = set(data.get("file_types", []))
        rule.source_path = data.get("source_path")
        rule.destination_path = data.get("destination_path")
        rule.name_pattern = data.get("name_pattern")
        rule.date_filter = data.get("date_filter")
        rule.content_filter = data.get("content_filter")
        rule.size_filter = data.get("size_filter")
        rule.priority = data.get("priority", 1)
        rule.recursive = data.get("recursive", False)
        return rule

class NaturalLanguageParser:
    """Parses natural language instructions into organization rules"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.base_dir, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.api_key = self._get_api_key()
        self.client = None
        if self.api_key and GROQ_AVAILABLE:
            self.client = groq.Client(api_key=self.api_key)
            
    def _get_api_key(self) -> Optional[str]:
        """Get the API key from environment or file"""
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key:
            return api_key
            
        # Try reading from .env file
        env_path = os.path.join(self.base_dir, ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith("GROQ_API_KEY="):
                        return line.split("=", 1)[1].strip()
        
        return None
    
    async def parse_instruction(self, instruction: str) -> List[NLOrganizationRule]:
        """Parse a natural language instruction into organization rules"""
        logger.info(f"Parsing instruction: {instruction}. Attempting to extract organization rules.")

        
        if not instruction:
            logger.warning("Empty instruction provided. Please provide a valid command.")

            return []
            
        # Try using AI-based parsing first
        if self.client:
            try:
                rules = await self._parse_with_ai(instruction)
                if rules:
                    return rules
            except Exception as e:
                logger.error(f"AI parsing failed: {e}. Falling back to rule-based parsing.")

        
        # Fall back to rule-based parsing if AI not available or fails
        return self._parse_with_rules(instruction)
    
    async def _parse_with_ai(self, instruction: str) -> List[NLOrganizationRule]:
        """Parse instruction using AI language model"""
        system_prompt = """
You are a file organization expert that converts natural language instructions into structured file organization rules.
Extract precise organization rules from the user's instructions, accounting for:
1. File types (extensions or categories like documents, images, etc.)
2. Source locations (where to look for files)
3. Destination locations (where to move files)
4. Naming patterns (how files should be renamed)
5. Date-based filters (time constraints or file age)
6. Content-based filters (text or properties within files)
7. Size-based filters (file size constraints)

Respond with a JSON array of rule objects with these fields:
- file_types: array of file extensions to match (with dots, e.g. [".pdf", ".jpg"])
- source_path: string path where to look for files
- destination_path: string path where to move matched files
- name_pattern: string pattern for renaming (null if no renaming)
- date_filter: object with date constraints or null
- content_filter: string content to match or null
- size_filter: object with size constraints or null
- priority: number 1-10 indicating rule specificity (higher = more specific)
- recursive: boolean whether to search subdirectories

Example response:
```json
[
  {
    "file_types": [".pdf", ".doc", ".docx"],
    "source_path": "Downloads",
    "destination_path": "Documents/Work",
    "name_pattern": "{date}_{filename}",
    "date_filter": {"newer_than_days": 7},
    "content_filter": null,
    "size_filter": null,
    "priority": 3,
    "recursive": true
  }
]
```
"""

        logger.info("Using AI to parse instruction")
        try:
            # Make API call to Groq
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": instruction}
                ],
                model="llama-3.1-70b-versatile",
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            response_text = completion.choices[0].message.content
            response_json = json.loads(response_text)
            
            # Convert to rule objects
            rules = []
            for rule_data in response_json:
                rule = NLOrganizationRule()
                rule.file_types = set(rule_data.get("file_types", []))
                rule.source_path = rule_data.get("source_path")
                rule.destination_path = rule_data.get("destination_path")
                rule.name_pattern = rule_data.get("name_pattern")
                rule.date_filter = rule_data.get("date_filter")
                rule.content_filter = rule_data.get("content_filter")
                rule.size_filter = rule_data.get("size_filter")
                rule.priority = rule_data.get("priority", 1)
                rule.recursive = rule_data.get("recursive", False)
                rules.append(rule)
            
            logger.info(f"AI parsing generated {len(rules)} rules")
            return rules
        except Exception as e:
            logger.error(f"Error in AI parsing: {str(e)}")
            return []
    
    def _parse_with_rules(self, instruction: str) -> List[NLOrganizationRule]:
        """Parse instruction using rule-based approach (fallback)"""
        logger.info("Using rule-based parsing for instruction. Attempting to detect file types and paths.")

        rules = []
        
        # Basic rule creation
        rule = NLOrganizationRule()
        
        # Default source path is Downloads
        rule.source_path = "Downloads"
        
        # Detect file types
        for file_type, extensions in FILE_TYPE_MAPPING.items():
            if file_type.lower() in instruction.lower():
                rule.file_types.update(extensions)
        
        # If no file types detected, default to all files
        if not rule.file_types:
            rule.file_types = {"*"}
        
        # Parse destination path
        destination_match = re.search(r"to (?:the |my )?([\w/\\]+) folder", instruction, re.IGNORECASE)
        if destination_match:
            rule.destination_path = destination_match.group(1)
        
        # Check for rename instructions
        if "rename" in instruction.lower() or "name" in instruction.lower():
            if "date" in instruction.lower():
                rule.name_pattern = "{date}_{filename}"
            elif "number" in instruction.lower() or "sequence" in instruction.lower():
                rule.name_pattern = "{counter}_{filename}"
        
        # Check for recursive search
        rule.recursive = "all" in instruction.lower() or "recursive" in instruction.lower()
        
        # Set default destination if none specified
        if not rule.destination_path:
            # Use first file type as destination folder
            if rule.file_types and "*" not in rule.file_types:
                first_type = next(iter(rule.file_types))
                if first_type.startswith("."):
                    first_type = first_type[1:]
                rule.destination_path = first_type.capitalize() + "s"
            else:
                rule.destination_path = "Organized"
        
        rules.append(rule)
        logger.info(f"Rule-based parsing generated {len(rules)} rules")
        return rules

class NaturalLanguageOrganizer:
    """Main organizer that applies parsed rules to files"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.parser = NaturalLanguageParser()
        
    async def organize(self, instruction: str, base_path: Optional[str] = None) -> Dict[str, Any]:
        """Organize files based on natural language instruction
        
        Args:
            instruction: Natural language instruction
            base_path: Optional base path to start from (defaults to safe path)
            
        Returns:
            Dictionary with organization results
        """
        start_time = time.time()
        
        # Get safe base path
        if base_path:
            safe_path = SafePaths.get_safe_path(base_path)
        else:
            safe_path = SafePaths.DEFAULT_SAFE_PATH
        
        logger.info(f"Starting organization with base path: {safe_path}")
        
        # Parse the instruction into rules
        rules = await self.parser.parse_instruction(instruction)
        if not rules:
            return {"success": False, "message": "Could not parse instruction", "files_moved": 0}
        
        # Process rules and move files
        total_moved = 0
        actions = []
        
        for rule in rules:
            source_path = rule.source_path
            
            # Handle relative/absolute paths
            if not os.path.isabs(source_path):
                source_path = os.path.join(safe_path, source_path)
            
            # Verify source path is within safe path
            if not source_path.startswith(safe_path) and SafePaths.is_github_path(source_path):
                logger.warning(f"Source path outside of safe path: {source_path}")
                continue
                
            if not os.path.exists(source_path):
            logger.warning(f"Source path does not exist: {source_path}. Please check the path and try again.")

                continue
            
            # Apply rule to files
            files_moved = await self._process_rule(rule, source_path, safe_path)
            total_moved += len(files_moved)
            actions.extend(files_moved)
        
        execution_time = time.time() - start_time
        
        result = {
            "success": True,
            "message": f"Organized {total_moved} files according to instruction",
            "files_moved": total_moved,
            "actions": actions,
            "execution_time": execution_time
        }
        
        logger.info(f"Organization complete: {result['message']}")
        return result
    
    async def _process_rule(self, rule: NLOrganizationRule, source_path: str, base_path: str) -> List[Dict]:
        """Process a single organization rule
        
        Args:
            rule: The rule to apply
            source_path: Source path to look for files
            base_path: Base safe path
            
        Returns:
            List of actions performed (files moved)
        """
        files_moved = []
        
        # Build destination path
        dest_path = rule.destination_path
        if not os.path.isabs(dest_path):
            dest_path = os.path.join(base_path, dest_path)
            
        # Ensure destination exists
        os.makedirs(dest_path, exist_ok=True)
        
        # Find matching files
        matching_files = self._find_matching_files(rule, source_path)
        
        # Move each file
        for src_file in matching_files:
            # Generate destination filename
            filename = os.path.basename(src_file)
            if rule.name_pattern:
                filename = self._apply_name_pattern(rule.name_pattern, filename, src_file)
                
            dst_file = os.path.join(dest_path, filename)
            
            # Handle filename conflicts
            if os.path.exists(dst_file):
                base, ext = os.path.splitext(dst_file)
                counter = 1
                while os.path.exists(f"{base}_{counter}{ext}"):
                    counter += 1
                dst_file = f"{base}_{counter}{ext}"
            
            # Move the file
            try:
                # Create containing folder if needed
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                
                # Move file
                shutil.move(src_file, dst_file)
                
                # Record action
                files_moved.append({
                    "source": src_file,
                    "destination": dst_file,
                    "success": True
                })
                logger.info(f"Moved file: {src_file} -> {dst_file}")
            except Exception as e:
                files_moved.append({
                    "source": src_file,
                    "destination": dst_file,
                    "success": False,
                    "error": str(e)
                })
                logger.error(f"Failed to move file {src_file}: {e}")
        
        return files_moved
    
    def _find_matching_files(self, rule: NLOrganizationRule, source_path: str) -> List[str]:
        """Find files matching the rule criteria
        
        Args:
            rule: The rule to apply
            source_path: Source path to look for files
            
        Returns:
            List of matching file paths
        """
        matching_files = []
        
        # Walk through directory (recursive or not)
        if rule.recursive:
            for root, _, files in os.walk(source_path):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    if self._file_matches_rule(file_path, rule):
                        matching_files.append(file_path)
        else:
            # Non-recursive mode
            for filename in os.listdir(source_path):
                file_path = os.path.join(source_path, filename)
                if os.path.isfile(file_path) and self._file_matches_rule(file_path, rule):
                    matching_files.append(file_path)
        
        return matching_files
    
    def _file_matches_rule(self, file_path: str, rule: NLOrganizationRule) -> bool:
        """Check if a file matches the rule criteria
        
        Args:
            file_path: Path to the file
            rule: The rule to check against
            
        Returns:
            True if file matches all criteria, False otherwise
        """
        # Check file extension
        _, ext = os.path.splitext(file_path.lower())
        if "*" not in rule.file_types and ext not in rule.file_types:
            return False
        
        # Check date filter
        if rule.date_filter:
            file_time = os.path.getmtime(file_path)
            if not self._matches_date_filter(file_time, rule.date_filter):
                return False
        
        # Check content filter
        if rule.content_filter and not self._matches_content_filter(file_path, rule.content_filter):
            return False
        
        # Check size filter
        if rule.size_filter:
            file_size = os.path.getsize(file_path)
            if not self._matches_size_filter(file_size, rule.size_filter):
                return False
        
        return True
    
    def _matches_date_filter(self, file_time: float, date_filter: Dict) -> bool:
        """Check if a file's modification time matches the date filter
        
        Args:
            file_time: File modification timestamp
            date_filter: Date filter specification
            
        Returns:
            True if file matches the date filter
        """
        now = time.time()
        
        if "newer_than_days" in date_filter:
            days = date_filter["newer_than_days"]
            return now - file_time < days * 86400  # seconds in a day
            
        if "older_than_days" in date_filter:
            days = date_filter["older_than_days"]
            return now - file_time > days * 86400
            
        return True
    
    def _matches_content_filter(self, file_path: str, content_filter: str) -> bool:
        """Check if a file's content matches the content filter
        
        Args:
            file_path: Path to the file
            content_filter: Content filter specification
            
        Returns:
            True if file matches the content filter
        """
        # Only check text-based files
        _, ext = os.path.splitext(file_path.lower())
        text_extensions = [".txt", ".md", ".py", ".js", ".html", ".css", ".json", ".xml", ".csv"]
        
        if ext not in text_extensions:
            return False
            
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                return content_filter.lower() in content.lower()
        except Exception:
            return False
    
    def _matches_size_filter(self, file_size: int, size_filter: Dict) -> bool:
        """Check if a file's size matches the size filter
        
        Args:
            file_size: File size in bytes
            size_filter: Size filter specification
            
        Returns:
            True if file matches the size filter
        """
        if "min_bytes" in size_filter and file_size < size_filter["min_bytes"]:
            return False
            
        if "max_bytes" in size_filter and file_size > size_filter["max_bytes"]:
            return False
            
        return True
    
    def _apply_name_pattern(self, pattern: str, filename: str, file_path: str) -> str:
        """Apply naming pattern to a file
        
        Args:
            pattern: Naming pattern
            filename: Original filename
            file_path: Path to the file
            
        Returns:
            New filename based on pattern
        """
        # Get file info
        name, ext = os.path.splitext(filename)
        mod_time = os.path.getmtime(file_path)
        mod_date = time.strftime("%Y-%m-%d", time.localtime(mod_time))
        file_size = os.path.getsize(file_path)
        
        # Replace placeholders
        result = pattern.replace("{filename}", name)
        result = result.replace("{extension}", ext[1:] if ext.startswith('.') else ext)
        result = result.replace("{ext}", ext)
        result = result.replace("{date}", mod_date)
        result = result.replace("{size}", str(file_size))
        
        # Add extension if not included in pattern
        if not result.endswith(ext):
            result += ext
            
        return result

# API functions for the FastAPI server
async def handle_natural_language_command(instruction: str, path: Optional[str] = None) -> Dict[str, Any]:
    """Handle a natural language organization command
    
    Args:
        instruction: Natural language instruction
        path: Optional base path to start from
        
    Returns:
        Dictionary with organization results
    """
    organizer = NaturalLanguageOrganizer()
    result = await organizer.organize(instruction, path)
    return result

# Command-line interface
def main():
    """Command-line interface for testing the natural language organizer"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Organize files using natural language commands")
    parser.add_argument("instruction", help="Natural language instruction for file organization")
    parser.add_argument("--path", "-p", help="Base path to start organization from")
    
    args = parser.parse_args()
    
    loop = asyncio.get_event_loop()
    organizer = NaturalLanguageOrganizer()
    result = loop.run_until_complete(organizer.organize(args.instruction, args.path))
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    # Required imports for standalone use
    import shutil
    main()
