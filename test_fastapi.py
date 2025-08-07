"""
Test script to verify FastAPI application functionality.
"""
import asyncio
import httpx
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from casebuilder.core.config import settings

async def test_fastapi_app():
    """Test FastAPI application endpoints."""
    base_url = "http://127.0.0.1:8001"
    
    async with httpx.AsyncClient() as client:
        # Test health endpoint
        try:
            health_response = await client.get(f"{base_url}/health")
            print(f"Health check status: {health_response.status_code}")
            print(f"Health check response: {health_response.text}")
        except Exception as e:
            print(f"Health check failed: {e}")
            return False
        
        # Test OpenAPI docs
        try:
            docs_response = await client.get(f"{base_url}/docs")
            print(f"Docs status: {docs_response.status_code}")
        except Exception as e:
            print(f"Docs check failed: {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("Testing FastAPI application...")
    if asyncio.run(test_fastapi_app()):
        print("\nFastAPI application tests completed successfully!")
    else:
        print("\nFastAPI application tests failed!")
        sys.exit(1)
