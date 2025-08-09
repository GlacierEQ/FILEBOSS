"""
Test package for the FileBoss application.

This package contains all the test modules for the application.
"""
from pathlib import Path

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "test_data"
TEST_DATA_DIR.mkdir(exist_ok=True)
