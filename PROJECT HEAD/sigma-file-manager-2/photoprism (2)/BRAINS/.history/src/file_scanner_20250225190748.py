import os
import logging
import shutil
import mimetypes
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from .path_utils import is_safe_path, sanitize_path
from .error_handler import logger

class FileScanResult:
    """Container for file scan results"""
    def __init__(self, path: str):
        self.path = path
        self.issues = []
        self.repaired = []
        self.errors = []
        self.scan_time = None
        self.repair_time = None
        
    def add_issue(self, issue: str):
        self.issues.append(issue)
        
    def add_repair(self, repair: str):
        self.repaired.append(repair)
        
    def add_error(self, error: str):
        self.errors.append(error)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert scan results to a dictionary"""
        return {
            "path": self.path,
            "issues_found": len(self.issues),
            "issues": self.issues,
            "repairs_made": len(self.repaired),
            "repairs": self.repaired,
            "errors": self.errors,
            "scan_time_seconds": self.scan_time,
            "repair_time_seconds": self.repair_time if self.repair_time else None,
            "is_clean": len(self.issues) == 0 and len(self.errors) == 0
        }

class FileScanner:
    """Utility for scanning and repairing file system issues"""
    def __init__(self, base_path: str):
        self.base_path = base_path
        
    def scan_file(self, file_path: str) -> FileScanResult:
        """Scan a single file for issues"""
        if not is_safe_path(file_path) or not sanitize_path(file_path):
            raise ValueError(f"Path validation failed for {file_path}")
        
        result = FileScanResult(file_path)
        start_time = time.time()
        
        try:
            path_obj = Path(file_path)
            
            # Check if file exists
            if not path_obj.exists():
                result.add_issue("File does not exist")
                return result
                
            # Check if file is readable
            if not os.access(file_path, os.R_OK):
                result.add_issue("File is not readable")
            
            # Check for zero-byte files
            if path_obj.is_file() and path_obj.stat().st_size == 0:
                result.add_issue("File is empty (zero bytes)")
            
            # Check file extension matches content type
            if path_obj.is_file() and path_obj.suffix:
                mime_type, encoding = mimetypes.guess_type(file_path)
                if mime_type:
                    guessed_ext = mimetypes.guess_extension(mime_type)
                    if guessed_ext and guessed_ext != path_obj.suffix.lower():
                        result.add_issue(f"File extension ({path_obj.suffix}) does not match content type (expected {guessed_ext})")
            
            # Check for permissions issues
            try:
                if path_obj.is_file():
                    with open(file_path, 'rb') as f:
                        # Just read a small chunk to verify readability
                        f.read(1024)
            except PermissionError:
                result.add_issue("File has permission issues")
            except Exception as e:
                result.add_issue(f"File read test failed: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error scanning file {file_path}: {str(e)}")
            result.add_error(f"Scan failed: {str(e)}")
            
        result.scan_time = time.time() - start_time
        return result
    
    def repair_file(self, scan_result: FileScanResult) -> FileScanResult:
        """Attempt to repair issues found in a file"""
        if not scan_result.issues:
            return scan_result
            
        start_time = time.time()
        file_path = scan_result.path
        path_obj = Path(file_path)
        
        try:
            # Fix file extension if needed
            if any("File extension" in issue for issue in scan_result.issues):
                try:
                    mime_type, _ = mimetypes.guess_type(file_path)
                    if mime_type:
                        guessed_ext = mimetypes.guess_extension(mime_type)
                        if guessed_ext and guessed_ext != path_obj.suffix.lower():
                            new_path = path_obj.with_suffix(guessed_ext)
                            try:
                                os.rename(file_path, new_path)
                                scan_result.add_repair(f"Fixed file extension: {path_obj.name} → {new_path.name}")
                            except Exception as e:
                                scan_result.add_error(f"Failed to fix file extension: {str(e)}")
                except Exception as e:
                    scan_result.add_error(f"Error determining MIME type: {str(e)}")
                    
            # Repair empty files (just log it, don't actually delete)
            if any("zero bytes" in issue for issue in scan_result.issues):
                scan_result.add_repair("Identified empty file - marked for review")
                
            # Repair permission issues
            if any("permission" in issue.lower() for issue in scan_result.issues):
                try:
                    if path_obj.is_file():
                        # Try to fix permissions - example for Unix-like systems
                        # For Windows, this would be different
                        os.chmod(file_path, 0o644)  # rw-r--r--
                        scan_result.add_repair("Fixed file permissions")
                except Exception as e:
                    scan_result.add_error(f"Failed to fix permissions: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error repairing file {file_path}: {str(e)}")
            scan_result.add_error(f"Repair failed: {str(e)}")
            
        scan_result.repair_time = time.time() - start_time
        return scan_result
        
    def scan_directory(self, directory_path: str, recursive: bool = True) -> List[FileScanResult]:
        """Scan all files in a directory"""
        if not is_safe_path(directory_path) or not sanitize_path(directory_path):
            raise ValueError(f"Path validation failed for {directory_path}")
            
        results = []
        
        try:
            path_obj = Path(directory_path)
            if not path_obj.is_dir():
                raise ValueError(f"{directory_path} is not a directory")
                
            if recursive:
                for root, dirs, files in os.walk(directory_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        results.append(self.scan_file(file_path))
            else:
                for item in path_obj.iterdir():
                    if item.is_file():
                        results.append(self.scan_file(str(item)))
        except Exception as e:
            logger.error(f"Error scanning directory {directory_path}: {str(e)}")
            # Create a dummy result for the directory itself
            result = FileScanResult(directory_path)
            result.add_error(f"Directory scan failed: {str(e)}")
            results.append(result)
            
        return results
        
    def repair_all(self, scan_results: List[FileScanResult]) -> List[FileScanResult]:
        """Repair all issues found in scan results"""
        repaired_results = []
        
        for result in scan_results:
            if result.issues:
                repaired_results.append(self.repair_file(result))
            else:
                repaired_results.append(result)
                
        return repaired_results
