#!/usr/bin/env python3
"""
CodexFlō Improved System - Best Practices Implementation
Comprehensive fixes and improvements for production-ready operation
"""

import asyncio
import typer
import logging
import signal
import atexit
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Protocol
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import json
import yaml
import hashlib
import subprocess
import sys
import os
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor
import aiofiles
import aiohttp
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.logging import RichHandler
import structlog

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

# Structured logging setup
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
console = Console()

# Custom Exceptions with proper hierarchy
class CodexFloError(Exception):
    """Base exception for CodexFlō system"""
    pass

class ConfigurationError(CodexFloError):
    """Configuration-related errors"""
    pass

class ProcessingError(CodexFloError):
    """Document processing errors"""
    pass

class SecurityError(CodexFloError):
    """Security and compliance errors"""
    pass

class ServiceError(CodexFloError):
    """Service startup/management errors"""
    pass

# Type definitions and protocols
class ProcessingEngine(Protocol):
    """Protocol for processing engines"""
    async def initialize(self) -> None: ...
    async def process(self, data: Any) -> Dict[str, Any]: ...
    async def health_check(self) -> bool: ...

@dataclass(frozen=True)
class SystemConfig:
    """Immutable system configuration"""
    app_name: str
    version: str
    storage_path: Path
    ai_provider: str
    api_key: str
    modules: Dict[str, bool]
    security_settings: Dict[str, Any]

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'SystemConfig':
        """Create config from dictionary with validation"""
        try:
            return cls(
                app_name=config_dict['app']['name'],
                version=config_dict['app']['version'],
                storage_path=Path(config_dict['storage']['base_path']),
                ai_provider=config_dict['ai']['provider'],
                api_key=config_dict['ai']['api_key'],
                modules=config_dict.get('modules', {}),
                security_settings=config_dict.get('security', {})
            )
        except KeyError as e:
            raise ConfigurationError(f"Missing required configuration: {e}")

@dataclass
class ProcessingResult:
    """Standardized processing result"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class ResourceManager:
    """Centralized resource management with proper cleanup"""

    def __init__(self):
        self._resources: List[Any] = []
        self._cleanup_registered = False

    def register_resource(self, resource: Any) -> None:
        """Register a resource for cleanup"""
        self._resources.append(resource)
        if not self._cleanup_registered:
            self._setup_cleanup_handlers()

    def _setup_cleanup_handlers(self) -> None:
        """Setup signal handlers for graceful cleanup"""
        def cleanup_handler(signum=None, frame=None):
            logger.info("Starting resource cleanup")
            for resource in self._resources:
                try:
                    if hasattr(resource, 'close'):
                        resource.close()
                    elif hasattr(resource, 'terminate'):
                        resource.terminate()
                        if hasattr(resource, 'wait'):
                            try:
                                resource.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                if hasattr(resource, 'kill'):
                                    resource.kill()
                except Exception as e:
                    logger.warning("Error during cleanup", resource=str(resource), error=str(e))

            self._resources.clear()
            logger.info("Resource cleanup complete")
            if signum:
                sys.exit(0)

        signal.signal(signal.SIGINT, cleanup_handler)
        signal.signal(signal.SIGTERM, cleanup_handler)
        atexit.register(cleanup_handler)
        self._cleanup_registered = True

# Global resource manager
resource_manager = ResourceManager()

class ConfigValidator:
    """Comprehensive configuration validation"""

    @staticmethod
    def validate_config(config_dict: Dict[str, Any]) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []

        # Required sections
        required_sections = ['app', 'ai', 'storage', 'modules']
        for section in required_sections:
            if section not in config_dict:
                errors.append(f"Missing required section: {section}")

        # AI configuration validation
        if 'ai' in config_
