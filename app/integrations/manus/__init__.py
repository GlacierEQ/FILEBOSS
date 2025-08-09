""
APEX MANUS Integration Hub

A powerful integration framework for connecting various services and platforms
with advanced synchronization, versioning, and conflict resolution capabilities.
"""
__version__ = "0.1.0"

# Core components
from .core.base_integration import BaseIntegration, IntegrationConfig
from .core.manager import IntegrationManager

# Connectors
from .connectors.base_connector import BaseConnector

# Models
from .models.base import (
    BaseResource,
    ResourceType,
    SyncStatus,
    SyncResult,
    SyncBatch
)

# Initialize the global integration manager
manager = IntegrationManager()

__all__ = [
    # Core
    'BaseIntegration',
    'IntegrationConfig',
    'IntegrationManager',
    'manager',
    
    # Connectors
    'BaseConnector',
    
    # Models
    'BaseResource',
    'ResourceType',
    'SyncStatus',
    'SyncResult',
    'SyncBatch',
    
    # Version
    '__version__',
]
