# main.py - The Core of the CaseBuilder Application

import uvicorn
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# Import the database engine and models from our new structure
from casebuilder.db.base import engine, Base
from casebuilder.cascade_integration import cascade
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

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# Request validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Check the health of the application and its dependencies."""
    from sqlalchemy import text
    
    # Check database connection
    db_status = "ok"
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Check Cascade connection
    cascade_status = "ok"
    try:
        await cascade.query_cascade("test connection")
    except Exception as e:
        cascade_status = f"error: {str(e)}"
    
    return {
        "status": "ok",
        "services": {
            "database": db_status,
            "cascade": cascade_status
        },
        "version": "2.0.0"
    }

@app.on_event("startup")
async def on_startup():
    """This function runs when the application starts."""
    print("Initializing database...")
    try:
        async with engine.begin() as conn:
            # This will create all tables defined in our models
            await conn.run_sync(Base.metadata.create_all)
        print("Database initialized successfully.")
        
        # Test Cascade connection
        print("Testing Cascade connection...")
        response = await cascade.query_cascade("test connection")
        print(f"Cascade connection test: {response.get('status', 'success')}")
        
    except Exception as e:
        print(f"Error during startup: {e}")
        raise

@app.on_event("shutdown")
async def on_shutdown():
    """This function runs when the application shuts down."""
    print("Shutting down application...")
    await cascade.close()
    print("Application shutdown complete.")

@app.get("/")
def read_root():
    """A root endpoint to welcome users."""
    return {
        "message": "Welcome to CaseBuilder Operator Edition!",
        "documentation": "/docs",
        "health_check": "/health",
        "api_status": "/api/status"
    }

if __name__ == "__main__":
    # This allows running the app directly with `python main.py`
    uvicorn.run(
        "main:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=True, # Auto-reload on code changes
        log_level="info"
    )
