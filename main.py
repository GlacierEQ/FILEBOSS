# main.py - The Core of the CaseBuilder Application

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the database engine and models from our new structure
from casebuilder.database import engine, Base
# Import the API router
from casebuilder.api import router

# Create the FastAPI app instance
app = FastAPI(
    title="CaseBuilder - Operator Edition",
    description="A robust, scalable, and over-engineered evidence management system.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware to allow all origins (great for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include our API routes
app.include_router(router, prefix="/api", tags=["CaseBuilder API"])

@app.on_event("startup")
async def on_startup():
    """This function runs when the application starts."""
    print("Initializing database...")
    async with engine.begin() as conn:
        # This will create all tables defined in our models
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialized successfully.")

@app.get("/")
def read_root():
    """A root endpoint to welcome users."""
    return {
        "message": "Welcome to CaseBuilder Operator Edition!",
        "documentation": "/docs",
        "api_status": "/health"
    }

@app.get("/health")
def health_check():
    """A health check endpoint for monitoring."""
    return {"status": "ok", "message": "System is fully operational."}


if __name__ == "__main__":
    # This allows running the app directly with `python main.py`
    uvicorn.run(
        "main:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=True, # Auto-reload on code changes
        log_level="info"
    )
