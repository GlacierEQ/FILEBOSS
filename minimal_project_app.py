"""
Minimal FastAPI application using the project's structure with simplified settings.
"""
import os
import sys
from pathlib import Path
from typing import List

# Add project root to path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("=" * 60)
print("🚀 Starting Minimal Project Application")
print("=" * 60)

# Set environment variables for testing
os.environ["CORS_ORIGINS"] = "*"
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./fileboss.db"

# Import FastAPI
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Create a minimal FastAPI app
app = FastAPI(
    title="FileBoss Minimal",
    description="Minimal FastAPI application for testing",
    version="0.1.0",
    debug=True
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple endpoints
@app.get("/")
async def root():
    return {
        "message": "Welcome to the minimal FileBoss API",
        "status": "running",
        "environment": os.getenv("ENVIRONMENT", "unknown")
    }

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "database": "sqlite"  # Simplified for testing
    }

# Database test endpoint
@app.get("/test-db")
async def test_db():
    try:
        # Try to import and use the database
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        
        # Create a simple SQLite engine
        engine = create_engine("sqlite:///./fileboss.db")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Test the connection
        with SessionLocal() as db:
            result = db.execute(text("SELECT 1"))
            db_test = result.scalar() == 1
        
        return {
            "status": "ok",
            "database": "connected" if db_test else "error",
            "message": "Database connection test successful"
        }
    except Exception as e:
        return {
            "status": "error",
            "database": "error",
            "message": f"Database connection failed: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    
    print("\nEndpoints:")
    print("  - GET /           - Welcome message")
    print("  - GET /health     - Health check")
    print("  - GET /test-db    - Database connection test")
    print("\nStarting server on http://127.0.0.1:8000")
    print("Press Ctrl+C to stop the server")
    
    # Run the server
    uvicorn.run(
        "minimal_project_app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )
