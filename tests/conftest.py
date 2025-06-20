"""
Configuration file for pytest.
This file ensures that the project root is in the Python path.
"""
import os
import sys

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
