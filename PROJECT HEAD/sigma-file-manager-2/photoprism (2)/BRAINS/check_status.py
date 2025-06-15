import os
import sys
import time
import json
import subprocess
import platform
import requests
import psutil
import logging
from tabulate import tabulate
from colorama import Fore, Style, init
from pathlib import Path

# Initialize colorama
init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("status_checker")

class SortingHatStatus:
    """Monitor and report status of Sorting Hat components"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_file = os.path.join(self.base_dir, 'sorting_service.log')
        self.safe_path = os.path.join(os.path.expanduser("~"), "OrganizeFolder")
        self.api_endpoint = "http://localhost:8000"
    
    def check_service_status(self):
        """Check if the Windows service is installed and running"""
        if platform.system() != 'Windows':
            return None
            
        try:
            # Check if service is installed
            service_check = subprocess.run(
                ['sc', 'query', 'SortingHatService'],
                capture_output=True,
                text=True
            )
            
            if 'RUNNING' in service_check.stdout:
                return True, "RUNNING"
            elif 'STOPPED' in service_check.stdout:
                return True, "STOPPED"
            else:
                return False, "NOT INSTALLED"
        except Exception as e:
            logger.error(f"Error checking service: {e}")
            return None, str(e)
    
    def check_startup_registry(self):
        """Check if the application is in Windows startup registry"""
        if platform.system() != 'Windows':
            return None
            
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, winreg.KEY_READ)
            try:
                value, _ = winreg.QueryValueEx(key, "SortingHat")
                winreg.CloseKey(key)
                return True
            except WindowsError:
                winreg.CloseKey(key)
                return False
        except Exception as e:
            logger.error(f"Error checking registry: {e}")
            return None
    
    def check_processes(self):
        """Check if server and watcher processes are running"""
        server_running = False
        watcher_running = False
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline:
                    cmdline_str = ' '.join(cmdline)
                    if "uvicorn server:app" in cmdline_str:
                        server_running = True
                    elif "watch_files.py" in cmdline_str:
                        watcher_running = True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        return server_running, watcher_running
    
    def check_server_response(self):
        """Check if the API server is responding"""
        try:
            response = requests.get(f"{self.api_endpoint}/help", timeout=5)
            if response.status_code == 200:
                return True, response.elapsed.total_seconds()
            else:
                return False, response.status_code
        except requests.RequestException as e:
            return False, str(e)
    
    def get_log_tail(self, lines=10):
        """Get the last few lines from the log file"""
        if not os.path.exists(self.log_file):
            return []
            
        with open(self.log_file, 'r') as f:
            return list(f.readlines())[-lines:]
    
    def get_safe_path_status(self):
        """Check if the safe path exists and is accessible"""
        if os.path.exists(self.safe_path):
            writable = os.access(self.safe_path, os.W_OK)
            file_count = len([f for f in os.listdir(self.safe_path) if os.path.isfile(os.path.join(self.safe_path, f))])
            return True, writable, file_count
        else:
            return False, False, 0
    
    def check_evolution_system(self):
        """Check if evolution system is enabled and working"""
        try:
            response = requests.get(f"{self.api_endpoint}/evolution/report", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and data['message'] == 'Evolution system not available':
                    return False, "Not installed"
                return True, data.get('metrics', {})
            else:
                return False, f"Error: {response.status_code}"
        except requests.RequestException:
            return False, "Server not responding"
    
    def display_status(self):
        """Display full system status"""
        print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   SORTING HAT SYSTEM STATUS CHECK   {Style.RESET_ALL}")
        print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")
        print()
        
        # Check service status
        service_installed, service_status = self.check_service_status()
        if service_installed is not None:  # Windows only
            status_color = Fore.GREEN if service_installed and service_status == "RUNNING" else Fore.RED
            print(f"Windows Service: {status_color}{service_status}{Style.RESET_ALL}")
        
        # Check startup registry
        startup_registered = self.check_startup_registry()
        if startup_registered is not None:  # Windows only
            status_color = Fore.GREEN if startup_registered else Fore.RED
            print(f"Startup Registry: {status_color}{'REGISTERED' if startup_registered else 'NOT REGISTERED'}{Style.RESET_ALL}")
        
        # Check processes
        server_running, watcher_running = self.check_processes()
        print(f"Server Process: {Fore.GREEN if server_running else Fore.RED}{'RUNNING' if server_running else 'STOPPED'}{Style.RESET_ALL}")
        print(f"Watcher Process: {Fore.GREEN if watcher_running else Fore.RED}{'RUNNING' if watcher_running else 'STOPPED'}{Style.RESET_ALL}")
        
        # Check API response
        api_responding, response_details = self.check_server_response()
        status_color = Fore.GREEN if api_responding else Fore.RED
        status_text = f"{response_details:.3f}s" if api_responding else response_details
        print(f"API Response: {status_color}{'OK' if api_responding else 'FAILED'} ({status_text}){Style.RESET_ALL}")
        
        # Check safe path
        safe_exists, safe_writable, file_count = self.get_safe_path_status()
        status_color = Fore.GREEN if safe_exists and safe_writable else Fore.RED
        print(f"Safe Path: {status_color}{self.safe_path}{Style.RESET_ALL}")
        print(f"  - Exists: {Fore.GREEN if safe_exists else Fore.RED}{safe_exists}{Style.RESET_ALL}")
        print(f"  - Writable: {Fore.GREEN if safe_writable else Fore.RED}{safe_writable}{Style.RESET_ALL}")
        print(f"  - Files: {file_count}")
        
        # Check evolution system
        evolution_active, evolution_details = self.check_evolution_system()
        status_color = Fore.GREEN if evolution_active else Fore.YELLOW
        print(f"Evolution System: {status_color}{'ACTIVE' if evolution_active else 'INACTIVE'}{Style.RESET_ALL}")
        if evolution_active and isinstance(evolution_details, dict):
            print("  - Metrics:")
            for key, value in evolution_details.items():
                if isinstance(value, float):
                    print(f"    - {key}: {value:.2f}")
                else:
                    print(f"    - {key}: {value}")
        
        # Show recent logs
        print("\nRecent Logs:")
        log_entries = self.get_log_tail(5)
        if log_entries:
            for entry in log_entries:
                print(f"  {entry.strip()}")
        else:
            print(f"  {Fore.YELLOW}No log entries found{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}======================================{Style.RESET_ALL}")
        
        # Overall system status
        system_ok = (
            (service_installed is None or (service_installed and service_status == "RUNNING")) and
            server_running and 
            watcher_running and 
            api_responding and
            safe_exists and
            safe_writable
        )
        
        status_color = Fore.GREEN if system_ok else Fore.RED
        print(f"Overall System Status: {status_color}{'HEALTHY' if system_ok else 'ISSUES DETECTED'}{Style.RESET_ALL}")
        
        if not system_ok:
            print("\nTroubleshooting Steps:")
            if not server_running:
                print(f"  {Fore.YELLOW}- Server not running. Try: python service_manager.py{Style.RESET_ALL}")
            if not watcher_running:
                print(f"  {Fore.YELLOW}- Watcher not running. Check logs for errors.{Style.RESET_ALL}")
            if not api_responding:
                print(f"  {Fore.YELLOW}- API not responding. Check if port 8000 is available.{Style.RESET_ALL}")
            if not safe_exists:
                print(f"  {Fore.YELLOW}- Safe path doesn't exist. It will be created automatically.{Style.RESET_ALL}")
            if not safe_writable:
                print(f"  {Fore.YELLOW}- Safe path not writable. Check permissions.{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")
    
    def generate_status_json(self):
        """Generate status information in JSON format"""
        service_installed, service_status = self.check_service_status()
        server_running, watcher_running = self.check_processes()
        api_responding, response_details = self.check_server_response()
        safe_exists, safe_writable, file_count = self.get_safe_path_status()
        evolution_active, evolution_details = self.check_evolution_system()
        startup_registered = self.check_startup_registry()
        
        system_ok = (
            (service_installed is None or (service_installed and service_status == "RUNNING")) and
            server_running and 
            watcher_running and 
            api_responding and
            safe_exists and
            safe_writable
        )
        
        return {
            "timestamp": time.time(),
            "system_healthy": system_ok,
            "windows_service": {
                "installed": service_installed,
                "status": service_status
            } if service_installed is not None else None,
            "startup_registered": startup_registered,
            "processes": {
                "server": server_running,
                "watcher": watcher_running
            },
            "api": {
                "responding": api_responding,
                "details": response_details if isinstance(response_details, (int, float)) else str(response_details)
            },
            "safe_path": {
                "path": self.safe_path,
                "exists": safe_exists,
                "writable": safe_writable,
                "file_count": file_count
            },
            "evolution_system": {
                "active": evolution_active,
                "details": evolution_details
            }
        }

def main():
    try:
        import psutil
    except ImportError:
        print("Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil", "requests", "colorama", "tabulate"])
        print("Packages installed successfully!")
        # Restart script to use newly installed packages
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    status = SortingHatStatus()
    
    # Check for command-line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--json':
            print(json.dumps(status.generate_status_json(), indent=2))
        elif sys.argv[1] == '--web':
            # Generate a simple HTML status report
            status_data = status.generate_status_json()
            html_path = os.path.join(status.base_dir, 'status_report.html')
            
            with open(html_path, 'w') as f:
                f.write(f"""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Sorting Hat Status Report</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; }}
                        .healthy {{ color: green; }}
                        .unhealthy {{ color: red; }}
                        .warning {{ color: orange; }}
                        .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 15px; }}
                        h2 {{ margin-top: 0; }}
                    </style>
                </head>
                <body>
                    <h1>Sorting Hat Status Report</h1>
                    <div class="card">
                        <h2>Overall Status: <span class="{'healthy' if status_data['system_healthy'] else 'unhealthy'}">
                            {'HEALTHY' if status_data['system_healthy'] else 'ISSUES DETECTED'}</span>
                        </h2>
                        <p>Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                    
                    <div class="card">
                        <h2>Services</h2>
                        <p>Server Process: <span class="{'healthy' if status_data['processes']['server'] else 'unhealthy'}">
                            {'RUNNING' if status_data['processes']['server'] else 'STOPPED'}</span>
                        </p>
                        <p>Watcher Process: <span class="{'healthy' if status_data['processes']['watcher'] else 'unhealthy'}">
                            {'RUNNING' if status_data['processes']['watcher'] else 'STOPPED'}</span>
                        </p>
                        <p>API Response: <span class="{'healthy' if status_data['api']['responding'] else 'unhealthy'}">
                            {'OK' if status_data['api']['responding'] else 'FAILED'} ({status_data['api']['details']})</span>
                        </p>
                    </div>
                    
                    <div class="card">
                        <h2>File Storage</h2>
                        <p>Safe Path: {status_data['safe_path']['path']}</p>
                        <p>Path Exists: <span class="{'healthy' if status_data['safe_path']['exists'] else 'unhealthy'}">
                            {status_data['safe_path']['exists']}</span>
                        </p>
                        <p>Path Writable: <span class="{'healthy' if status_data['safe_path']['writable'] else 'unhealthy'}">
                            {status_data['safe_path']['writable']}</span>
                        </p>
                        <p>Files in Directory: {status_data['safe_path']['file_count']}</p>
                    </div>
                    
                    <div class="card">
                        <h2>Evolution System</h2>
                        <p>Status: <span class="{'healthy' if status_data['evolution_system']['active'] else 'warning'}">
                            {'ACTIVE' if status_data['evolution_system']['active'] else 'INACTIVE'}</span>
                        </p>
                    </div>
                    
                    <script>
                        // Auto-refresh every 30 seconds
                        setTimeout(function() {{ 
                            location.reload();
                        }}, 30000);
                    </script>
                </body>
                </html>
                """)
            
            print(f"Status report saved to {html_path}")
            # Try to open the HTML file in the default browser
            try:
                import webbrowser
                webbrowser.open('file://' + html_path)
            except:
                pass
    else:
        # Display formatted status to console
        status.display_status()

if __name__ == "__main__":
    main()
