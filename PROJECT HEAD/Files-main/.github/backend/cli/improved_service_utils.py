"""
Service utilities for CodexFlō with improved error handling and resource management
"""
import asyncio
import time
import logging
import requests
import subprocess
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

async def wait_for_service_ready(url: str, timeout: int = 30, interval: float = 1.0) -> bool:
    """Wait for a service to become available with improved error handling"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=min(5, interval))
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass
        
        await asyncio.sleep(interval)
    
    return False

def validate_config_data(config: Dict[str, Any]) -> List[str]:
    """Validate configuration structure and required fields"""
    errors = []
    
    # Required top-level sections
    required_sections = ["app", "ai", "storage"]
    for section in required_sections:
        if section not in config:
            errors.append(f"Missing required section: {section}")
    
    # AI configuration validation
    if "ai" in config:
        ai_config = config["ai"]
        provider = ai_config.get("provider")
        
        # Check for API key if using cloud providers
        if provider in ["openai", "anthropic", "gemini"]:
            api_key = ai_config.get("api_key")
            if not api_key or api_key.startswith("${"):
                errors.append(f"API key required for {provider} provider")
    
    return errors

def safe_process_cleanup(process: subprocess.Popen, timeout: int = 5) -> None:
    """Safely terminate a process with timeout and fallback to kill"""
    if process and process.poll() is None:  # Process still running
        try:
            process.terminate()
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        except Exception as e:
            logger.warning(f"Error cleaning up process: {e}")

class ProcessManager:
    """Manage subprocess lifecycle with proper cleanup"""
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
    
    def add(self, process: subprocess.Popen) -> None:
        """Add process to managed list"""
        if process:
            self.processes.append(process)
    
    def remove(self, process: subprocess.Popen) -> None:
        """Remove process from managed list"""
        if process in self.processes:
            self.processes.remove(process)
    
    def cleanup_all(self) -> None:
        """Clean up all managed processes"""
        for proc in self.processes[:]:  # Work on a copy to avoid modification during iteration
            safe_process_cleanup(proc)
            self.remove(proc)