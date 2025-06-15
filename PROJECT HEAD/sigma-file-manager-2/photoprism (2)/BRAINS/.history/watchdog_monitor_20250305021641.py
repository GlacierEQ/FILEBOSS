#!/usr/bin/env python
"""
Watchdog Monitor for Sorting Hat

This script monitors the Sorting Hat services and automatically restarts them if they fail.
It also performs periodic health checks and self-healing operations.
"""
import os
import sys
import time
import logging
import subprocess
import signal
import json
import socket
import psutil
from pathlib import Path
import threading
from check_status import SortingHatStatus

# Configure logging
logging.basicConfig(
    filename=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'watchdog.log'),
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)

class SortingHatWatchdog:
    """Watchdog monitor for Sorting Hat that ensures continuous operation"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.server_process = None
        self.watcher_process = None
        self.running = False
        self.safe_path = os.path.join(os.path.expanduser("~"), "OrganizeFolder")
        self.check_interval = 30  # Seconds between health checks
        self.consecutive_failures = 0
        self.max_failures = 5
    
    def ensure_paths_exist(self):
        """Ensure required directories exist"""
        paths = [
            self.safe_path,
            os.path.join(self.base_dir, 'data'),
            os.path.join(self.base_dir, 'logs')
        ]
        
        for path in paths:
            if not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                    logging.info(f"Created directory: {path}")
                except Exception as e:
                    logging.error(f"Failed to create directory {path}: {e}")
                    
    def is_port_in_use(self, port):
        """Check if a port is in use"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
            
    def is_process_running_by_pid(self, pid):
        """Check if a process with given PID is running"""
        if pid is None:
            return False
        try:
            process = psutil.Process(pid)
            return process.is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def is_server_running(self):
        """Check if the server process is running"""
        # First check PID if we have it
        if self.server_process and self.is_process_running_by_pid(self.server_process.pid):
            return True
            
        # Then check if port 8000 is in use
        return self.is_port_in_use(8000)
        
    def is_watcher_running(self):
        """Check if the file watcher process is running"""
        if self.watcher_process and self.is_process_running_by_pid(self.watcher_process.pid):
            return True
            
        # Check for running watcher by looking for watch_files.py in process list
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and 'watch_files.py' in ' '.join(cmdline):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    
    def start_services(self):
        """Start both server and watcher services"""
        logging.info("Starting Sorting Hat services")
        
        # First, check if they're already running
        server_running = self.is_server_running()
        watcher_running = self.is_watcher_running()
        
        if server_running and watcher_running:
            logging.info("All services already running")
            return True
            
        # Start the service manager if it exists
        service_manager = os.path.join(self.base_dir, 'service_manager.py')
        if os.path.exists(service_manager):
            try:
                logging.info("Starting services via service_manager.py")
                self.server_process = subprocess.Popen(
                    [sys.executable, service_manager],
                    cwd=self.base_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                time.sleep(5)  # Wait for startup
                return self.is_server_running() and self.is_watcher_running()
            except Exception as e:
                logging.error(f"Failed to start service_manager.py: {e}")
                # Fall through to individual service startup
        
        # Start services individually if service_manager isn't available or failed
        success = True
        
        # Start server if needed
        if not server_running:
            try:
                logging.info("Starting server individually")
                server_cmd = [sys.executable, '-m', 'uvicorn', 'server:app', '--host', '0.0.0.0', '--port', '8000']
                self.server_process = subprocess.Popen(
                    server_cmd,
                    cwd=self.base_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                time.sleep(3)  # Wait for server to start
                if not self.is_server_running():
                    logging.error("Server failed to start")
                    success = False
            except Exception as e:
                logging.error(f"Error starting server: {e}")
                success = False
        
        # Start watcher if needed
        if not watcher_running:
            try:
                logging.info("Starting file watcher individually")
                watch_cmd = [sys.executable, 'watch_files.py', '--path', self.safe_path]
                self.watcher_process = subprocess.Popen(
                    watch_cmd,
                    cwd=self.base_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                time.sleep(2)  # Wait for watcher to start
                if not self.is_watcher_running():
                    logging.error("File watcher failed to start")
                    success = False
            except Exception as e:
                logging.error(f"Error starting file watcher: {e}")
                success = False
                
        return success
        
    def stop_services(self):
        """Stop all running services"""
        logging.info("Stopping services")
        
        # Stop using service_manager if available
        service_manager = os.path.join(self.base_dir, 'service_manager.py')
        if os.path.exists(service_manager):
            try:
                subprocess.run([sys.executable, service_manager, '--stop'], timeout=10)
                time.sleep(2)
                if not (self.is_server_running() or self.is_watcher_running()):
                    return True
            except Exception as e:
                logging.error(f"Failed to stop services via service_manager: {e}")
        
        # Kill processes individually if needed
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except Exception:
                # Force kill if termination doesn't work
                try:
                    self.server_process.kill()
                except:
                    pass
            self.server_process = None
                
        if self.watcher_process:
            try:
                self.watcher_process.terminate()
                self.watcher_process.wait(timeout=5)
            except Exception:
                # Force kill if termination doesn't work
                try:
                    self.watcher_process.kill()
                except:
                    pass
            self.watcher_process = None
            
        # Force kill any remaining processes by name
        try:
            # Kill uvicorn
            if os.name == 'nt':  # Windows
                os.system("taskkill /f /im uvicorn.exe 2>NUL")
            else:  # Unix/Linux
                os.system("pkill -f uvicorn")
                
            # Small delay to allow process termination
            time.sleep(1)
        except:
            pass
            
        return not (self.is_server_running() or self.is_watcher_running())
    
    def health_check(self):
        """Perform health check on the system"""
        logging.info("Performing health check")
        
        # Check API server
        api_healthy = self.is_server_running()
        
        # Check file watcher
        watcher_healthy = self.is_watcher_running()
        
        # Check database access
        db_path = os.path.join(self.base_dir, 'data', 'evolution.db')
        db_healthy = os.path.exists(db_path) and os.access(db_path, os.R_OK | os.W_OK)
        
        # Check safe path
        safe_path_healthy = os.path.exists(self.safe_path) and os.access(self.safe_path, os.R_OK | os.W_OK)
        
        # Overall health assessment
        system_healthy = api_healthy and watcher_healthy and db_healthy and safe_path_healthy
        
        health_status = {
            "timestamp": time.time(),
            "system_healthy": system_healthy,
            "api_server": api_healthy,
            "file_watcher": watcher_healthy,
            "database": db_healthy,
            "safe_path": safe_path_healthy
        }
        
        # Log health status
        log_level = logging.INFO if system_healthy else logging.ERROR
        logging.log(log_level, f"Health check: {json.dumps(health_status)}")
        
        # Save current health status to file for dashboard access
        try:
            status_file = os.path.join(self.base_dir, 'data', 'watchdog_status.json')
            with open(status_file, 'w') as f:
                json.dump(health_status, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save health status: {e}")
            
        return system_healthy
        
    def self_heal(self):
        """Attempt to fix issues detected during health check"""
        logging.warning("Self-healing initiated")
        
        # Increment failure counter
        self.consecutive_failures += 1
        
        # If we've had too many failures, do a full restart
        if self.consecutive_failures >= self.max_failures:
            logging.warning(f"Max failures ({self.max_failures}) reached, performing full restart")
            self.stop_services()
            time.sleep(2)
            # Create missing directories
            self.ensure_paths_exist()
            # Reinitialize database if needed
            self.reinitialize_database()
            # Restart services
            return self.start_services()
        else:
            # Just restart services for now
            logging.info(f"Consecutive failures: {self.consecutive_failures}/{self.max_failures}")
            self.stop_services()
            time.sleep(1)
            return self.start_services()
    
    def reinitialize_database(self):
        """Reinitialize the evolution database if needed"""
        db_path = os.path.join(self.base_dir, 'data', 'evolution.db')
        init_script = os.path.join(self.base_dir, 'initialize_evolution.py')
        
        if not os.path.exists(db_path) and os.path.exists(init_script):
            logging.info("Reinitializing evolution database")
            try:
                subprocess.run([sys.executable, init_script], check=True)
                return True
            except Exception as e:
                logging.error(f"Failed to reinitialize database: {e}")
                return False
        return True
    
    def run(self):
        """Main watchdog loop"""
        self.running = True
        logging.info("Watchdog monitor starting")
        
        # Initial setup
        self.ensure_paths_exist()
        
        # Initial service start
        if not self.start_services():
            logging.error("Failed to start services during initialization")
            self.self_heal()
            
        # Monitoring loop
        try:
            while self.running:
                # Perform health check
                if self.health_check():
                    # Reset failure counter on success
                    self.consecutive_failures = 0
                else:
                    # Try to heal the system
                    self.self_heal()
                
                # Wait for next check interval
                for _ in range(self.check_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            logging.info("Watchdog received interrupt signal")
            self.running = False
        finally:
            logging.info("Watchdog shutting down")
            self.stop_services()
            
    def start(self):
        """Start the watchdog in a separate thread"""
        self.watchdog_thread = threading.Thread(target=self.run)
        self.watchdog_thread.daemon = True
        self.watchdog_thread.start()
        return self.watchdog_thread
        
    def stop(self):
        """Stop the watchdog"""
        self.running = False
        if hasattr(self, 'watchdog_thread') and self.watchdog_thread.is_alive():
            self.watchdog_thread.join(timeout=10)
        self.stop_services()

def run_as_service():
    """Run the watchdog as a standalone process"""
    watchdog = SortingHatWatchdog()
    
    def signal_handler(sig, frame):
        print("Shutting down watchdog monitor...")
        watchdog.stop()
        sys.exit(0)
        
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start monitoring
    watchdog.run()

if __name__ == "__main__":
    run_as_service()
