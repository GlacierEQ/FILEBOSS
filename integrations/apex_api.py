"""APEX FILEBOSS API Layer
FastAPI endpoints exposing APEX orchestration capabilities
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from .apex_orchestrator import get_orchestrator, shutdown_orchestrator

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/apex", tags=["APEX Orchestration"])


# ==================== REQUEST/RESPONSE MODELS ====================

class FileProcessRequest(BaseModel):
    """Request model for file processing"""
    file_path: str = Field(..., description="Path to file to process")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata")
    bucket: str = Field(default="fileboss", description="Memory bucket to store in")


class SearchRequest(BaseModel):
    """Request model for intelligent search"""
    query: str = Field(..., description="Search query")
    limit: int = Field(default=20, ge=1, le=100, description="Max results per source")
    sources: Optional[List[str]] = Field(
        default=None,
        description="Specific sources to search (memory, github, notion)"
    )


class OperatorTaskRequest(BaseModel):
    """Request model for operator delegation"""
    task: str = Field(..., description="Task description")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Task context")
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")


class MemoryStoreRequest(BaseModel):
    """Request model for memory storage"""
    content: str = Field(..., description="Content to store")
    bucket: str = Field(default="fileboss", description="Memory bucket")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata")


class BatchProcessRequest(BaseModel):
    """Request model for batch file processing"""
    file_paths: List[str] = Field(..., description="List of file paths")
    bucket: str = Field(default="fileboss_batch", description="Memory bucket")
    parallel: bool = Field(default=True, description="Process in parallel")


# ==================== API ENDPOINTS ====================

@router.get("/health", summary="APEX Health Check")
async def apex_health():
    """
    Check health status of all APEX integrated systems:
    - Memory Plugin MCP
    - Supermemory AI MCP
    - Mem0 API
    - GitHub MCP
    - Notion MCP
    - Operator Code MCP
    """
    try:
        orchestrator = await get_orchestrator()
        health_status = await orchestrator.health_check()
        
        # Calculate overall health score
        systems = health_status["systems"]
        ok_count = sum(1 for status in systems.values() if "🟢" in status)
        total_count = len(systems)
        health_score = (ok_count / total_count) * 100 if total_count > 0 else 0
        
        return {
            "status": "healthy" if health_score > 70 else "degraded" if health_score > 40 else "unhealthy",
            "health_score": round(health_score, 1),
            "systems": systems,
            "timestamp": health_status["timestamp"],
            "integration_level": "APEX Quantum Entangled"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.post("/process", summary="Process File Through APEX Pipeline")
async def process_file(request: FileProcessRequest, background_tasks: BackgroundTasks):
    """
    Process a file through the complete APEX pipeline:
    1. Extract metadata
    2. Store in Memory Triad (Memory Plugin + Supermemory + Mem0)
    3. Sync with GitHub MCP
    4. Index in Notion MCP
    5. Return comprehensive processing report
    """
    try:
        orchestrator = await get_orchestrator()
        
        # Process file
        result = await orchestrator.process_file(
            file_path=request.file_path,
            metadata=request.metadata
        )
        
        return {
            "status": "success",
            "file": request.file_path,
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "File processed through APEX pipeline"
        }
    except Exception as e:
        logger.error(f"File processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/search", summary="Intelligent Multi-Source Search")
async def intelligent_search(request: SearchRequest):
    """
    Perform intelligent search across all integrated systems:
    - Memory Triad (3 memory systems)
    - GitHub repositories (538+ repos)
    - Notion workspace (complete documentation)
    - Operator Code tools (4000+ tools)
    
    Returns unified, ranked results from all sources.
    """
    try:
        orchestrator = await get_orchestrator()
        
        # Execute search
        search_results = await orchestrator.intelligent_search(request.query)
        
        # Count total results
        total_results = 0
        for source, data in search_results["sources"].items():
            if isinstance(data, dict) and "data" in data:
                if isinstance(data["data"], list):
                    total_results += len(data["data"])
        
        return {
            "status": "success",
            "query": request.query,
            "total_results": total_results,
            "results": search_results,
            "timestamp": search_results["timestamp"]
        }
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/delegate", summary="Delegate Task to Operator Code MCP")
async def delegate_task(request: OperatorTaskRequest):
    """
    Delegate complex tasks to Operator Code MCP (4000+ specialized tools).
    
    The task will be:
    1. Sent to Operator Code MCP for execution
    2. Result stored in Memory Triad for future reference
    3. Comprehensive execution report returned
    """
    try:
        orchestrator = await get_orchestrator()
        
        # Add priority to context
        context = request.context or {}
        context["priority"] = request.priority
        
        # Delegate task
        result = await orchestrator.operator_delegate(
            task=request.task,
            context=context
        )
        
        return {
            "status": "success",
            "task": request.task,
            "priority": request.priority,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Task delegation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Delegation failed: {str(e)}")


@router.post("/memory/store", summary="Store Memory in Triad")
async def store_memory(request: MemoryStoreRequest):
    """
    Store content across all three memory systems:
    - Memory Plugin MCP (session persistence)
    - Supermemory AI MCP (universal memory with OAuth)
    - Mem0 API (contradiction detection, graph memory)
    
    Returns storage confirmation from all three systems.
    """
    try:
        orchestrator = await get_orchestrator()
        
        # Store in memory triad
        result = await orchestrator.memory_triad.store(
            content=request.content,
            bucket=request.bucket,
            metadata=request.metadata
        )
        
        # Count successful stores
        success_count = sum(1 for v in result.values() if "error" not in v)
        
        return {
            "status": "success" if success_count > 0 else "partial_failure",
            "stored_in": success_count,
            "total_systems": len(result),
            "details": result,
            "bucket": request.bucket,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Memory storage failed: {e}")
        raise HTTPException(status_code=500, detail=f"Storage failed: {str(e)}")


@router.get("/memory/recall", summary="Recall Memory from Triad")
async def recall_memory(query: str, bucket: str = "fileboss", limit: int = 10):
    """
    Recall memories from all three memory systems and return unified results.
    """
    try:
        orchestrator = await get_orchestrator()
        
        # Recall from memory triad
        result = await orchestrator.memory_triad.recall(
            query=query,
            bucket=bucket,
            limit=limit
        )
        
        return {
            "status": "success",
            "query": query,
            "bucket": bucket,
            "results": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Memory recall failed: {e}")
        raise HTTPException(status_code=500, detail=f"Recall failed: {str(e)}")


@router.post("/batch-process", summary="Batch Process Multiple Files")
async def batch_process(request: BatchProcessRequest, background_tasks: BackgroundTasks):
    """
    Process multiple files in batch through the APEX pipeline.
    Can process in parallel for faster execution.
    """
    try:
        orchestrator = await get_orchestrator()
        
        results = []
        
        if request.parallel:
            # Process in parallel
            import asyncio
            tasks = [
                orchestrator.process_file(file_path, metadata={"batch": True})
                for file_path in request.file_paths
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Process sequentially
            for file_path in request.file_paths:
                try:
                    result = await orchestrator.process_file(
                        file_path,
                        metadata={"batch": True}
                    )
                    results.append(result)
                except Exception as e:
                    results.append({"error": str(e), "file": file_path})
        
        # Count successes
        success_count = sum(
            1 for r in results
            if isinstance(r, dict) and r.get("status") == "success"
        )
        
        return {
            "status": "completed",
            "total_files": len(request.file_paths),
            "successful": success_count,
            "failed": len(request.file_paths) - success_count,
            "results": results,
            "bucket": request.bucket,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch failed: {str(e)}")


@router.post("/upload", summary="Upload and Process File")
async def upload_file(file: UploadFile = File(...), bucket: str = "uploads"):
    """
    Upload a file and immediately process it through APEX pipeline.
    """
    try:
        import tempfile
        import os
        
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Process the file
        orchestrator = await get_orchestrator()
        result = await orchestrator.process_file(
            tmp_path,
            metadata={
                "original_filename": file.filename,
                "content_type": file.content_type,
                "size": len(content)
            }
        )
        
        # Cleanup temp file
        os.unlink(tmp_path)
        
        return {
            "status": "success",
            "filename": file.filename,
            "size": len(content),
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/stats", summary="APEX Integration Statistics")
async def get_stats():
    """
    Get comprehensive statistics about APEX integration:
    - Memory usage across all systems
    - File processing count
    - Search query count
    - Operator delegations
    """
    try:
        orchestrator = await get_orchestrator()
        
        # Get health status (includes system info)
        health = await orchestrator.health_check()
        
        return {
            "status": "success",
            "integration": {
                "name": "APEX FILEBOSS",
                "version": "2.0.0-alpha",
                "context_global": orchestrator.config.context_global,
                "context_direct": orchestrator.config.context_direct
            },
            "systems": health["systems"],
            "connected_services": [
                "Memory Plugin MCP",
                "Supermemory AI MCP",
                "Mem0 API",
                "GitHub MCP (538+ repos)",
                "Notion MCP",
                "Operator Code MCP (4000+ tools)"
            ],
            "capabilities": [
                "File Processing",
                "Intelligent Multi-Source Search",
                "Memory Triad Storage",
                "Task Delegation to Operator Code",
                "Batch Processing",
                "Real-time Health Monitoring"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats failed: {str(e)}")


# Lifespan events
@router.on_event("startup")
async def startup_event():
    """Initialize APEX orchestrator on startup"""
    logger.info("🚀 Initializing APEX FILEBOSS orchestrator...")
    orchestrator = await get_orchestrator()
    health = await orchestrator.health_check()
    logger.info(f"✅ APEX orchestrator ready | Systems: {health['systems']}")


@router.on_event("shutdown")
async def shutdown_event():
    """Cleanup APEX orchestrator on shutdown"""
    logger.info("👋 Shutting down APEX orchestrator...")
    await shutdown_orchestrator()
    logger.info("✅ APEX orchestrator shutdown complete")
