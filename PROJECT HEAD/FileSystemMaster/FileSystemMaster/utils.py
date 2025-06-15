"""
Utility functions for file operations and data processing
"""

import hashlib
import re
import os
from pathlib import Path
from typing import Optional

def safe_filename(filename: str) -> str:
    """Convert a string to a safe filename"""
    
    if not filename or not filename.strip():
        return "unnamed_file"
    
    # Remove or replace problematic characters
    filename = filename.strip()
    
    # Replace common problematic characters
    replacements = {
        '/': '_',
        '\\': '_',
        ':': '_',
        '*': '_',
        '?': '_',
        '"': '_',
        '<': '_',
        '>': '_',
        '|': '_',
        '\n': '_',
        '\r': '_',
        '\t': '_'
    }
    
    for char, replacement in replacements.items():
        filename = filename.replace(char, replacement)
    
    # Replace multiple spaces/underscores with single underscore
    filename = re.sub(r'[\s_]+', '_', filename)
    
    # Remove leading/trailing special characters
    filename = re.sub(r'^[._\-]+|[._\-]+$', '', filename)
    
    # Ensure not empty
    if not filename:
        filename = "unnamed_file"
    
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]
        # Try to break at word boundary
        last_underscore = filename.rfind('_')
        if last_underscore > 50:
            filename = filename[:last_underscore]
    
    return filename

def calculate_file_hash(file_path: Path, chunk_size: int = 8192) -> str:
    """Calculate SHA-256 hash of a file"""
    
    hash_sha256 = hashlib.sha256()
    
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception:
        return ""

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    size_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and size_index < len(size_names) - 1:
        size /= 1024
        size_index += 1
    
    return f"{size:.1f} {size_names[size_index]}"

def get_file_extension_type(extension: str) -> str:
    """Get file type category from extension"""
    
    extension = extension.lower().lstrip('.')
    
    type_mapping = {
        # Documents
        'pdf': 'document',
        'doc': 'document',
        'docx': 'document',
        'txt': 'document',
        'rtf': 'document',
        'odt': 'document',
        
        # Audio
        'mp3': 'audio',
        'wav': 'audio',
        'flac': 'audio',
        'm4a': 'audio',
        'aac': 'audio',
        'ogg': 'audio',
        'wma': 'audio',
        
        # Video
        'mp4': 'video',
        'avi': 'video',
        'mov': 'video',
        'mkv': 'video',
        'wmv': 'video',
        'flv': 'video',
        'webm': 'video',
        
        # Images
        'jpg': 'image',
        'jpeg': 'image',
        'png': 'image',
        'gif': 'image',
        'bmp': 'image',
        'svg': 'image',
        'webp': 'image',
        
        # Archives
        'zip': 'archive',
        'rar': 'archive',
        '7z': 'archive',
        'tar': 'archive',
        'gz': 'archive'
    }
    
    return type_mapping.get(extension, 'unknown')

def create_directory_structure(base_path: Path, structure: dict) -> None:
    """Create directory structure from nested dictionary"""
    
    for name, content in structure.items():
        dir_path = base_path / name
        dir_path.mkdir(parents=True, exist_ok=True)
        
        if isinstance(content, dict):
            create_directory_structure(dir_path, content)

def is_text_file(file_path: Path) -> bool:
    """Check if file appears to be a text file"""
    
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            
        # Check for null bytes (binary files typically contain them)
        if b'\x00' in chunk:
            return False
        
        # Try to decode as text
        try:
            chunk.decode('utf-8')
            return True
        except UnicodeDecodeError:
            try:
                chunk.decode('latin-1')
                return True
            except UnicodeDecodeError:
                return False
                
    except Exception:
        return False

def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length - len(suffix)]
    
    # Try to break at word boundary
    last_space = truncated.rfind(' ')
    if last_space > max_length * 0.7:  # Don't break too early
        truncated = truncated[:last_space]
    
    return truncated + suffix

def sanitize_path(path_str: str) -> str:
    """Sanitize a path string for cross-platform compatibility"""
    
    # Replace problematic characters
    path_str = re.sub(r'[<>:"|?*]', '_', path_str)
    
    # Handle path separators
    path_str = path_str.replace('\\', '/')
    
    # Remove double slashes
    path_str = re.sub(r'/+', '/', path_str)
    
    # Remove leading/trailing slashes and spaces
    path_str = path_str.strip('/ ')
    
    return path_str

def extract_keywords(text: str, max_keywords: int = 10) -> list:
    """Extract keywords from text using simple frequency analysis"""
    
    if not text:
        return []
    
    # Convert to lowercase and split into words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Common stop words to exclude
    stop_words = {
        'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
        'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his',
        'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who',
        'boy', 'did', 'man', 'put', 'say', 'she', 'too', 'use', 'that', 'with',
        'have', 'this', 'will', 'your', 'from', 'they', 'know', 'want', 'been',
        'good', 'much', 'some', 'time', 'very', 'when', 'come', 'here', 'just',
        'like', 'long', 'make', 'many', 'over', 'such', 'take', 'than', 'them',
        'well', 'were'
    }
    
    # Filter out stop words and count frequency
    word_freq = {}
    for word in words:
        if word not in stop_words and len(word) > 2:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in keywords[:max_keywords]]
