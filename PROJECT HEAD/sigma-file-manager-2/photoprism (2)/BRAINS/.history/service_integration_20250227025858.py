#!/usr/bin/env python
"""
Service Integration for Natural Language Organizer

This script registers the Natural Language Organizer with the Sorting Hat service.
"""
import os
import sys
import importlib
import json
import logging
from typing import Dict, Any, Optional, List, Union

# Set up path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s'
)
logger = logging.getLogger("service_integration")

def register_with_service():
    """Register the Natural Language Organizer with the service manager"""
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
            "name": "natural_language_organizer",
            "display_name": "Natural Language File Organizer",
            "version": "1.0.0",
            "description": "Organize files using natural language instructions",
            "author": "Sorting Hat Team",
            "entry_points": {
                "api": "routes.nl_routes:router",
                "cli": "nlorganize:main",
                "gui": "nl_gui:main",
                "tray": "tray_app_nl:main"
            },
            "dependencies": [
                "colorama",
                "pystray",
                "pillow",
                "groq"  # Optional
            ],
            "settings": {
                "enabled": True,
                "use_ai": True,
                "default_safe_path": os.path.join(os.path.expanduser("~"), "OrganizeFolder")
            },
            "documentation": "docs/natural_language_guide.md"
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
            base_dir = os.path.dirname(os.path.abspath(__file__))
            reg_dir = os.path.join(base_dir, "data", "components")
            os.makedirs(reg_dir, exist_ok=True)
            
            reg_file = os.path.join(reg_dir, "natural_language_organizer.json")
            with open(reg_file, "w") as f:
                json.dump(component_info, f, indent=2)
                
            logger.info(f"Created component registration file: {reg_file}")
        
        # Add API routes to server if possible
        try:
            from routes.nl_routes import setup_routes
            
            # Try to get the app instance
            try:
                from server import app
                setup_routes(app)
                logger.info("Added Natural Language API routes to server")
            except (ImportError, AttributeError):
                logger.warning("Could not add API routes: server.app not found")
        except ImportError:
            logger.warning("Could not import nl_routes module")
        
        return True
    except Exception as e:
        logger.error(f"Error registering natural language component: {e}")
        return False

if __name__ == "__main__":
    success = register_with_service()
    if success:
        print("Natural Language Organizer successfully integrated with the service")
    else:
        print("Failed to integrate Natural Language Organizer with the service")
        sys.exit(1)
