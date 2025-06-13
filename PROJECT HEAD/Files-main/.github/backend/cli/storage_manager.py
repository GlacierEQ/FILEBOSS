#!/usr/bin/env python3
"""
CodexFlō Storage Manager
Handles file organization, storage, and retrieval
"""

import logging
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import os

logger = logging.getLogger(__name__)

class StorageManager:
    """Manages file storage, organization, and retrieval"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_path = Path(config.get("storage", {}).get("base_path", "./storage"))
        self.backup_enabled = config.get("storage", {}).get("backup_enabled", False)
        self.encryption_enabled = config.get("security", {}).get("encryption_enabled", False)
        
        # Create base directories
        self._init_storage_structure()
        
    def _init_storage_structure(self):
        """Initialize storage directory structure"""
        try:
            # Create base directory
            self.base_path.mkdir(parents=True, exist_ok=True)
            
            # Create standard subdirectories
            for subdir in ["cases", "documents", "entities", "exports", "temp", "backups"]:
                (self.base_path / subdir).mkdir(exist_ok=True)
                
            logger.info(f"Storage structure initialized at {self.base_path}")
        except Exception as e:
            logger.error(f"Error initializing storage structure: {e}")
            raise
            
    async def organize_file(self, file_path: Path, metadata: Dict[str, Any], legal_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Organize a file based on its metadata"""
        result = {
            "original_path": str(file_path),
            "organized_path": None,
            "metadata_path": None,
            "backup_path": None,
            "status": "pending"
        }
        
        try:
            # Determine file type and category
            file_type = metadata.get("type", "unknown")
            
            # Determine organization path
            org_path = await self._determine_organization_path(file_path, metadata, legal_metadata)
            org_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate standardized filename
            new_filename = await self._generate_standardized_filename(file_path, metadata, legal_metadata)
            target_path = org_path / new_filename
            
            # Handle filename conflicts
            counter = 1
            while target_path.exists():
                name_parts = new_filename.split(".")
                if len(name_parts) > 1:
                    ext = "." + name_parts[-1]
                    base = ".".join(name_parts[:-1])
                else:
                    ext = ""
                    base = new_filename
                    
                target_path = org_path / f"{base}_v{counter}{ext}"
                counter += 1
            
            # Create backup if enabled
            if self.backup_enabled:
                backup_path = self.base_path / "backups" / file_path.name
                shutil.copy2(file_path, backup_path)
                result["backup_path"] = str(backup_path)
            
            # Copy file to organized location
            shutil.copy2(file_path, target_path)
            result["organized_path"] = str(target_path)
            
            # Create metadata sidecar file
            metadata_path = target_path.with_suffix(target_path.suffix + ".meta.json")
            combined_metadata = {
                "file_metadata": metadata,
                "legal_metadata": legal_metadata or {},
                "organization": {
                    "original_path": str(file_path),
                    "organized_path": str(target_path),
                    "organization_time": datetime.now().isoformat()
                }
            }
            
            with open(metadata_path, 'w') as f:
                json.dump(combined_metadata, f, indent=2)
                
            result["metadata_path"] = str(metadata_path)
            result["status"] = "organized"
            
            return result
            
        except Exception as e:
            logger.error(f"Error organizing file {file_path}: {e}")
            result["status"] = "error"
            result["error"] = str(e)
            return result
            
    async def retrieve_file(self, file_id: str) -> Dict[str, Any]:
        """Retrieve a file by its ID"""
        # In a real implementation, this would look up the file in a database
        # Placeholder implementation
        return {"error": "Not implemented"}
            
    async def generate_usage_report(self) -> Dict[str, Any]:
        """Generate storage usage report"""
        report = {
            "total_size": 0,
            "file_count": 0,
            "by_type": {},
            "by_category": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Calculate storage usage
            for item in self.base_path.rglob("*"):
                if item.is_file():
                    # Skip metadata files
                    if item.suffix.endswith(".meta.json"):
                        continue
                        
                    size = item.stat().st_size
                    report["total_size"] += size
                    report["file_count"] += 1
                    
                    # Categorize by file type
                    file_type = item.suffix.lower().lstrip(".")
                    if not file_type:
                        file_type = "unknown"
                        
                    if file_type not in report["by_type"]:
                        report["by_type"][file_type] = {"count": 0, "size": 0}
                        
                    report["by_type"][file_type]["count"] += 1
                    report["by_type"][file_type]["size"] += size
                    
                    # Categorize by directory
                    category = item.parent.name
                    if category not in report["by_category"]:
                        report["by_category"][category] = {"count": 0, "size": 0}
                        
                    report["by_category"][category]["count"] += 1
                    report["by_category"][category]["size"] += size
            
            # Convert bytes to human-readable format
            report["total_size_human"] = self._format_size(report["total_size"])
            
            for file_type in report["by_type"]:
                report["by_type"][file_type]["size_human"] = self._format_size(report["by_type"][file_type]["size"])
                
            for category in report["by_category"]:
                report["by_category"][category]["size_human"] = self._format_size(report["by_category"][category]["size"])
                
            return report
            
        except Exception as e:
            logger.error(f"Error generating usage report: {e}")
            return {"error": str(e)}
    
    async def _determine_organization_path(self, file_path: Path, metadata: Dict[str, Any], legal_metadata: Dict[str, Any] = None) -> Path:
        """Determine the appropriate organization path for a file"""
        # Extract relevant metadata
        file_type = metadata.get("type", "unknown")
        
        # Check for case information in legal metadata
        if legal_metadata and "case_numbers" in legal_metadata and legal_metadata["case_numbers"]:
            case_id = legal_metadata["case_numbers"][0]
            return self.base_path / "cases" / case_id / file_type
        
        # Check for entities in legal metadata
        if legal_metadata and "entities" in legal_metadata and legal_metadata["entities"]:
            entity = legal_metadata["entities"][0]
            entity_name = self._sanitize_name(entity)[:30]  # Limit length
            return self.base_path / "entities" / entity_name / file_type
        
        # Default organization by document type
        return self.base_path / "documents" / file_type
    
    async def _generate_standardized_filename(self, file_path: Path, metadata: Dict[str, Any], legal_metadata: Dict[str, Any] = None) -> str:
        """Generate a standardized filename based on metadata"""
        # Extract date information
        date_str = ""
        if legal_metadata and "dates" in legal_metadata and legal_metadata["dates"]:
            # Use first date from legal metadata
            date_str = legal_metadata["dates"][0].split("T")[0]
        else:
            # Use file modification date
            mod_date = metadata.get("metadata", {}).get("modified", "")
            if mod_date:
                date_str = mod_date.split("T")[0]
        
        # Clean up date string
        if date_str and not date_str.startswith("20"):  # Simple check for YYYY-MM-DD format
            date_str = datetime.now().strftime("%Y-%m-%d")
            
        # Add date prefix if available
        prefix = f"{date_str}_" if date_str else ""
        
        # Use original filename as base
        original_name = file_path.name
        
        # Add document type if available
        doc_type = metadata.get("type", "")
        suffix = f"_{doc_type}" if doc_type and doc_type != "unknown" else ""
        
        # Combine parts
        if prefix:
            # If we have a date prefix, use it with the original name
            return f"{prefix}{original_name}{suffix}"
        else:
            # Otherwise just use the original name
            return f"{original_name}{suffix}"
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize names for filesystem compatibility"""
        import re
        return re.sub(r'[^\w\-_\.]', '_', name)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format bytes to human-readable size"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"