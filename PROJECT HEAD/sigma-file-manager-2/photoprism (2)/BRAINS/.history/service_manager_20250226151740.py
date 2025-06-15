import os
import sys
import subprocess
import signal
import time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), 'sorting_service.log'),
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sorting_service')

class SortingHatService:
    """
    Manages the Sorting Hat service processes to keep them running continuously
    """
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.server_process = None
        self.watcher_process = None
        self.running = False
        self.safe_path = os.path.join(os.path.expanduser("~"), "OrganizeFolder")
        
    def ensure_safe_path(self):
        """Ensure the safe path exists"""
        if not os.path.exists(self.safe_path):
            os.makedirs(self.safe_path, exist_ok=True)
            logger.info(f"Created safe directory: {self.safe_path}")
    
    def start_server(self):
        """Start the FastAPI server"""
        logger.info("Starting Sorting Hat server...")
        
        # Kill any existing uvicorn processes if needed
        self._kill_existing_uvicorn()
        
        try:
            # Start the server as a subprocess
            server_cmd = [sys.executable, "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
            self.server_process = subprocess.Popen(
                server_cmd,
                cwd=self.base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info(f"Server started with PID: {self.server_process.pid}")
            return True
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False
    
    def start_watcher(self):
        """Start the file watcher"""
        logger.info(f"Starting file watcher for path: {self.safe_path}")
        
        try:
            # Start the watcher as a subprocess
            watcher_cmd = [sys.executable, "watch_files.py", "--path", self.safe_path]
            self.watcher_process = subprocess.Popen(
                watcher_cmd,
                cwd=self.base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info(f"Watcher started with PID: {self.watcher_process.pid}")
            return True
        except Exception as e:
            logger.error(f"Failed to start watcher: {e}")
            return False
    
    def _kill_existing_uvicorn(self):
        """Kill any existing uvicorn processes"""
        if os.name == 'nt':  # Windows
            try:
                # Find and kill uvicorn processes
                subprocess.call("taskkill /f /im uvicorn.exe", shell=True)
            except:
                pass
        else:  # Unix-like
            try:
                # Find and kill uvicorn processes
                subprocess.call("pkill uvicorn", shell=True)
            except:
                pass
    
    def start(self):
        """Start all components of the service"""
        logger.info("Starting Sorting Hat service...")
        self.ensure_safe_path()
        
        # Start the server
        server_started = self.start_server()
        if not server_started:
            logger.error("Failed to start server component")
            return False
        
        # Wait for server to initialize
        time.sleep(5)
        
        # Start the watcher
        watcher_started = self.start_watcher()
        if not watcher_started:
            logger.error("Failed to start watcher component")
            return False
        
        self.running = True
        logger.info("Sorting Hat service successfully started")
        return True
    
    def stop(self):
        """Stop all service components"""
        logger.info("Stopping Sorting Hat service...")
        
        if self.server_process:
            logger.info(f"Terminating server process (PID: {self.server_process.pid})")
            self.server_process.terminate()
            self.server_process = None
        
        if self.watcher_process:
            logger.info(f"Terminating watcher process (PID: {self.watcher_process.pid})")
            self.watcher_process.terminate()
            self.watcher_process = None
        
        self.running = False
        logger.info("Sorting Hat service stopped")
    
    def check(self):
        """Check if processes are still running and restart if needed"""
        if not self.running:
            return
            
        # Check server process
        if self.server_process and self.server_process.poll() is not None:
            logger.warning("Server process has stopped. Restarting...")
            self.start_server()
        
        # Check watcher process
        if self.watcher_process and self.watcher_process.poll() is not None:
            logger.warning("Watcher process has stopped. Restarting...")
            self.start_watcher()

def run_service():
    """Run the service with process monitoring"""
    service = SortingHatService()
    
    # Handler for graceful shutdown
    def signal_handler(sig, frame):
        print("Shutting down Sorting Hat service...")
        service.stop()
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the service
    if not service.start():
        logger.error("Failed to start service. Exiting.")
        sys.exit(1)
    
    # Keep running and monitoring
    try:
        logger.info("Service monitoring active. Press Ctrl+C to stop.")
        while True:
            service.check()
            time.sleep(30)  # Check every 30 seconds
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down...")
        service.stop()
        
if __name__ == "__main__":
    run_service()
