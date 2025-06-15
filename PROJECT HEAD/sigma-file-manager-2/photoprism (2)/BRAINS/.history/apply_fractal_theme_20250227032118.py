#!/usr/bin/env python
"""
Apply Fractal Theme to Sorting Hat

This script sets up the fractal theme for the Sorting Hat system.
It generates the necessary assets and updates configuration files.
"""
import os
import sys
import shutil
import subprocess
import json
from pathlib import Path

def print_header(text):
    """Print a styled header"""
    print("\n" + "=" * 70)
    print(f"{text.center(70)}")
    print("=" * 70 + "\n")

def print_step(text):
    """Print a step in the process"""
    print(f"➤ {text}")

def print_success(text):
    """Print a success message"""
    print(f"✅ {text}")

def print_error(text):
    """Print an error message"""
    print(f"❌ {text}")

def ensure_dir(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print_step(f"Created directory: {directory}")

def copy_file(src, dst):
    """Copy a file with directory creation"""
    ensure_dir(os.path.dirname(dst))
    shutil.copy2(src, dst)
    print_step(f"Copied {os.path.basename(src)} to {dst}")

def main():
    """Main function to apply fractal theme"""
    print_header("SORTING HAT FRACTAL THEME SETUP")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    static_