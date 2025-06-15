#!/usr/bin/env python
"""
PhotoPrism Sorting Department API

This module provides API endpoints for the PhotoPrism Sorting Department.
"""
import os
import sys
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

# Set up path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Try to import FastAPI
try:
    from fastapi import APIRouter, HTTPException, File, UploadFile, Form, BackgroundTasks
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    # Create a dummy APIRouter for type hinting
    class APIRouter:
        def get(self, *args, **kwargs): pass
        def post(self, *args, **kwargs): pass
        def put(self, *args, **kwargs): pass
        def delete(self, *args, **kwargs): pass

# Configure logging
try:
    from log_manager import get_logger
    logger = get_logger("photoprism_api", separate_file=True)
except ImportError:
    # Fall back to standard logging if log_manager is not available
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("photoprism_api")

# Import the PhotoPrism sorter
try:
    from integration.photoprism.photoprism_sorter import PhotoPrismSorter, FileInfo
except ImportError:
    logger.error("Could not import PhotoPrismSorter")
    PhotoPrismSorter = None
    FileInfo = None

# Create router
if FASTAPI_AVAILABLE:
    router = APIRouter(
        prefix="/api/photoprism",
        tags=["photoprism"],
        responses={404: {"description": "Not found"}},
    )
else:
    router = None

# Initialize PhotoPrism sorter
sorter = None
if PhotoPrismSorter:
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
            sorter = PhotoPrismSorter(config)
            logger.info("Initialized PhotoPrism sorter")
        else:
            logger.error(f"Config file not found: {config_path}")
    except Exception as e:
        logger.error(f"Error initializing PhotoPrism sorter: {e}")

# API endpoints
if FASTAPI_AVAILABLE and router and sorter:
    @router.get("/status")
    async def get_status():
        """Get the status of the PhotoPrism Sorting Department"""
        try:
            # Check if sorting department directory exists
            sorting_dept_path = sorter.sorting_dept_path
            if not os.path.exists(sorting_dept_path):
                return {"status": "error", "message": f"Sorting department directory not found: {sorting_dept_path}"}
            
            # Count files in sorting department
            files_count = len([f for f in os.listdir(sorting_dept_path) if os.path.isfile(os.path.join(sorting_dept_path, f))])
            
            # Check PhotoPrism connection
            photoprism_connected = sorter.photoprism_session is not None
            
            return {
                "status": "ok",
                "sorting_department_path": sorting_dept_path,
                "files_waiting": files_count,
                "photoprism_connected": photoprism_connected
            }
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {"status": "error", "message": str(e)}
    
    @router.post("/process")
    async def process_file(background_tasks: BackgroundTasks, file_path: str = Form(...)):
        """Process a file in the PhotoPrism Sorting Department
        
        Args:
            file_path: Path to the file to process
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
            
            # Process file in background
            background_tasks.add_task(sorter.process_file, file_path)
            
            return {"status": "processing", "file_path": file_path}
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/upload")
    async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
        """Upload a file to the PhotoPrism Sorting Department
        
        Args:
            file: File to upload
        """
        try:
            # Save file to sorting department
            file_path = os.path.join(sorter.sorting_dept_path, file.filename)
            
            # Write file
            with open(file_path, "wb") as f:
                f.write(await file.read())
            
            # Process file in background
            background_tasks.add_task(sorter.process_file, file_path)
            
            return {"status": "uploaded", "file_path": file_path}
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/categories")
    async def get_categories():
        """Get the list of categories used by the PhotoPrism Sorting Department"""
        try:
            from integration.photoprism.photoprism_sorter import HIERARCHICAL_CATEGORIES
            
            return {"categories": list(HIERARCHICAL_CATEGORIES.keys())}
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/files/{category}")
    async def get_files_by_category(category: str):
        """Get the list of files in a category
        
        Args:
            category: Category name
        """
        try:
            # Check if category exists
            category_path = os.path.join(sorter.sorting_dept_path, category)
            if not os.path.exists(category_path):
                raise HTTPException(status_code=404, detail=f"Category not found: {category}")
            
            # Get files recursively
            files = []
            for root, _, filenames in os.walk(category_path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(file_path, sorter.sorting_dept_path)
                    files.append({
                        "path": relative_path,
                        "filename": filename,
                        "size": os.path.getsize(file_path),
                        "modified": os.path.getmtime(file_path)
                    })
            
            return {"category": category, "files": files}
        except Exception as e:
            logger.error(f"Error getting files by category: {e}")
            raise HTTPException(status_code=500, detail=str(e))

def setup_routes(app):
    """Set up API routes for the FastAPI application
    
    Args:
        app: FastAPI application
    """
    if FASTAPI_AVAILABLE and router:
        app.include_router(router)
        logger.info("Added PhotoPrism Sorting Department API routes to FastAPI application")
    else:
        logger.warning("FastAPI not available, could not set up routes")

if __name__ == "__main__":
    # If run directly, print API information
    print("PhotoPrism Sorting Department API")
    print("Available endpoints:")
    print("  GET  /api/photoprism/status")
    print("  POST /api/photoprism/process")
    print("  POST /api/photoprism/upload")
    print("  GET  /api/photoprism/categories")
    print("  GET  /api/photoprism/files/{category}")
