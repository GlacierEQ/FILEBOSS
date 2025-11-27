"""FILEBOSS APEX Integrations Package

This package contains the complete APEX orchestration system:
- apex_orchestrator: Core orchestration logic (Memory Triad + MCP servers)
- apex_api: FastAPI endpoints for APEX operations

Context Global: LFVBLPUL3N8N8K2FLYGCSCKMSMSRHSG9
Context Direct: yD4IKCdlI0VCXlfD4xLT1x5D0dEU9Hd1
"""

from .apex_orchestrator import (
    ApexFileBossOrchestrator,
    get_orchestrator,
    shutdown_orchestrator,
    ApexConfig,
    MemoryTriad,
    MCPOrchestrator
)

from .apex_api import router as apex_router

__version__ = "2.0.0-APEX"
__all__ = [
    "ApexFileBossOrchestrator",
    "get_orchestrator",
    "shutdown_orchestrator",
    "ApexConfig",
    "MemoryTriad",
    "MCPOrchestrator",
    "apex_router"
]
