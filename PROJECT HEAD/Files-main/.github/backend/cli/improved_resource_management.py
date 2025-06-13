"""
Improved resource management for CodexFlō CLI
"""
import signal
import atexit
import logging
import subprocess
import sys
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

class ProcessManager:
    """Process manager with proper cleanup and signal handling"""
    
    def __init__(self):
        self._processes: List[subprocess.Popen] = []
        self._cleanup_registered = False
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful cleanup"""
        if self._cleanup_registered:
            return
        
        def cleanup_handler(signum=None, frame=None):
            logger.info("Cleaning up processes...")
            self.cleanup_all()
            if signum:
                sys.exit(0)
        
        # Register signal handlers
        signal.signal(signal.SIGINT, cleanup_handler)
        signal.signal(signal.SIGTERM, cleanup_handler)
        atexit.register(cleanup_handler)
        self._cleanup_registered = True
    
    def add(self, process: subprocess.Popen) -> None:
        """Add process to managed list"""
        if process and process.poll() is None:  # Only add running processes
            self._processes.append(process)
    
    def remove(self, process: subprocess.Popen) -> None:
        """Remove process from managed list"""
        if process in self._processes:
            self._processes.remove(process)
    
    def cleanup_all(self) -> None:
        """Clean up all managed processes"""
        for proc in self._processes[:]:  # Work on a copy to avoid modification during iteration
            try:
                if proc.poll() is None:  # Process still running
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
            except Exception as e:
                logger.warning(f"Error cleaning up process: {e}")
            self.remove(proc)
    
    def __len__(self) -> int:
        """Return number of managed processes"""
        return len(self._processes)
    
    def __contains__(self, process: subprocess.Popen) -> bool:
        """Check if process is managed"""
        return process in self._processes

def safe_subprocess_run(
    cmd: List[str], 
    cwd: Optional[str] = None,
    timeout: Optional[int] = None,
    check: bool = False,
    capture_output: bool = True
) -> subprocess.CompletedProcess:
    """Run subprocess with proper error handling and timeout"""
    try:
        return subprocess.run(
            cmd,
            cwd=cwd,
            timeout=timeout,
            check=check,
            capture_output=capture_output,
            text=True
        )
    except subprocess.TimeoutExpired as e:
        logger.error(f"Command timed out after {timeout}s: {' '.join(cmd)}")
        raise
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code {e.returncode}: {' '.join(cmd)}")
        if e.stderr:
            logger.error(f"Error output: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"Failed to execute command: {' '.join(cmd)}")
        logger.exception("Command execution error")
        raise

# Example usage:
# process_manager = ProcessManager()
# try:
#     process = subprocess.Popen(["python", "-m", "http.server"])
#     process_manager.add(process)
#     # Do work...
# finally:
#     process_manager.cleanup_all()