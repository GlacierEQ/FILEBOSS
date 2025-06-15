#!/usr/bin/env python
"""
PhotoPrism Sorting Department

This module implements a multi-agent file sorting system that integrates with PhotoPrism.
It uses two specialized AIs:
1. Fast AI: Quick scanning and categorization
2. Accurate AI: Deep analysis and final naming

Files are sorted hierarchically based on content and renamed with the format:
YYMMDD-[Description Up to 30 Chars]
"""
import os
import sys
import json
import time
import shutil
import logging
import datetime
import re
from typing import Dict, List, Tuple, Set, Optional, Any, Union
from pathlib import Path
import asyncio
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Set up path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configure logging
try:
    from log_manager import get_logger
    logger = get_logger("photoprism_sorter", separate_file=True)
except ImportError:
    # Fall back to standard logging if log_manager is not available
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("photoprism_sorter")

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

# Define hierarchical categories for sorting
HIERARCHICAL_CATEGORIES = {
    "People": ["portrait", "face", "group", "selfie", "person", "people", "family", "child", "baby"],
    "Events": ["wedding", "party", "celebration", "ceremony", "festival", "concert", "graduation", "birthday"],
    "Documents": ["document", "receipt", "invoice", "contract", "form", "certificate", "letter", "resume"],
    "Nature": ["landscape", "mountain", "beach", "forest", "sky", "sunset", "sunrise", "animal", "plant", "flower"],
    "Travel": ["city", "architecture", "building", "monument", "landmark", "hotel", "airport", "vacation"],
    "Food": ["meal", "restaurant", "cooking", "recipe", "dish", "drink", "dessert", "fruit", "vegetable"],
    "Art": ["painting", "drawing", "sculpture", "graffiti", "illustration", "design", "artwork"],
    "Technology": ["computer", "phone", "device", "gadget", "screen", "software", "hardware", "code"],
    "Vehicles": ["car", "motorcycle", "bicycle", "boat", "plane", "train", "transportation"],
    "Miscellaneous": []  # Default category
}

class FileInfo:
    """Represents information about a file for sorting purposes"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.filename = os.path.basename(file_path)
        self.extension = os.path.splitext(file_path)[1].lower()
        self.size = os.path.getsize(file_path)
        self.creation_time = os.path.getctime(file_path)
        self.modification_time = os.path.getmtime(file_path)
        self.content_type = self._determine_content_type()
        self.categories = []
        self.description = ""
        self.date_str = self._get_date_string()
        
    def _determine_content_type(self) -> str:
        """Determine the content type based on file extension"""
        image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".heic"]
        video_extensions = [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv"]
        document_extensions = [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".md"]
        
        if self.extension in image_extensions:
            return "image"
        elif self.extension in video_extensions:
            return "video"
        elif self.extension in document_extensions:
            return "document"
        else:
            return "other"
    
    def _get_date_string(self) -> str:
        """Get date string in YYMMDD format from file metadata"""
        date = datetime.datetime.fromtimestamp(self.creation_time)
        return date.strftime("%y%m%d")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation"""
        return {
            "file_path": self.file_path,
            "filename": self.filename,
            "extension": self.extension,
            "size": self.size,
            "creation_time": self.creation_time,
            "modification_time": self.modification_time,
            "content_type": self.content_type,
            "categories": self.categories,
            "description": self.description,
            "date_str": self.date_str
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FileInfo':
        """Create from dictionary representation"""
        file_info = cls(data["file_path"])
        file_info.categories = data.get("categories", [])
        file_info.description = data.get("description", "")
        return file_info

class FastAI:
    """Fast AI for quick scanning and initial categorization"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.memory = {}  # Dictionary to store previous decisions
        self.memory_limit = 100  # Limit the number of stored decisions
        self.load_memory()
    
    def load_memory(self):
        """Load memory from disk if available"""
        memory_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fast_ai_memory.json")
        if os.path.exists(memory_path):
            try:
                with open(memory_path, "r") as f:
                    self.memory = json.load(f)
                logger.info(f"Loaded Fast AI memory with {len(self.memory)} entries")
            except Exception as e:
                logger.error(f"Error loading Fast AI memory: {e}")
    
    def save_memory(self):
        """Save memory to disk"""
        memory_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fast_ai_memory.json")
        try:
            with open(memory_path, "w") as f:
                json.dump(self.memory, f, indent=2)
            logger.info(f"Saved Fast AI memory with {len(self.memory)} entries")
        except Exception as e:
            logger.error(f"Error saving Fast AI memory: {e}")
    
    def analyze_file(self, file_info: FileInfo) -> FileInfo:
        """Analyze file and provide initial categorization
        
        Args:
            file_info: Information about the file
            
        Returns:
            Updated file info with categories and initial description
        """
        # Check memory for similar files
        filename_pattern = self._get_filename_pattern(file_info.filename)
        if filename_pattern in self.memory:
            # Use previous decision for similar files
            previous_decision = self.memory[filename_pattern]
            file_info.categories = previous_decision["categories"]
            file_info.description = previous_decision["description"]
            logger.info(f"Fast AI: Using previous decision for {file_info.filename}")
            return file_info
        
        # Perform quick analysis based on filename and extension
        categories = self._categorize_by_filename(file_info.filename)
        if not categories:
            categories = self._categorize_by_content_type(file_info.content_type)
        
        # Generate a simple description
        description = self._generate_description(file_info)
        
        # Update file info
        file_info.categories = categories
        file_info.description = description
        
        # Store in memory
        self._update_memory(filename_pattern, {
            "categories": categories,
            "description": description
        })
        
        logger.info(f"Fast AI: Analyzed {file_info.filename} - Categories: {categories}")
        return file_info
    
    def _get_filename_pattern(self, filename: str) -> str:
        """Extract a pattern from filename for memory matching"""
        # Remove numbers and special characters, keep the structure
        pattern = re.sub(r'[0-9]', '#', filename)
        pattern = re.sub(r'[_\-\s]+', '_', pattern)
        return pattern
    
    def _update_memory(self, key: str, value: Dict):
        """Update memory with new decision"""
        self.memory[key] = value
        
        # Trim memory if it exceeds the limit
        if len(self.memory) > self.memory_limit:
            # Remove oldest entries (assuming keys are added in order)
            keys_to_remove = list(self.memory.keys())[:(len(self.memory) - self.memory_limit)]
            for key in keys_to_remove:
                del self.memory[key]
        
        # Save memory to disk
        self.save_memory()
    
    def _categorize_by_filename(self, filename: str) -> List[str]:
        """Categorize file based on filename"""
        filename_lower = filename.lower()
        categories = []
        
        # Check for keywords in filename
        for category, keywords in HIERARCHICAL_CATEGORIES.items():
            for keyword in keywords:
                if keyword.lower() in filename_lower:
                    categories.append(category)
                    break
        
        return categories
    
    def _categorize_by_content_type(self, content_type: str) -> List[str]:
        """Categorize file based on content type"""
        if content_type == "image":
            return ["Nature"]  # Default category for images
        elif content_type == "video":
            return ["Events"]  # Default category for videos
        elif content_type == "document":
            return ["Documents"]  # Default category for documents
        else:
            return ["Miscellaneous"]  # Default category for other files
    
    def _generate_description(self, file_info: FileInfo) -> str:
        """Generate a simple description based on filename and type"""
        # Remove extension and special characters
        base_name = os.path.splitext(file_info.filename)[0]
        base_name = re.sub(r'[_\-\s]+', ' ', base_name)
        
        # Limit to 30 characters
        if len(base_name) > 30:
            base_name = base_name[:27] + "..."
        
        return base_name

class AccurateAI:
    """Accurate AI for deep analysis and final naming"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.memory = {}  # Dictionary to store previous decisions
        self.memory_limit = 200  # Limit the number of stored decisions
        self.load_memory()
    
    def load_memory(self):
        """Load memory from disk if available"""
        memory_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "accurate_ai_memory.json")
        if os.path.exists(memory_path):
            try:
                with open(memory_path, "r") as f:
                    self.memory = json.load(f)
                logger.info(f"Loaded Accurate AI memory with {len(self.memory)} entries")
            except Exception as e:
                logger.error(f"Error loading Accurate AI memory: {e}")
    
    def save_memory(self):
        """Save memory to disk"""
        memory_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "accurate_ai_memory.json")
        try:
            with open(memory_path, "w") as f:
                json.dump(self.memory, f, indent=2)
            logger.info(f"Saved Accurate AI memory with {len(self.memory)} entries")
        except Exception as e:
            logger.error(f"Error saving Accurate AI memory: {e}")
    
    def analyze_file(self, file_info: FileInfo, fast_ai_result: FileInfo) -> FileInfo:
        """Perform deep analysis on file and finalize categorization and naming
        
        Args:
            file_info: Original file information
            fast_ai_result: Results from Fast AI analysis
            
        Returns:
            Updated file info with final categories and description
        """
        # Start with Fast AI results
        file_info.categories = fast_ai_result.categories
        file_info.description = fast_ai_result.description
        
        # Check memory for exact matches
        file_hash = self._get_file_hash(file_info.file_path)
        if file_hash and file_hash in self.memory:
            # Use previous decision for exact file
            previous_decision = self.memory[file_hash]
            file_info.categories = previous_decision["categories"]
            file_info.description = previous_decision["description"]
            logger.info(f"Accurate AI: Using previous decision for {file_info.filename}")
            return file_info
        
        # Perform deeper analysis
        self._analyze_content(file_info)
        
        # Refine categories
        self._refine_categories(file_info)
        
        # Generate better description
        self._refine_description(file_info)
        
        # Store in memory
        if file_hash:
            self._update_memory(file_hash, {
                "categories": file_info.categories,
                "description": file_info.description
            })
        
        logger.info(f"Accurate AI: Analyzed {file_info.filename} - Categories: {file_info.categories}")
        return file_info
    
    def _get_file_hash(self, file_path: str) -> Optional[str]:
        """Generate a hash for the file content"""
        try:
            import hashlib
            with open(file_path, "rb") as f:
                file_hash = hashlib.md5()
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    file_hash.update(chunk)
            return file_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error generating file hash: {e}")
            return None
    
    def _update_memory(self, key: str, value: Dict):
        """Update memory with new decision"""
        self.memory[key] = value
        
        # Trim memory if it exceeds the limit
        if len(self.memory) > self.memory_limit:
            # Remove oldest entries (assuming keys are added in order)
            keys_to_remove = list(self.memory.keys())[:(len(self.memory) - self.memory_limit)]
            for key in keys_to_remove:
                del self.memory[key]
        
        # Save memory to disk
        self.save_memory()
    
    def _analyze_content(self, file_info: FileInfo):
        """Analyze file content for better categorization"""
        # This would ideally use more sophisticated content analysis
        # For now, we'll use a simplified approach based on file type
        
        if file_info.content_type == "image":
            # For images, we could use image recognition
            # Here we'll just use a more sophisticated filename analysis
            self._analyze_image(file_info)
        elif file_info.content_type == "document":
            # For documents, we could extract text and analyze it
            self._analyze_document(file_info)
        elif file_info.content_type == "video":
            # For videos, we could analyze metadata or frames
            self._analyze_video(file_info)
    
    def _analyze_image(self, file_info: FileInfo):
        """Analyze image content"""
        # In a real implementation, this would use image recognition
        # For now, we'll use a more sophisticated filename analysis
        filename_lower = file_info.filename.lower()
        
        # Check for specific image types
        if any(keyword in filename_lower for keyword in ["dsc", "img", "photo"]):
            if "People" not in file_info.categories:
                file_info.categories.append("People")
        
        # Check for screenshot indicators
        if any(keyword in filename_lower for keyword in ["screenshot", "screen", "capture"]):
            if "Technology" not in file_info.categories:
                file_info.categories.append("Technology")
    
    def _analyze_document(self, file_info: FileInfo):
        """Analyze document content"""
        # In a real implementation, this would extract and analyze text
        # For now, we'll use filename patterns
        filename_lower = file_info.filename.lower()
        
        # Check for specific document types
        if any(keyword in filename_lower for keyword in ["invoice", "receipt", "bill"]):
            if "Documents" not in file_info.categories:
                file_info.categories.append("Documents")
        
        # Check for work-related documents
        if any(keyword in filename_lower for keyword in ["report", "memo", "meeting", "presentation"]):
            if "Documents" not in file_info.categories:
                file_info.categories.append("Documents")
    
    def _analyze_video(self, file_info: FileInfo):
        """Analyze video content"""
        # In a real implementation, this would analyze video metadata or frames
        # For now, we'll use filename patterns
        filename_lower = file_info.filename.lower()
        
        # Check for specific video types
        if any(keyword in filename_lower for keyword in ["trip", "travel", "vacation"]):
            if "Travel" not in file_info.categories:
                file_info.categories.append("Travel")
        
        # Check for event videos
        if any(keyword in filename_lower for keyword in ["party", "celebration", "wedding", "birthday"]):
            if "Events" not in file_info.categories:
                file_info.categories.append("Events")
    
    def _refine_categories(self, file_info: FileInfo):
        """Refine categories based on deeper analysis"""
        # Ensure we have at least one category
        if not file_info.categories:
            file_info.categories = ["Miscellaneous"]
        
        # Limit to at most 2 categories, prioritizing more specific ones
        if len(file_info.categories) > 2:
            # Prioritize categories that are not Miscellaneous
            non_misc_categories = [c for c in file_info.categories if c != "Miscellaneous"]
            if non_misc_categories:
                file_info.categories = non_misc_categories[:2]
            else:
                file_info.categories = file_info.categories[:2]
    
    def _refine_description(self, file_info: FileInfo):
        """Generate a better description based on deep analysis"""
        # Start with the existing description
        description = file_info.description
        
        # Add category information if not already in the description
        for category in file_info.categories:
            if category.lower() not in description.lower() and category != "Miscellaneous":
                if len(description) + len(category) + 3 <= 30:
                    description = f"{category}-{description}"
                break
        
        # Ensure description is not too long
        if len(description) > 30:
            description = description[:27] + "..."
        
        file_info.description = description

class PhotoPrismSorter:
    """Main class for PhotoPrism file sorting"""
    
    def __init__(self, config: Dict = None):
        self.config = config or self._load_default_config()
        self.fast_ai = FastAI(self.config.get("fast_ai", {}))
        self.accurate_ai = AccurateAI(self.config.get("accurate_ai", {}))
        
        # Create sorting department directory if it doesn't exist
        self.sorting_dept_path = self.config["sorting_department_path"]
        os.makedirs(self.sorting_dept_path, exist_ok=True)
        
        # Create memory directory for AIs
        memory_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        os.makedirs(memory_dir, exist_ok=True)
        
        # Initialize PhotoPrism API client
        self.photoprism_url = self.config.get("photoprism_url")
        self.photoprism_username = self.config.get("photoprism_username")
        self.photoprism_password = self.config.get("photoprism_password")
        self.photoprism_session = None
        
        if self.photoprism_url:
            self._init_photoprism_session()
    
    def _load_default_config(self) -> Dict:
        """Load default configuration"""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        # Default configuration
        return {
            "sorting_department_path": os.path.join(os.path.expanduser("~"), "PhotoPrism", "storage", "sorting-dept"),
            "photoprism_url": "http://localhost:2342",
            "photoprism_username": "admin",
            "photoprism_password": "admin",
            "fast_ai": {
                "memory_limit": 100
            },
            "accurate_ai": {
                "memory_limit": 200
            }
        }
    
    def _init_photoprism_session(self):
        """Initialize PhotoPrism API session"""
        try:
            self.photoprism_session = requests.Session()
            
            # Login to PhotoPrism
            login_url = f"{self.photoprism_url}/api/v1/session"
            login_data = {
                "username": self.photoprism_username,
                "password": self.photoprism_password
            }
            
            response = self.photoprism_session.post(login_url, json=login_data)
            if response.status_code == 200:
                logger.info("Successfully logged in to PhotoPrism API")
            else:
                logger.error(f"Failed to login to PhotoPrism API: {response.status_code}")
                self.photoprism_session = None
        except Exception as e:
            logger.error(f"Error initializing PhotoPrism session: {e}")
            self.photoprism_session = None
    
    def process_file(self, file_path: str) -> Dict:
        """Process a single file
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            Dictionary with processing results
        """
        start_time = time.time()
        
        try:
            # Create file info
            file_info = FileInfo(file_path)
            
            # Fast AI analysis
            fast_ai_start = time.time()
            fast_ai_result = self.fast_ai.analyze_file(file_info)
            fast_ai_time = time.time() - fast_ai_start
            
            # Accurate AI analysis
            accurate_ai_start = time.time()
            final_result = self.accurate_ai.analyze_file(file_info, fast_ai_result)
            accurate_ai_time = time.time() - accurate_ai_start
            
            # Generate new filename
            new_filename = self._generate_filename(final_result)
            
            # Determine destination path
            destination_path = self._get_destination_path(final_result)
            
            # Move and rename file
            os.makedirs(destination_path, exist_ok=True)
            new_file_path = os.path.join(destination_path, new_filename)
            
            # Handle filename conflicts
            if os.path.exists(new_file_path):
                base_name, extension = os.path.splitext(new_filename)
                counter = 1
                while os.path.exists(os.path.join(destination_path, f"{base_name}_{counter}{extension}")):
                    counter += 1
                new_filename = f"{base_name}_{counter}{extension}"
                new_file_path = os.path.join(destination_path, new_filename)
            
            # Move the file
            shutil.move(file_path, new_file_path)
            
            # Update PhotoPrism index if configured
            if self.photoprism_session:
                self._update_photoprism_index(new_file_path)
            
            total_time = time.time() - start_time
            
            result = {
                "success": True,
                "original_path": file_path,
                "new_path": new_file_path,
                "categories": final_result.categories,
                "description": final_result.description,
                "fast_ai_time": fast_ai_time,
                "accurate_ai_time": accurate_ai_time,
                "total_time": total_time
            }
            
            logger.info(f"Processed file: {file_path} -> {new_file_path}")
            return result
        
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return {
                "success": False,
                "original_path": file_path,
                "error": str(e)
            }
    
    def _generate_filename(self, file_info: FileInfo) -> str:
        """Generate new filename in the format YYMMDD-[Description]
        
        Args:
            file_info: File information
            
        Returns:
            New filename
        """
        # Get date string
        date_str = file_info.date_str
        
        # Clean up description (remove invalid characters)
        description = re.sub(r'[<>:"/\\|?*]', '', file_info.description)
        
        # Ensure description is not too long
        if len(description) > 30:
            description = description[:27] + "..."
        
        # Get file extension
        _, extension = os.path.splitext(file_info.filename)
        
        # Generate new filename
        return f"{date_str}-{description}{extension}"
    
    def _get_destination_path(self, file_info: FileInfo) -> str:
        """Determine destination path based on categories
        
        Args:
            file_info: File information
            
        Returns:
            Destination path
        """
        # Start with sorting department path
        base_path = self.sorting_dept_path
        
        # Use first category as main folder
        if file_info.categories:
            main_category = file_info.categories[0]
        else:
            main_category = "Miscellaneous"
        
        # Create hierarchical path
        destination_path = os.path.join(base_path, main_category)
        
        # Add subcategory if available
        if len(file_info.categories) > 1:
            subcategory = file_info.categories[1]
            destination_path = os.path.join(destination_path, subcategory)
        
        # Add year-month folder based on file date
        date = datetime.datetime.fromtimestamp(file_info.creation_time)
        year_month = date.strftime("%Y-%m")
        destination_path = os.path.join(destination_path, year_month)
        
        return destination_path
    
    def _update_photoprism_index(self, file_path: str):
        """Update PhotoPrism index for the new file
        
        Args:
            file_path: Path to the file
        """
        if not self.photoprism_session:
            return
        
        try:
            # Get the directory containing the file
            directory = os.path.dirname(file_path)
            
            # Call PhotoPrism index API
            index_url = f"{self.photoprism_url}/api/v1/index"
            index_data = {
                "path": directory
            }
            
            response = self.photoprism_session.post(index_url, json=index_data)
            if response.status_code == 200:
                logger.info(f"Successfully indexed directory in PhotoPrism: {directory}")
            else:
                logger.error(f"Failed to index directory in PhotoPrism: {response.status_code}")
        except Exception as e:
            logger.error(f"Error updating PhotoPrism index: {e}")

class SortingDepartmentWatcher(FileSystemEventHandler):
    """Watches the sorting department directory for new files"""
    
    def __init__(self, sorter: PhotoPrismSorter):
        self.sorter = sorter
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        logger.info(f"New file detected: {event.src_path}")
        self.sorter.process_file(event.src_path)

def start_watcher(config: Dict = None):
    """Start the sorting department watcher
    
    Args:
        config: Optional configuration dictionary
    """
    sorter = PhotoPrismSorter(config)
    watcher = SortingDepartmentWatcher(sorter)
    
    observer = Observer()
    observer.schedule(watcher, sorter.sorting_dept_path, recursive=False)
    observer.start()
    
    logger.info(f"Started watching sorting department: {sorter.sorting_dept_path}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="PhotoPrism Sorting Department")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--file", help="Process a single file")
    
    args = parser.parse_args()
    
    config = None
    if args.config:
        try:
            with open(args.config, "r") as f:
                config = json.load(f)
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
    
    sorter = PhotoPrismSorter(config)
    
    if args.file:
        result = sorter.process_file(args.file)
        print(json.dumps(result, indent=2))
    else:
        start_watcher(config)
