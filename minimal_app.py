"""
Minimal FastAPI application that bypasses the project's configuration system.
"""
from fastapi import FastAPI
import uvicorn
import os

# Create a minimal FastAPI app
app = FastAPI()

# Simple endpoint
@app.get("/")
async def root():
    return {"message": "Hello, World! This is a minimal FastAPI app."}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Health check passed"}

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting Minimal FastAPI Application")
    print("=" * 60)
    print("Endpoints:")
    print("  - GET /           - Simple hello world")
    print("  - GET /health     - Health check")
    print("\nPress Ctrl+C to stop the server")
    
    # Run with explicit host and port, no reload
    uvicorn.run(
        "minimal_app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )
