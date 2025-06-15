import os
import shutil
from pathlib import Path

class SafePaths:
    """Utility for safely managing file operations"""
    
    DEFAULT_SAFE_PATH = "C:/Users/casey/OrganizeFolder"
    
    @staticmethod
    def is_github_path(path):
        """Check if a path contains GitHub directories"""
        norm_path = os.path.normpath(str(path)).lower()
        return "github" in norm_path
    
    @staticmethod
    def get_safe_path(path=None):
        """Return a safe path to use for file operations"""
        if path and os.path.exists(path) and not SafePaths.is_github_path(path):
            return path
        
        # Create default safe path if it doesn't exist
        if not os.path.exists(SafePaths.DEFAULT_SAFE_PATH):
            os.makedirs(SafePaths.DEFAULT_SAFE_PATH, exist_ok=True)
            print(f"Created default safe directory: {SafePaths.DEFAULT_SAFE_PATH}")
            
        return SafePaths.DEFAULT_SAFE_PATH
    
    @staticmethod
    def safe_move(src, dst):
        """Safely move a file, ensuring GitHub paths are protected"""
        if SafePaths.is_github_path(src) or SafePaths.is_github_path(dst):
            print(f"⚠️ Skipping unsafe move operation: {src} -> {dst}")
            return False
            
        try:
            # Create destination directory if needed
            dst_dir = os.path.dirname(os.path.abspath(dst))
            os.makedirs(dst_dir, exist_ok=True)
            
            # Perform move operation
            shutil.move(src, dst)
            print(f"✅ Moved: {src} -> {dst}")
            return True
        except Exception as e:
            print(f"❌ Move failed: {e}")
            return False
    
    @staticmethod
    def safe_copy(src, dst):
        """Safely copy a file, ensuring GitHub paths are protected"""
        if SafePaths.is_github_path(src) or SafePaths.is_github_path(dst):
            print(f"⚠️ Skipping unsafe copy operation: {src} -> {dst}")
            return False
            
        try:
            # Create destination directory if needed
            dst_dir = os.path.dirname(os.path.abspath(dst))
            os.makedirs(dst_dir, exist_ok=True)
            
            # Perform copy operation
            shutil.copy2(src, dst)
            print(f"✅ Copied: {src} -> {dst}")
            return True
        except Exception as e:
            print(f"❌ Copy failed: {e}")
            return False
