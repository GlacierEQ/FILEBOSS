#!/usr/bin/env python
"""
PhotoPrism Sorting Department Integration

This script registers the PhotoPrism Sorting Department with the Sorting Hat service.
"""
import os
import sys
import json
import logging
from typing import Dict, Any, Optional

# Set up path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configure logging
try:
    from log_manager import get_logger
    logger = get_logger("photoprism_integration", separate_file=True)
except ImportError:
    # Fall back to standard logging if log_manager is not available
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("photoprism_integration")

def register_with_service():
    """Register the PhotoPrism Sorting Department with the service manager"""
    try:
        # Try to import the service registry
        service_registry = None
        try:
            from service_registry import ServiceRegistry
            service_registry = ServiceRegistry()
        except ImportError:
            logger.warning("Service registry not available, creating feature registration file")
            
        # Component information
        component_info = {
            "name": "photoprism_sorting_department",
            "display_name": "PhotoPrism Sorting Department",
            "version": "1.0.0",
            "description": "Multi-agent file sorting system integrated with PhotoPrism",
            "author": "Sorting Hat Team",
            "entry_points": {
                "api": "integration.photoprism.api:router",
                "cli": "integration.photoprism.photoprism_sorter:main",
                "gui": None,
                "tray": None
            },
            "dependencies": [
                "requests",
                "watchdog",
                "pillow"
            ],
            "settings": {
                "enabled": True,
                "sorting_department_path": os.path.join(os.path.expanduser("~"), "PhotoPrism", "storage", "sorting-dept"),
                "photoprism_url": "http://localhost:2342"
            },
            "documentation": "docs/photoprism_sorting_guide.md"
        }
        
        # Register with service registry if available
        if service_registry:
            service_registry.register_component(
                component_info["name"],
                component_info
            )
            logger.info(f"Registered {component_info['display_name']} with service registry")
        else:
            # Create a registration file
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            reg_dir = os.path.join(base_dir, "data", "components")
            os.makedirs(reg_dir, exist_ok=True)
            
            reg_file = os.path.join(reg_dir, "photoprism_sorting_department.json")
            with open(reg_file, "w") as f:
                json.dump(component_info, f, indent=2)
                
            logger.info(f"Created component registration file: {reg_file}")
        
        # Add API routes to server if possible
        try:
            from integration.photoprism.api import setup_routes
            
            # Try to get the app instance
            try:
                from server import app
                setup_routes(app)
                logger.info("Added PhotoPrism Sorting Department API routes to server")
            except (ImportError, AttributeError):
                logger.warning("Could not add API routes: server.app not found")
        except ImportError:
            logger.warning("Could not import photoprism api module")
        
        return True
    except Exception as e:
        logger.error(f"Error registering PhotoPrism Sorting Department component: {e}")
        return False

def create_sorting_department():
    """Create the sorting department directory structure"""
    try:
        # Load configuration
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        with open(config_path, "r") as f:
            config = json.load(f)
        
        # Create sorting department directory
        sorting_dept_path = config["sorting_department_path"]
        os.makedirs(sorting_dept_path, exist_ok=True)
        logger.info(f"Created sorting department directory: {sorting_dept_path}")
        
        # Create category directories
        categories = [
            "People", "Events", "Documents", "Nature", "Travel",
            "Food", "Art", "Technology", "Vehicles", "Miscellaneous"
        ]
        
        for category in categories:
            category_path = os.path.join(sorting_dept_path, category)
            os.makedirs(category_path, exist_ok=True)
            logger.info(f"Created category directory: {category_path}")
        
        return True
    except Exception as e:
        logger.error(f"Error creating sorting department: {e}")
        return False

def main():
    """Main entry point for the integration script"""
    # Create sorting department
    create_sorting_department()
    
    # Register with service
    success = register_with_service()
    
    if success:
        print("PhotoPrism Sorting Department successfully integrated with the service")
        
        # Create documentation
        create_documentation()
    else:
        print("Failed to integrate PhotoPrism Sorting Department with the service")
        sys.exit(1)

def create_documentation():
    """Create documentation for the PhotoPrism Sorting Department"""
    try:
        # Create docs directory if it doesn't exist
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        docs_dir = os.path.join(base_dir, "docs")
        os.makedirs(docs_dir, exist_ok=True)
        
        # Create documentation file
        doc_path = os.path.join(docs_dir, "photoprism_sorting_guide.md")
        
        with open(doc_path, "w") as f:
            f.write("""# PhotoPrism Sorting Department Guide

## Overview

The PhotoPrism Sorting Department is a multi-agent file sorting system integrated with PhotoPrism. It uses two specialized AIs:

1. **Fast AI**: Quick scanning and categorization
2. **Accurate AI**: Deep analysis and final naming

Files are sorted hierarchically based on content and renamed with the format:
`YYMMDD-[Description Up to 30 Chars]`

## Setup

1. Ensure PhotoPrism is installed and running
2. Configure the sorting department in `integration/photoprism/config.json`
3. Run the integration script: `python integration/photoprism/photoprism_integration.py`

## Usage

1. Place files in the sorting department directory: `~/PhotoPrism/storage/sorting-dept/`
2. The system will automatically process files and organize them into categories
3. Files will be renamed with the format: `YYMMDD-[Description]`
4. PhotoPrism will be updated to index the newly organized files

## Categories

Files are organized into the following categories:

- People
- Events
- Documents
- Nature
- Travel
- Food
- Art
- Technology
- Vehicles
- Miscellaneous

## Configuration

You can customize the behavior of the sorting department by editing the `config.json` file:

```json
{
    "sorting_department_path": "C:/Users/casey/PhotoPrism/storage/sorting-dept",
    "photoprism_url": "http://localhost:2342",
    "photoprism_username": "admin",
    "photoprism_password": "admin",
    "fast_ai": {
        "memory_limit": 100,
        "confidence_threshold": 0.7,
        "max_processing_time": 1.0
    },
    "accurate_ai": {
        "memory_limit": 200,
        "confidence_threshold": 0.9,
        "max_processing_time": 5.0
    }
}
```

## Command Line Interface

You can also process files manually using the command line:

```bash
python integration/photoprism/photoprism_sorter.py --file /path/to/file.jpg
```

## Troubleshooting

If you encounter issues:

1. Check the log file: `photoprism_sorter.log`
2. Ensure PhotoPrism is running and accessible
3. Verify the sorting department directory exists and is writable
4. Check that the configuration file is correctly formatted
""")
        
        logger.info(f"Created documentation: {doc_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating documentation: {e}")
        return False

if __name__ == "__main__":
    main()
