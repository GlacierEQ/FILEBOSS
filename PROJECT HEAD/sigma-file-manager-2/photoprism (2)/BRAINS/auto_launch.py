#!/usr/bin/env python
"""
Auto-Launch Script for Sorting Hat

This script determines the best way to launch the Sorting Hat system
based on the environment and available components.
"""
import os
import sys
import subprocess
import time
import argparse
import platform

def is_admin():
    """Check if the script is running with administrator privileges"""
    try:
        if os.name == 'nt':
            # Windows
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            # Unix/Linux/MacOS
            return os.geteuid() == 0
    except:
        return False

def create_shortcut(target_path, shortcut_path, args="", icon=None, description=None):
    """Create a Windows shortcut (.lnk) file"""
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = target_path
        if args:
            shortcut.Arguments = args
        if icon:
            shortcut.IconLocation = icon
        if description:
            shortcut.Description = description
        shortcut.WindowStyle = 1  # Normal window
        shortcut.save()
        return True
    except Exception as e:
        print(f"Error creating shortcut: {e}")
        return False

def get_python_path():
    """Get the path to the current Python interpreter"""
    return sys.executable

def install_as_windows_service():
    """Install Sorting Hat as a Windows service"""
    # Check if pywin32 is installed
    try:
        import win32serviceutil
        import win32service
    except ImportError:
        try:
            subprocess.check_call([get_python_path(), "-m", "pip", "install", "pywin32"])
            print("Installed pywin32 successfully")
        except:
            print("Failed to install pywin32. Windows service installation skipped.")
            return False
    
    # Check if the service install script exists
    base_dir = os.path.dirname(os.path.abspath(__file__))
    service_script = os.path.join(base_dir, "install_windows_service.py")
    
    if os.path.exists(service_script):
        try:
            result = subprocess.call([get_python_path(), service_script, "install"])
            if result == 0:
                print("Windows service installed successfully")
                # Try to start the service
                subprocess.call([get_python_path(), service_script, "start"])
                return True
            else:
                print(f"Windows service installation returned error code: {result}")
                return False
        except Exception as e:
            print(f"Error installing Windows service: {e}")
            return False
    else:
        print(f"Windows service installation script not found: {service_script}")
        return False

def ensure_dependencies():
    """Ensure all dependencies are installed"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dependency_script = os.path.join(base_dir, "install_dependencies.py")
    
    if os.path.exists(dependency_script):
        try:
            subprocess.check_call([get_python_path(), dependency_script])
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error installing dependencies: {e}")
            return False
    else:
        # Install basic dependencies directly
        try:
            packages = ["fastapi", "uvicorn", "watchdog", "psutil", "requests", "colorama", 
                       "nest-asyncio", "python-dotenv", "pystray", "Pillow"]
            subprocess.check_call([get_python_path(), "-m", "pip", "install"] + packages)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error installing basic dependencies: {e}")
            return False

def initialize_system():
    """Initialize the Sorting Hat system"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    init_script = os.path.join(base_dir, "initialize_evolution.py")
    
    if os.path.exists(init_script):
        try:
            subprocess.check_call([get_python_path(), init_script])
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error initializing system: {e}")
            return False
    else:
        # Create basic directories
        safe_path = os.path.join(os.path.expanduser("~"), "OrganizeFolder")
        data_dir = os.path.join(base_dir, "data")
        try:
            os.makedirs(safe_path, exist_ok=True)
            os.makedirs(data_dir, exist_ok=True)
            print(f"Created basic directories: {safe_path}, {data_dir}")
            return True
        except Exception as e:
            print(f"Error creating directories: {e}")
            return False

def launch_system():
    """Launch the Sorting Hat system using the best available method"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check for tray app first
    tray_app = os.path.join(base_dir, "tray_app.py")
    if os.path.exists(tray_app):
        try:
            if platform.system() == 'Windows':
                # Use pythonw on Windows to hide console window
                pythonw = get_python_path().replace('python.exe', 'pythonw.exe')
                if not os.path.exists(pythonw):
                    pythonw = get_python_path()
                subprocess.Popen([pythonw, tray_app], creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                # Use normal python on other platforms
                subprocess.Popen([get_python_path(), tray_app])
            print("Launched system tray application")
            return True
        except Exception as e:
            print(f"Error launching tray app: {e}")
            # Fall through to other methods
    
    # Try watchdog monitor
    watchdog_script = os.path.join(base_dir, "watchdog_monitor.py")
    if os.path.exists(watchdog_script):
        try:
            if platform.system() == 'Windows':
                # Use pythonw to hide console
                pythonw = get_python_path().replace('python.exe', 'pythonw.exe')
                if not os.path.exists(pythonw):
                    pythonw = get_python_path()
                subprocess.Popen([pythonw, watchdog_script], creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen([get_python_path(), watchdog_script])
            print("Launched watchdog monitor")
            return True
        except Exception as e:
            print(f"Error launching watchdog: {e}")
            # Fall through to other methods
    
    # Try quick start
    quick_start = os.path.join(base_dir, "quick_start.py")
    if os.path.exists(quick_start):
        try:
            if platform.system() == 'Windows':
                subprocess.Popen([get_python_path(), quick_start], creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen([get_python_path(), quick_start])
            print("Launched quick start script")
            return True
        except Exception as e:
            print(f"Error launching quick start: {e}")
            # Fall through to other methods
    
    # Try service manager directly
    service_manager = os.path.join(base_dir, "service_manager.py")
    if os.path.exists(service_manager):
        try:
            if platform.system() == 'Windows':
                subprocess.Popen([get_python_path(), service_manager], creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen([get_python_path(), service_manager])
            print("Launched service manager")
            return True
        except Exception as e:
            print(f"Error launching service manager: {e}")
            # Fall through to other methods
    
    # Last resort: try starting the server directly
    server_file = os.path.join(base_dir, "server.py")
    if os.path.exists(server_file):
        try:
            if platform.system() == 'Windows':
                subprocess.Popen([get_python_path(), "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"],
                              cw