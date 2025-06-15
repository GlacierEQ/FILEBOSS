import os
from fastapi import HTTPException

SAFE_BASE_PATH = os.path.realpath("C:/Users/casey/OneDrive/Documents/GitHub/llama-fs")

def is_safe_path(path: str) -> bool:
    """
    Checks if a path is within the safe base directory.
    """
    return os.path.realpath(path).startswith(SAFE_BASE_PATH)

def sanitize_path(path: str) -> bool:
    """
    Rejects path traversal attempts.
    """
    return ".." not in path

def validate_path(path: str) -> str:
    """
    Validates a path for safety and existence.
    Returns the path if valid, raises HTTPException otherwise.
    """
    if not path or not (is_safe_path(path) and sanitize_path(path)):
        raise HTTPException(status_code=403, detail="Access Denied")
    if not os.path.exists(path):
        raise HTTPException(status_code=400, detail="Path does not exist in filesystem")
    return path

def validate_commit_paths(base_path: str, src_path: str, dst_path: str) -> tuple:
    """
    Validates source and destination paths for commit operations.
    Returns (src, dst) tuple if valid, raises HTTPException otherwise.
    """
    src = os.path.join(base_path, src_path)
    dst = os.path.join(base_path, dst_path)
    
    if not (is_safe_path(src) and sanitize_path(src) and 
            is_safe_path(dst) and sanitize_path(dst)):
        raise HTTPException(status_code=403, detail="Access Denied")
    if not os.path.exists(src):
        raise HTTPException(status_code=400, 
                            detail="Source path does not exist in filesystem")
    
    return src, dst
