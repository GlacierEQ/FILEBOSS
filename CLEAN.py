#!/usr/bin/env python3
"""
Clean up the project directory - remove all the bullshit
"""

import os
import shutil
from pathlib import Path

def main():
    print("🧹 CLEANING PROJECT DIRECTORY...")
    
    # Files to keep
    keep_files = {
        'START.py', 'START.bat', 'START.sh',
        'main.py', 'requirements.txt', 'README.md',
        'Dockerfile', 'docker-compose.yml',
        'test_casebuilder_verification.py',
        '.env', '.env.example', '.gitignore',
        'Procfile', 'railway.json', 'render.yaml'
    }
    
    # Directories to keep
    keep_dirs = {
        'casebuilder', 'docs', '.git', '.vscode'
    }
    
    # Get all items in current directory
    current_dir = Path('.')
    
    for item in current_dir.iterdir():
        if item.name.startswith('.') and item.name not in keep_dirs:
            continue
            
        if item.is_file():
            if item.name not in keep_files:
                print(f"🗑️  Removing file: {item.name}")
                try:
                    item.unlink()
                except Exception as e:
                    print(f"   ❌ Failed: {e}")
        
        elif item.is_dir():
            if item.name not in keep_dirs:
                print(f"🗑️  Removing directory: {item.name}")
                try:
                    shutil.rmtree(item)
                except Exception as e:
                    print(f"   ❌ Failed: {e}")
    
    print("✅ Project directory cleaned!")
    print("\n📁 Remaining structure:")
    for item in sorted(current_dir.iterdir()):
        if not item.name.startswith('.'):
            print(f"   {item.name}")

if __name__ == "__main__":
    main()