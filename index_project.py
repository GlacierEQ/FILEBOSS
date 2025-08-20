#!/usr/bin/env python3
"""
FILEBOSS Project Indexer

This script creates an index of the project structure and components.
"""
import os
import json
from pathlib import Path
from datetime import datetime

def scan_directory(path, max_depth=3, current_depth=0):
    """Recursively scan directory structure."""
    items = []
    
    if current_depth >= max_depth:
        return items
    
    try:
        for item in sorted(os.listdir(path)):
            if item.startswith('.') and item not in ['.env', '.env.example']:
                continue
            
            item_path = os.path.join(path, item)
            
            if os.path.isdir(item_path):
                # Skip common build/cache directories
                if item in ['__pycache__', '.mypy_cache', 'node_modules', '.git']:
                    continue
                
                items.append({
                    'name': item,
                    'type': 'directory',
                    'path': item_path,
                    'children': scan_directory(item_path, max_depth, current_depth + 1)
                })
            else:
                # Get file info
                stat = os.stat(item_path)
                items.append({
                    'name': item,
                    'type': 'file',
                    'path': item_path,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
    except PermissionError:
        pass
    
    return items

def analyze_project():
    """Analyze project structure and create index."""
    project_root = Path(__file__).parent
    
    # Basic project info
    project_info = {
        'name': 'FILEBOSS',
        'description': 'Digital Evidence Management System',
        'version': '0.1.0',
        'indexed_at': datetime.now().isoformat(),
        'root_path': str(project_root)
    }
    
    # Scan project structure
    structure = scan_directory(str(project_root))
    
    # Identify key components
    components = {
        'api': 'casebuilder/api/',
        'core': 'casebuilder/core/',
        'database': 'casebuilder/db/',
        'services': 'casebuilder/services/',
        'tests': 'tests/',
        'scripts': 'scripts/',
        'docs': 'docs/',
        'docker': 'docker-compose.yml',
        'config': ['.env', '.env.example', 'pyproject.toml', 'requirements.txt']
    }
    
    # Count files by type
    file_types = {}
    total_files = 0
    
    def count_files(items):
        nonlocal total_files
        for item in items:
            if item['type'] == 'file':
                total_files += 1
                ext = os.path.splitext(item['name'])[1].lower()
                file_types[ext] = file_types.get(ext, 0) + 1
            elif item['type'] == 'directory':
                count_files(item['children'])
    
    count_files(structure)
    
    # Create index
    index = {
        'project': project_info,
        'structure': structure,
        'components': components,
        'statistics': {
            'total_files': total_files,
            'file_types': file_types
        },
        'deployment': {
            'docker_available': os.path.exists('docker-compose.yml'),
            'requirements_file': os.path.exists('requirements.txt'),
            'env_configured': os.path.exists('.env')
        }
    }
    
    return index

def main():
    """Main indexing function."""
    print("🔍 Indexing FILEBOSS project...")
    
    # Create project index
    index = analyze_project()
    
    # Save index to file
    with open('project_index.json', 'w') as f:
        json.dump(index, f, indent=2)
    
    # Print summary
    print(f"✅ Project indexed successfully!")
    print(f"📁 Total files: {index['statistics']['total_files']}")
    print(f"🐍 Python files: {index['statistics']['file_types'].get('.py', 0)}")
    print(f"📄 Config files: {len([f for f in index['statistics']['file_types'] if f in ['.yml', '.yaml', '.toml', '.ini', '.env']])}")
    print(f"🐳 Docker ready: {index['deployment']['docker_available']}")
    print(f"⚙️  Environment configured: {index['deployment']['env_configured']}")
    
    # Show key components
    print("\n📋 Key Components:")
    for component, path in index['components'].items():
        if isinstance(path, list):
            for p in path:
                if os.path.exists(p):
                    print(f"  ✅ {component}: {p}")
        else:
            if os.path.exists(path):
                print(f"  ✅ {component}: {path}")
            else:
                print(f"  ❌ {component}: {path} (missing)")
    
    print(f"\n📊 Index saved to: project_index.json")

if __name__ == "__main__":
    main()