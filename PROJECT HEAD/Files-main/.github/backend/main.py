#!/usr/bin/env python3
"""
CodexFlō Main Backend Service
Integrates all components for seamless operation
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
import argparse
import yaml
import json
from typing import Dict, Any, List
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path
parent_dir = str(Path(__file__).parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import local modules
try:
    from cli.legal_pipeline import LegalPipeline
    from cli.integration import CodexFloIntegration, create_integration
except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    sys.exit(1)

# Create FastAPI app
app = FastAPI(
    title="CodexFlō API",
    description="AI-Driven Strategic File Nexus API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
integration = None
config = {}
processing_queue = asyncio.Queue()
is_processing = False

# Models
class FileRequest(BaseModel):
    path: str

class CaseRequest(BaseModel):
    case_id: str

class ReportRequest(BaseModel):
    report_type: str
    params: Dict[str, Any]

# Startup event
@app.on_event("startup")
async def startup_event():
    global config, integration
    
    # Load configuration
    config_path = os.environ.get("CODEXFLO_CONFIG", "config/ai_file_explorer.yml")
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info(f"Configuration loaded from {config_path}")
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        sys.exit(1)
    
    # Initialize integration
    try:
        integration = await create_integration(config_path)
        if not integration.initialized:
            logger.error("Failed to initialize integration")
            sys.exit(1)
        logger.info("Integration initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing integration: {e}")
        sys.exit(1)
    
    # Start background processing
    asyncio.create_task(process_queue())

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down CodexFlō backend")

# Background processing
async def process_queue():
    global is_processing
    
    while True:
        try:
            is_processing = True
            file_path, callback = await processing_queue.get()
            
            logger.info(f"Processing file: {file_path}")
            result = await integration.process_file(Path(file_path))
            
            if callback:
                await callback(result)
            
            processing_queue.task_done()
            
        except Exception as e:
            logger.error(f"Error in background processing: {e}")
        finally:
            is_processing = processing_queue.qsize() > 0

# Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "components": {
            name: "available" for name in integration.components
        },
        "queue_size": processing_queue.qsize(),
        "is_processing": is_processing
    }

@app.post("/files/process")
async def process_file(file_request: FileRequest, background_tasks: BackgroundTasks):
    """Process a file through the pipeline"""
    file_path = Path(file_request.path)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Add to processing queue
    task_id = f"task_{int(time.time())}_{hash(str(file_path))}"
    await processing_queue.put((str(file_path), None))
    
    return {
        "task_id": task_id,
        "file": str(file_path),
        "status": "queued",
        "queue_position": processing_queue.qsize()
    }

@app.get("/files/status/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a processing task"""
    # In a real implementation, this would check a database for task status
    return {
        "task_id": task_id,
        "status": "processing" if is_processing else "queued",
        "queue_size": processing_queue.qsize()
    }

@app.post("/cases/build")
async def build_case(case_request: CaseRequest):
    """Build a case using the legal pipeline"""
    if "legal_pipeline" not in integration.components:
        raise HTTPException(status_code=400, detail="Legal pipeline not enabled")
    
    result = await integration.build_case(case_request.case_id)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@app.post("/reports/generate")
async def generate_report(report_request: ReportRequest):
    """Generate a report"""
    result = await integration.generate_report(
        report_request.report_type, report_request.params
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@app.get("/ai/health")
async def ai_health():
    """AI engine health check"""
    if "ai_engine" not in integration.components:
        raise HTTPException(status_code=503, detail="AI engine not available")
    
    return {
        "status": "healthy",
        "provider": integration.components["ai_engine"].get("provider", "unknown")
    }

@app.get("/db/health")
async def db_health():
    """Database health check"""
    # Placeholder for database health check
    return {
        "status": "healthy",
        "type": config.get("storage", {}).get("metadata_db", "unknown")
    }

# Main function
def main():
    parser = argparse.ArgumentParser(description="CodexFlō Backend Service")
    parser.add_argument("--config", default="config/ai_file_explorer.yml", help="Configuration file path")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Set environment variable for config path
    os.environ["CODEXFLO_CONFIG"] = args.config
    
    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Start server
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="debug" if args.debug else "info"
    )

if __name__ == "__main__":
    main()