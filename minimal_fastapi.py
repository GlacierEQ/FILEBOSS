"""
Minimal FastAPI application for testing.
"""
from fastapi import FastAPI
import uvicorn
import sys
import os

print("=" * 60)
print("🚀 Starting Minimal FastAPI Test Application")
print("=" * 60)
print(f"Python: {sys.version}")
print(f"Working Directory: {os.getcwd()}")
print(f"Python Path: {sys.path}")

# Create a minimal FastAPI app
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    print("\nEndpoints:")
    print("  - GET /           - Simple hello world")
    print("  - GET /health     - Health check")
    print("\nPress Ctrl+C to stop the server")
    
    # Run with explicit host and port
    uvicorn.run(
        "minimal_fastapi:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="debug"
    )
