"""
Configuration management for the file automation tool
"""

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Config:
    """Configuration settings for file automation"""
    
    # File processing settings
    file_types: List[str]
    max_files: int = 100
    
    # Naming and organization settings
    naming_pattern: str = "smart"  # smart, content, timestamp, category
    
    # Operation settings
    dry_run: bool = False
    backup_enabled: bool = True
    copy_files: bool = False  # If True, copy instead of move
    
    # AI settings
    ai_confidence_threshold: float = 0.3
    
    # Directory settings
    create_subdirectories: bool = True
    max_directory_depth: int = 3
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        
        # Normalize file types
        normalized_types = []
        for file_type in self.file_types:
            file_type = file_type.lower().strip()
            if file_type:
                normalized_types.append(file_type)
        
        self.file_types = normalized_types
        
        # Validate naming pattern
        valid_patterns = ["smart", "content", "timestamp", "category"]
        if self.naming_pattern not in valid_patterns:
            self.naming_pattern = "smart"
        
        # Validate numeric settings
        self.max_files = max(1, min(10000, self.max_files))
        self.ai_confidence_threshold = max(0.0, min(1.0, self.ai_confidence_threshold))
        self.max_directory_depth = max(1, min(10, self.max_directory_depth))
