# -------------------------------------------------------------------
#  CaseBuilder - THE ONE AND ONLY FILE YOU NEED
#  Run with: python app.py
# -------------------------------------------------------------------

import os
import sys
import uvicorn
import webbrowser
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, AsyncGenerator

# --- Check Python Version (Optional but Recommended) ---
def check_python_version():
    if sys.version_info < (3, 8):
        print(f"❌ WARNING: Your Python version ({sys.version_info.major}.{sys.version_info.minor}) is old.")
        print("   The app might work, but Python 3.8+ is recommended.")

# --- FastAPI Application Setup ---
from fastapi import FastAPI, APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

# --- Database Setup (SQLAlchemy) ---
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, func

# Use an in-memory SQLite database for simplicity. No file needed.
DATABASE_URL = "sqlite+aiosqlite:///./casebuilder.db"

engine = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False})
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# --- Database Models ---
class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    description = Column(String)
    case_id = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# --- Pydantic Schemas (for API validation) ---
from pydantic import BaseModel
from datetime import datetime

class EvidenceSchema(BaseModel):
    id: int
    filename: str
    description: Optional[str] = None
    case_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Database Session Dependency ---
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

# --- API Router ---
router = APIRouter()

@router.post("/upload/", response_model=EvidenceSchema, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    case_id: str,
    description: Optional[str] = None,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """Upload a file. It gets saved to the DB."""
    new_evidence = Evidence(
        filename=file.filename,
        description=description,
        case_id=case_id
    )
    db.add(new_evidence)
    await db.commit()
    await db.refresh(new_evidence)
    return new_evidence

@router.get("/case/{case_id}", response_model=List[EvidenceSchema])
async def get_evidence_for_case(
    case_id: str,
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """Get all evidence for a specific case."""
    result = await db.execute(
        Evidence.__table__.select().where(Evidence.case_id == case_id)
    )
    return result.fetchall()

# --- Main FastAPI App ---
app = FastAPI(
    title="CaseBuilder - Simple Edition",
    description="A dead-simple, single-file evidence management API.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(router, prefix="/api", tags=["Evidence"])

@app.get("/")
def read_root():
    """Root endpoint with instructions."""
    return {
        "message": "Welcome to CaseBuilder!",
        "docs_url": "/docs",
        "api_health_check": "/health"
    }

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

# --- Startup and Shutdown Events ---
@app.on_event("startup")
async def startup_event():
    """Create database tables on startup."""
    print("Starting up...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created.")
    # Open browser automatically
    webbrowser.open("http://127.0.0.1:8000/docs")

# --- Main Entry Point to Run the App ---
if __name__ == "__main__":
    check_python_version()
    print("-------------------------------------------------------------------")
    print("🚀 Starting CaseBuilder Server...")
    print("   Your app will be ready at: http://127.0.0.1:8000")
    print("   API Docs will open automatically in your browser.")
    print("   Press CTRL+C to stop the server.")
    print("-------------------------------------------------------------------")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
