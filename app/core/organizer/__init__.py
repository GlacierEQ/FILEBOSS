"""
FILEBOSS File Organizer Module

This package provides file organization and analysis capabilities for the FILEBOSS system.
"""

from .file_organizer import FileOrganizer
from .file_analyzer import FileAnalyzer
from .file_utils import (
    get_file_type,
    calculate_file_hash,
    get_file_metadata,
    is_hidden
)

__all__ = [
    'FileOrganizer',
    'FileAnalyzer',
    'get_file_type',
    'calculate_file_hash',
    'get_file_metadata',
    'is_hidden'
]
