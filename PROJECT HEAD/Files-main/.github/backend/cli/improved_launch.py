"""
Improved launch function for CodexFlō CLI with enhanced error handling and resource management
"""
import sys
import time
import asyncio
import subprocess
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import yaml
import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel

# Import from the improved service utils
from improved_service_utils import wait_for_service_ready, ProcessManager, safe_process_cleanup

logger = logging.getLogger(__name__)
console = Console()

class ServiceError(Exception):
    """Service startup/management error"""
    pass

class ValidationError(Exception):
    """Input validation error"""
    pass

def validate_path(path: str, must_exist: bool = False, must_be_dir: bool = False) -> Path:
    """Validate and sanitize file paths"""
    try:
        path_obj = Path(path).expanduser().resolve()
        
        if must_exist and not path_obj.exists():
            raise ValidationError(f"Path does not exist: {path}")
        
        if must_be_dir and path_obj.exists() and not path_obj.is_dir():
            raise ValidationError(f"Path is not a directory: {path}")
        
        return path_obj
    except Exception as e:
        raise ValidationError(f"Invalid path '{path}': {e}")

def check_port_available(port: int) -> bool:
    """Check if a port is available"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return True
        except OSError:
            return False

async def launch_service(
    watch_dir: str = "./",
    agent: str = "Codex Architect",
    config: str = "config/ai_file_explorer.yml",
    port: int = 8000,
    dev: bool = False,
    gui: bool = True,
    health_check: bool = True,
    retry_attempts: int = 3
):
    """Launch CodexFlō with improved error handling and resource management"""
    process_manager = ProcessManager()
    
    try:
        # Validate config
        config_path = validate_path(config, must_exist=True)
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Validate watch directory
        watch_dir_path = validate_path(watch_dir, must_exist=True, must_be_dir=True)
        
        # Check if port is available
        if not check_port_available(port):
            console.print(f"❌ Port {port} is already in use")
            return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            # Start backend with retry mechanism
            task1 = progress.add_task("Starting backend server...", total=100)
            
            backend_cmd = [
                sys.executable, "-m", "backend.main",
                "--config", str(config_path),
                "--port", str(port),
                "--watch-dir", str(watch_dir_path),
                "--agent", agent
            ]
            
            if dev:
                backend_cmd.append("--reload")
            
            # Start backend with retry mechanism
            backend_process = None
            for attempt in range(retry_attempts):
                try:
                    backend_process = subprocess.Popen(
                        backend_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    process_manager.add(backend_process)
                    progress.update(task1, advance=30, description=f"Backend server starting (attempt {attempt+1})...")
                    
                    # Wait for backend to be ready with health check
                    backend_url = f"http://localhost:{port}/health"
                    if await wait_for_service_ready(backend_url, timeout=10):
                        progress.update(task1, advance=70, description="✅ Backend server ready")
                        break
                    else:
                        safe_process_cleanup(backend_process)
                        process_manager.remove(backend_process)
                        if attempt == retry_attempts - 1:
                            raise ServiceError("Backend failed to start within timeout")
                        progress.update(task1, description=f"Retrying backend startup ({attempt+1}/{retry_attempts})...")
                except (subprocess.SubprocessError, OSError) as e:
                    if attempt == retry_attempts - 1:
                        raise ServiceError(f"Failed to start backend: {e}")
                    progress.update(task1, description=f"Retrying backend startup ({attempt+1}/{retry_attempts})...")
                    time.sleep(2)
            
            if backend_process is None or backend_process.poll() is not None:
                raise ServiceError("Failed to start backend server")
            
            # Start frontend if GUI enabled
            frontend_process = None
            if gui:
                task2 = progress.add_task("Starting GUI interface...", total=100)
                
                if dev:
                    frontend_cmd = ["npm", "run", "dev"]
                else:
                    frontend_cmd = ["npm", "start"]
                
                try:
                    frontend_process = subprocess.Popen(
                        frontend_cmd,
                        cwd="frontend",
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    process_manager.add(frontend_process)
                    
                    # Wait for frontend to be ready
                    frontend_url = f"http://localhost:{port+1}"  # Assuming frontend runs on next port
                    if health_check and not await wait_for_service_ready(frontend_url, timeout=15):
                        console.print("⚠️ Frontend may not be ready, but continuing...")
                    
                    progress.update(task2, advance=100, description="✅ GUI interface ready")
                except (subprocess.SubprocessError, OSError) as e:
                    console.print(f"⚠️ GUI interface failed to start: {e}")
                    console.print("Continuing with backend only...")
            
            # Display service information
            console.print(f"\n🌐 CodexFlō running at http://localhost:{port}")
            console.print(f"👁️  Watching directory: {watch_dir_path}")
            console.print(f"🤖 AI Agent: {agent}")
            console.print("\n[bold yellow]Press Ctrl+C to stop[/bold yellow]")
            
            # Keep running with proper signal handling
            try:
                if backend_process:
                    exit_code = backend_process.wait()
                    if exit_code != 0:
                        console.print(f"⚠️ Backend exited with code {exit_code}")
                        stderr = backend_process.stderr.read()
                        if stderr:
                            logger.error(f"Backend error: {stderr}")
            except KeyboardInterrupt:
                pass
    
    except (ValidationError, ServiceError) as e:
        console.print(f"❌ Launch failed: {e}")
        return False
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}")
        logger.exception("Launch error")
        return False
    finally:
        # Ensure cleanup happens
        process_manager.cleanup_all()
    
    return True

# Example usage:
# if __name__ == "__main__":
#     asyncio.run(launch_service())