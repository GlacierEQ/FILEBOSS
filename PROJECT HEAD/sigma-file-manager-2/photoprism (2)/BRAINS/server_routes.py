"""
Routing module for Sorting Hat server.
Defines API endpoints for the FastAPI server.
"""
import os
import json
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Body

# Import natural language organizer
from natural_language_organizer import handle_natural_language_command

# Create router for natural language organization endpoints
natural_router = APIRouter()

@natural_router.post("/organize")
async def organize_with_natural_language(
    instruction: str = Body(..., embed=True),
    path: Optional[str] = Body(None, embed=True)
):
    """
    Organize files using a natural language instruction.
    
    Parameters:
    - instruction: Natural language description of how to organize files
    - path: Optional base path to organize (defaults to safe path)
    
    Returns:
    - Organization results including files moved and actions taken
    """
    try:
        result = await handle_natural_language_command(instruction, path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Organization failed: {str(e)}")

@natural_router.get("/examples")
async def get_natural_language_examples():
    """
    Get example natural language organization commands.
    
    Returns:
    - List of example instructions and descriptions
    """
    examples = [
        {
            "instruction": "Move all PDF files to the Documents folder and organize them by date",
            "description": "Sorts PDF files into Documents with date-based naming"
        },
        {
            "instruction": "Find images in Downloads and sort them into Photos by year and month",
            "description": "Creates a year/month structure for photos"
        },
        {
            "instruction": "Organize code files by language into the Programming folder",
            "description": "Separates code files by language type"
        },
        {
            "instruction": "Move large video files older than 30 days to the Archive folder",
            "description": "Archives old video files to free up space"
        },
        {
            "instruction": "Create folders for my projects and move related files into them",
            "description": "Groups related files into project folders"
        }
    ]
    
    return {"examples": examples}
