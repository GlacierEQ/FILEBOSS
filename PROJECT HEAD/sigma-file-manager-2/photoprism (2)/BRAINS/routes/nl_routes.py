"""
API Routes for Natural Language Organizer

This module defines the FastAPI routes for the Natural Language Organizer.
"""
import os
import sys
import asyncio
import time
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Body, Query, Request

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import NL bridge
from integration.nl_bridge import process_instruction, get_examples

# Create router
router = APIRouter(
    prefix="/nl",
    tags=["natural-language"],
    responses={404: {"description": "Not found"}}
)

@router.post("/organize")
async def organize_files(
    instruction: str = Body(..., description="Natural language instruction"),
    path: Optional[str] = Body(None, description="Path to process (optional)"),
    request: Request = None
):
    """
    Organize files using a natural language instruction.
    
    The instruction should be provided in plain English describing how you want files organized.
    Examples:
    - "Move PDFs to Documents folder"
    - "Sort images by year and month"
    - "Organize code files by language"
    
    Returns:
        Organization results including files moved and success status
    """
    # Extract metadata from request
    metadata = {
        "timestamp": time.time(),
        "user_agent": request.headers.get("user-agent", "unknown") if request else "unknown",
        "source": "api"
    }
    
    # Call the NL bridge to process the instruction
    result = await process_instruction(instruction, path, metadata)
    
    # If there was an error, raise HTTPException
    if not result.get("success", False) and "error" in result:
        raise HTTPException(status_code=500, detail=result["message"])
        
    return result

@router.get("/examples")
async def get_nl_examples(
    category: Optional[str] = Query(None, description="Category of examples to return")
):
    """
    Get example natural language instructions for file organization.
    
    Returns:
        List of example instructions with descriptions
    """
    return {"examples": get_examples(category)}

@router.get("/categories")
async def get_nl_categories():
    """
    Get available categories for natural language examples.
    
    Returns:
        List of available categories
    """
    # Extract unique categories from examples
    all_examples = get_examples()
    categories = list(set(ex["category"] for ex in all_examples))
    
    return {"categories": categories}

# Function to include these routes in the main app
def setup_routes(app):
    """
    Add Natural Language Organizer routes to FastAPI app
    
    Args:
        app: FastAPI application instance
    """
    app.include_router(router)
    
    # Add other necessary setup here
    return app
