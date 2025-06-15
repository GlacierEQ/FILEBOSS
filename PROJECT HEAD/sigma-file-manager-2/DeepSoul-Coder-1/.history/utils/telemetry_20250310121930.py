"""
Telemetry utilities for DeepSeek-Coder.
Provides anonymous usage telemetry for improving the model.
All telemetry can be disabled by setting ENABLE_TELEMETRY=false.
"""

import os
import sys
import json
import uuid
import time
import logging
import platform
import threading
import socket
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
import requests
from urllib.parse import urlparse

# Configure logging
logger = logging.getLogger(__name__)

# Default telemetry endpoint
DEFAULT_TELEMETRY_ENDPOINT = "https://telemetry.deepseek.com/v1/events"

@dataclass
class TelemetryEvent:
    """Represents a telemetry event to be sent."""
    
    event_type: str
    timestamp: float = field(default_factory=time.time)
    version: str = "1.0"
    
    # Runtime info
    runtime_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    platform_info: Dict[str, str] = field(default_factory=dict)
    
    # Event-specific data (varies by event type)
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return asdict(self)


class TelemetryManager:
    """
    Manages telemetry events for DeepSeek-Coder.
    Collects anonymous usage statistics to improve the product.
    """
    
    def __init__(
        self,
        enabled: bool = True,
        endpoint: str = DEFAULT_TELEMETRY_ENDPOINT,
        session_id: Optional[str] = None,
        queue_size: int = 100,
        flush_interval: int = 300  # 5 minutes
    ):
        """
        Initialize the telemetry manager.
        
        Args:
            enabled: Whether telemetry is enabled
            endpoint: Telemetry endpoint URL
            session_id: Optional session ID (generated if not provided)
            queue_size: Maximum queue size before forced flush
            flush_interval: Flush interval in seconds
        """
        self.enabled = enabled and not self._is_ci_environment()
        self.endpoint = endpoint
        self.session_id = session_id or str(uuid.uuid4())
        self.installation_id = self._get_installation_id()
        self.queue_size = queue_size
        self.flush_interval = flush_interval
        
        # Initialize queue and lock
        self.event_queue: List[TelemetryEvent] = []
        self.queue_lock = threading.RLock()
        
        # Start background thread if enabled
        self.flush_thread = None
        if self.enabled:
            self._start_flush_thread()
            self._send_startup_event()
        
        logger.debug(f"Telemetry {'enabled' if self.enabled else 'disabled'}")
    
    def _is_ci_environment(self) -> bool:
        """Check if running in a CI environment (where we should disable telemetry)."""
        return any(env in os.environ for env in [
            'CI', 'GITHUB_ACTIONS', 'TRAVIS', 'CIRCLECI', 'GITLAB_CI',
            'JENKINS_URL', 'TEAMCITY_VERSION'
        ])
    
    def _get_installation_id(self) -> str:
        """Get or generate a stable installation ID."""
        id_file = os.path.expanduser("~/.deepseek/installation_id")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(id_file), exist_ok=True)
        
        # Try to read existing ID
        if os.path.exists(id_file):
            try:
                with open(id_file, "r") as f:
                    return f.read().strip()
            except:
                pass
        
        # Generate new ID
        installation_id = str(uuid.uuid4())
        
        # Try to save it
        try:
            with open(id_file, "w") as f:
                f.write(installation_id)
        except:
            logger.debug("Could not save installation ID")
        
        return installation_id
    
    def _start_flush_thread(self):
        """Start background thread for periodic flushing."""
        self.flush_thread = threading.Thread(
            target=self._periodic_flush,
            daemon=True,
            name="TelemetryFlush"
        )
        self.flush_thread.start()
    
    def _periodic_flush(self):
        """Periodically flush the event queue."""
        while True:
            try:
                time.sleep(self.flush_interval)
                self.flush()
            except Exception as e:
                # Never let telemetry crash the application
                logger.debug(f"Error in telemetry flush thread: {e}")
    
    def _collect_platform_info(self) -> Dict[str, str]:
        """Collect anonymized platform information."""
        info = {}
        
        # OS info (without specific version)
        info["os_family"] = platform.system()
        info["architecture"] = platform.machine()
        
        # Python info
        info["python_version"] = platform.python_version()
        
        # PyTorch/CUDA info
        try:
            import torch
            info["torch_version"] = torch.__version__
            info["cuda_available"] = "True" if torch.cuda.is_available() else "False"
            if torch.cuda.is_available():
                info["gpu_count"] = str(torch.cuda.device_count())
                # Only include GPU name, not specific model numbers
                if torch.cuda.device_count() > 0:
                    gpu_name = torch.cuda.get_device_name(0)
                    # Extract just the GPU family name
                    if "NVIDIA" in gpu_name:
                        if "RTX" in gpu_name:
                            info["gpu_type"] = "NVIDIA RTX"
                        elif "GTX" in gpu_name:
                            info["gpu_type"] = "NVIDIA GTX"
                        elif "Tesla" in gpu_name:
                            info["gpu_type"] = "NVIDIA Tesla"
                        elif "Quadro" in gpu_name:
                            info["gpu_type"] = "NVIDIA Quadro"
                        elif "A100" in gpu_name or "H100" in gpu_name:
                            info["gpu_type"] = "NVIDIA Data Center"
                        else:
                            info["gpu_type"] = "NVIDIA Other"
        except ImportError:
            info["torch_available"] = "False"
        
        # Network connectivity (just check if internet is available, not actual IPs)
        try:
            socket.create_connection(("www.google.com", 80), timeout=1)
            info["network_connectivity"] = "True"
        except:
            info["network_connectivity"] = "False"
        
        return info
    
    def track(self, event_type: str, data: Dict[str, Any] = None):
        """
        Track a telemetry event.
        
        Args:
            event_type: Type of event to track
            data: Event-specific data
        """
        if not self.enabled:
            return
        
        event = TelemetryEvent(
            event_type=event_type,
            platform_info=self._collect_platform_info(),
            data=data or {}
        )
        
        # Add to queue
        with self.queue_lock:
            self.event_queue.append(event)
            
            # Flush if queue is getting large
            if len(self.event_queue) >= self.queue_size:
                # Flush in a separate thread to avoid blocking
                threading.Thread(target=self.flush, daemon=True).start()
    
    def _send_startup_event(self):
        """Send a startup event when telemetry is initialized."""
        self.track("system.startup", {
            "session_id": self.session_id,
            "installation_id": self.installation_id
        })
    
    def flush(self):
        """Flush the event queue by sending events to the telemetry endpoint."""
        if not self.enabled:
            return
        
        # Get the current queue and clear it atomically
        with self.queue_lock:
            if not self.event_queue:
                return
            events = self.event_queue
            self.event_queue = []
        
        if not events:
            return
        
        # Prepare payload
        payload = {
            "session_id": self.session_id,
            "installation_id": self.installation_id,
            "events": [event.to_dict() for event in events]
        }
        
        # Send events
        try:
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=5.0
            )
            
            if response.status_code != 200:
                logger.debug(f"Failed to send telemetry: {response.status_code}")
                
                # If backend is unavailable, don't keep retrying
                if response.status_code == 404:
                    self.enabled = False
            
        except Exception as e:
            logger.debug(f"Error sending telemetry: {str(e)}")
    
    def shutdown(self):
        """Shutdown telemetry manager and send final events."""
        if not self.enabled:
            return
        
        # Send shutdown event
        self.track("system.shutdown", {
            "session_duration": time.time() - self.event_queue[0].timestamp if self.event_queue else 0
        })
        
        # Flush remaining events
        self.flush()


# Global telemetry manager instance
_default_manager = None

def get_telemetry_manager() -> TelemetryManager:
    """
    Get or create the default telemetry manager.
    
    Returns:
        The default telemetry manager
    """
    global _default_manager
    if _default_manager is None:
        # Check if telemetry is disabled via environment variable
        enabled = os.environ.get("ENABLE_TELEMETRY", "true").lower() != "false"
        endpoint = os.environ.get("TELEMETRY_ENDPOINT", DEFAULT_TELEMETRY_ENDPOINT)
        _default_manager = TelemetryManager(enabled=enabled, endpoint=endpoint)
    return _default_manager

def track_event(event_type: str, data: Dict[str, Any] = None):
    """
    Track a telemetry event using the default telemetry manager.
    
    Args:
        event_type: Type of event to track
        data: Event-specific data
    """
    manager = get_telemetry_manager()
    manager.track(event_type, data)

def flush_events():
    """Flush all pending telemetry events."""
    manager = get_telemetry_manager()
    manager.flush()

def shutdown_telemetry():
    """Shutdown telemetry and send any pending events."""
    global _default_manager
    if _default_manager is not None:
        _default_manager.shutdown()
        _default_manager = None

# Automatically flush events on module exit
import atexit
atexit.register(shutdown_telemetry)
