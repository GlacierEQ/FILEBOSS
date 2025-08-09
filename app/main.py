import logging
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from app.core.config import settings
from app.db.session import engine, Base, SessionLocal
from app.api.v1.api import api_router
from app.db.init_db import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="FileBoss API - A powerful file management system",
        version="0.1.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )
    
    # Set up CORS
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    return app

app = create_application()

@app.on_event("startup")
def startup_event():
    """Initialize services on application startup"""
    logger.info("Starting up application...")
    
    # Create database tables
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Initialize database with first superuser
    logger.info("Initializing database...")
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
    
    logger.info("Application startup complete")

@app.get("/")
async def root():
    return {
        "message": "Welcome to FileBoss API",
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
