# main.py - FILEBOSS with APEX Orchestration Integration

import uvicorn
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

# Import the database engine and models from our new structure
from casebuilder.database import engine, Base, get_db
from casebuilder.cascade_integration import cascade
# Import the API router
from casebuilder.api import router

# Import APEX integration
try:
    from integrations.apex_api import router as apex_router
    from integrations.apex_orchestrator import shutdown_orchestrator
    APEX_ENABLED = True
except ImportError as e:
    logging.warning(f"APEX integration not available: {e}")
    APEX_ENABLED = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the FastAPI app instance
app = FastAPI(
    title="FILEBOSS - APEX Operator Edition",
    description="""
    🚀 **FILEBOSS with APEX Orchestration**
    
    A hyper-powerful file management and case building system with:
    - **Sigma Files Manager 2** foundation (plugin architecture)
    - **CaseBuilder** evidence management
    - **APEX Integration** (Memory Triad + MCP servers)
    - **Deep Soul Catalyst** AI processing pipeline
    
    ## Integrated Systems
    - 🧠 Memory Plugin MCP (session persistence)
    - 🌐 Supermemory AI MCP (universal memory)
    - 💠 Mem0 API (graph memory)
    - 🐙 GitHub MCP (538+ repos)
    - 📓 Notion MCP (documentation)
    - 🤖 Operator Code MCP (4000+ tools)
    
    Context Global: LFVBLPUL3N8N8K2FLYGCSCKMSMSRHSG9
    """,
    version="2.0.0-APEX",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "System", "description": "System health and status"},
        {"name": "CaseBuilder API", "description": "Evidence management and case building"},
        {"name": "APEX Orchestration", "description": "APEX memory and MCP integration"},
    ]
)

# Add CORS middleware to allow all origins (great for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include CaseBuilder API routes
app.include_router(router, prefix="/api", tags=["CaseBuilder API"])

# Include APEX API routes (if available)
if APEX_ENABLED:
    app.include_router(apex_router, tags=["APEX Orchestration"])
    logger.info("✅ APEX Integration ENABLED")
else:
    logger.warning("⚠️  APEX Integration DISABLED - Install dependencies: pip install httpx")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )

# Request validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

# Enhanced health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """
    Comprehensive health check for all integrated systems:
    - Database connection
    - Cascade AI integration
    - APEX orchestration (if enabled)
    """
    from sqlalchemy import text
    
    health_status = {
        "status": "ok",
        "version": "2.0.0-APEX",
        "integration": "APEX Quantum Entangled" if APEX_ENABLED else "Standard",
        "services": {}
    }
    
    # Check database connection
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        health_status["services"]["database"] = "🟢 OK"
    except Exception as e:
        health_status["services"]["database"] = f"🔴 ERROR: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Cascade connection
    try:
        response = await cascade.query_cascade("test connection")
        health_status["services"]["cascade_ai"] = "🟢 OK"
    except Exception as e:
        health_status["services"]["cascade_ai"] = f"⚠️  WARNING: {str(e)}"
    
    # Check APEX orchestration (if enabled)
    if APEX_ENABLED:
        try:
            from integrations.apex_orchestrator import get_orchestrator
            orchestrator = await get_orchestrator()
            apex_health = await orchestrator.health_check()
            health_status["services"]["apex"] = {
                "status": "🟢 OK",
                "systems": apex_health["systems"]
            }
        except Exception as e:
            health_status["services"]["apex"] = f"⚠️  WARNING: {str(e)}"
    else:
        health_status["services"]["apex"] = "⚠️  NOT ENABLED"
    
    return health_status

@app.on_event("startup")
async def on_startup():
    """Initialize all systems on application startup"""
    logger.info("="*60)
    logger.info("🚀 FILEBOSS APEX Edition Starting...")
    logger.info("="*60)
    
    # Initialize database
    logger.info("💾 Initializing database...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    # Test Cascade connection
    logger.info("🤖 Testing Cascade AI connection...")
    try:
        response = await cascade.query_cascade("test connection")
        logger.info(f"✅ Cascade AI connected: {response.get('status', 'success')}")
    except Exception as e:
        logger.warning(f"⚠️  Cascade AI connection warning: {e}")
    
    # Initialize APEX orchestration
    if APEX_ENABLED:
        logger.info("🌌 Initializing APEX orchestration...")
        try:
            from integrations.apex_orchestrator import get_orchestrator
            orchestrator = await get_orchestrator()
            apex_health = await orchestrator.health_check()
            
            logger.info("✅ APEX Orchestration initialized:")
            for system, status in apex_health["systems"].items():
                logger.info(f"   {system}: {status}")
        except Exception as e:
            logger.warning(f"⚠️  APEX initialization warning: {e}")
    
    logger.info("="*60)
    logger.info("✨ FILEBOSS READY FOR ACTION!")
    logger.info("="*60)
    logger.info(f"   📚 Documentation: http://localhost:8000/docs")
    logger.info(f"   🏛️ API Status: http://localhost:8000/api/status")
    if APEX_ENABLED:
        logger.info(f"   🚀 APEX Health: http://localhost:8000/apex/health")
    logger.info("="*60)

@app.on_event("shutdown")
async def on_shutdown():
    """Cleanup all systems on application shutdown"""
    logger.info("👋 Shutting down FILEBOSS...")
    
    # Close Cascade connection
    try:
        await cascade.close()
        logger.info("✅ Cascade AI connection closed")
    except Exception as e:
        logger.error(f"❌ Cascade shutdown error: {e}")
    
    # Shutdown APEX orchestrator
    if APEX_ENABLED:
        try:
            await shutdown_orchestrator()
            logger.info("✅ APEX orchestrator shutdown complete")
        except Exception as e:
            logger.error(f"❌ APEX shutdown error: {e}")
    
    logger.info("✅ FILEBOSS shutdown complete")

@app.get("/", tags=["System"])
def read_root():
    """
    Welcome endpoint with system information and quick links.
    """
    response = {
        "name": "FILEBOSS",
        "version": "2.0.0-APEX",
        "tagline": "Hyper-Powerful File Management with APEX Orchestration",
        "status": "operational",
        "integration_level": "APEX Quantum Entangled" if APEX_ENABLED else "Standard",
        "links": {
            "documentation": "/docs",
            "health_check": "/health",
            "api_status": "/api/status"
        },
        "features": [
            "Sigma Files Manager 2 Foundation",
            "CaseBuilder Evidence Management",
            "Deep Soul Catalyst AI Pipeline"
        ]
    }
    
    if APEX_ENABLED:
        response["apex_features"] = [
            "Memory Triad (3 memory systems)",
            "GitHub MCP (538+ repos)",
            "Notion MCP (complete docs)",
            "Operator Code MCP (4000+ tools)"
        ]
        response["links"]["apex_health"] = "/apex/health"
        response["links"]["apex_stats"] = "/apex/stats"
    
    return response

if __name__ == "__main__":
    # This allows running the app directly with `python main.py`
    uvicorn.run(
        "main:app", 
        host="0.0.0.0",  # Changed from 127.0.0.1 to allow external access
        port=8000, 
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
