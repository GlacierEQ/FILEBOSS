"""FILEBOSS Core - Main Application Entry Point"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

from .plugin_manager import PluginManager
from .event_bus import EventBus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileBossCore:
    """Main FILEBOSS application core built on Sigma File Manager 2 foundation"""
    
    def __init__(self):
        self.app = FastAPI(
            title="FILEBOSS - Hyper-Powerful File Manager",
            description="Modular file management system with tabbed interface",
            version="2.0.0-alpha"
        )
        
        # Core systems
        self.event_bus = EventBus()
        self.plugin_manager = PluginManager(self.event_bus)
        
        # Track loaded plugins
        self.loaded_plugins: Dict[str, Any] = {}
        
        # Setup application
        self._setup_routes()
        self._setup_middleware()
        
        logger.info("🚀 FILEBOSS Core initialized")
    
    def _setup_routes(self):
        """Setup core API routes"""
        
        @self.app.get("/")
        async def root():
            return {
                "name": "FILEBOSS",
                "version": "2.0.0-alpha",
                "description": "Hyper-Powerful Modular File Manager",
                "status": "active",
                "plugins_loaded": len(self.loaded_plugins)
            }
        
        @self.app.get("/api/plugins")
        async def list_plugins():
            """List all loaded plugins"""
            return {
                "plugins": [
                    {
                        "id": plugin_id,
                        "metadata": plugin.metadata.dict() if hasattr(plugin, 'metadata') else {}
                    }
                    for plugin_id, plugin in self.loaded_plugins.items()
                ]
            }
        
        @self.app.get("/api/tabs")
        async def get_tab_components():
            """Get all available tab components from plugins"""
            tabs = []
            for plugin_id, plugin in self.loaded_plugins.items():
                if hasattr(plugin, 'get_tab_component'):
                    try:
                        tab_component = plugin.get_tab_component()
                        tabs.append({
                            "plugin_id": plugin_id,
                            "component": tab_component.dict() if hasattr(tab_component, 'dict') else tab_component
                        })
                    except Exception as e:
                        logger.error(f"Error getting tab component for {plugin_id}: {e}")
            return {"tabs": tabs}
        
        @self.app.post("/api/events/{event_name}")
        async def emit_event(event_name: str, request: Request):
            """Emit event to all subscribed plugins"""
            try:
                data = await request.json()
                self.event_bus.emit(event_name, data)
                return {"status": "success", "event": event_name}
            except Exception as e:
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "message": str(e)}
                )
    
    def _setup_middleware(self):
        """Setup application middleware"""
        
        @self.app.middleware("http")
        async def log_requests(request: Request, call_next):
            logger.info(f"📡 {request.method} {request.url.path}")
            response = await call_next(request)
            return response
    
    def load_plugins(self, plugin_directory: str = "src/plugins/"):
        """Load all plugins from directory"""
        logger.info(f"🔌 Loading plugins from {plugin_directory}")
        
        # Discover and load plugins
        discovered = list(self.plugin_manager.discover_plugins(plugin_directory))
        logger.info(f"🔍 Discovered {len(discovered)} plugins: {discovered}")
        
        for plugin_name in discovered:
            if self.plugin_manager.load_plugin(plugin_name):
                plugin = self.plugin_manager.get_plugin(plugin_name)
                if plugin:
                    self.loaded_plugins[plugin_name] = plugin
                    logger.info(f"✅ Loaded plugin: {plugin_name}")
                else:
                    logger.error(f"❌ Failed to get plugin: {plugin_name}")
            else:
                logger.error(f"❌ Failed to load plugin: {plugin_name}")
        
        logger.info(f"🎯 Successfully loaded {len(self.loaded_plugins)} plugins")
    
    def start(self) -> FastAPI:
        """Start the FILEBOSS application"""
        logger.info("🔥 FILEBOSS CORE STARTING...")
        
        # Load plugins
        self.load_plugins()
        
        # Setup plugin routes
        self._setup_plugin_routes()
        
        logger.info("⚡ FILEBOSS READY FOR ACTION!")
        return self.app
    
    def _setup_plugin_routes(self):
        """Setup routes from loaded plugins"""
        for plugin_id, plugin in self.loaded_plugins.items():
            if hasattr(plugin, 'get_routes'):
                try:
                    routes = plugin.get_routes()
                    if routes:
                        self.app.include_router(routes, prefix=f"/api/{plugin_id}")
                        logger.info(f"📡 Added routes for plugin: {plugin_id}")
                except Exception as e:
                    logger.error(f"❌ Failed to add routes for {plugin_id}: {e}")

# Global instance
app_core = FileBossCore()