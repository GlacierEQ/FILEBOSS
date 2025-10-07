# FILEBOSS Core Foundation
# Sigma File Manager 2 Integration Layer

__version__ = "2.0.0-alpha"
__description__ = "Hyper-Powerful Modular File Manager with Tabbed Interface"

from .main import FileBossCore
from .plugin_manager import PluginManager
from .event_bus import EventBus

__all__ = ["FileBossCore", "PluginManager", "EventBus"]