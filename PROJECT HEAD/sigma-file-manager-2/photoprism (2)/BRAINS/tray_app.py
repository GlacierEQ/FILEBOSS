#!/usr/bin/env python
"""
System Tray Application for Sorting Hat

This script provides a system tray icon and menu for controlling the Sorting Hat system.
It allows easy access to start, stop, and configure the service.
"""
import os
import sys
import time
import subprocess
import threading
import webbrowser
from pathlib import Path

try:
    import pystray
    from PIL import Image, ImageDraw
    import psutil
except ImportError:
    # Install required packages
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pystray", "Pillow", "psutil"])
    import pystray
    from PIL import Image, ImageDraw
    import psutil

from watchdog_monitor import SortingHatWatchdog

class SortingHatTray:
    """System tray application for Sorting Hat"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.icon = None
        self.watchdog = SortingHatWatchdog()
        self.system_active = False
        self.safe_path = os.path.join(os.path.expanduser("~"), "OrganizeFolder")
        
    def create_icon(self):
        """Create the system tray icon"""
        # Create a simple icon with a hat silhouette
        width = 64
        height = 64
        color1 = (52, 152, 219)  # Blue
        color2 = (46, 204, 113)  # Green
        
        image = Image.new('RGB', (width, height), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        
        # Draw a hat shape
        dc.rectangle((5, 40, width-5, 50), fill=color1)  # Hat brim
        dc.ellipse((15, 15, width-15, 45), fill=color2)  # Hat top
        
        return image
        
    def start_system(self):
        """Start the Sorting Hat system"""
        if not self.system_active:
            self.watchdog.start()
            self.system_active = True
            self.update_menu()
            return True
        return False
        
    def stop_system(self):
        """Stop the Sorting Hat system"""
        if self.system_active:
            self.watchdog.stop()
            self.system_active = False
            self.update_menu()
            return True
        return False
        
    def open_dashboard(self):
        """Open the web dashboard"""
        # Try different dashboard options
        dashboard_paths = [
            os.path.join(self.base_dir, 'spaceship_dashboard.html'),
            os.path.join(self.base_dir, 'dashboard.html'),
            os.path.join(self.base_dir, 'status_report.html')
        ]
        
        for path in dashboard_paths:
            if os.path.exists(path):
                webbrowser.open(f"file://{path}")
                return True
                
        # If no dashboard file exists, open API docs
        webbrowser.open("http://localhost:8000/docs")
        return True
        
    def open_folder(self):
        """Open the safe folder"""
        # Create the folder if it doesn't exist
        os.makedirs(self.safe_path, exist_ok=True)
        
        # Open folder in file explorer
        if os.name == 'nt':  # Windows
            os.startfile(self.safe_path)
        elif os.name == 'posix':  # macOS or Linux
            if sys.platform == 'darwin':  # macOS
                subprocess.call(['open', self.safe_path])
            else:  # Linux
                subprocess.call(['xdg-open', self.safe_path])
                
    def run_troubleshooter(self):
        """Run the troubleshooter script"""
        troubleshooter_path = os.path.join(self.base_dir, 'troubleshoot.py')
        if os.path.exists(troubleshooter_path):
            subprocess.Popen([sys.executable, troubleshooter_path])
        else:
            print("Troubleshooter script not found")
            
    def toggle_autostart(self):
        """Toggle autostart setting"""
        autostart_script = os.path.join(self.base_dir, 'add_to_startup.py')
        if os.path.exists(autostart_script):
            if self.is_autostart_enabled():
                # Disable autostart
                subprocess.run([sys.executable, autostart_script, 'remove'])
            else:
                # Enable autostart
                subprocess.run([sys.executable, autostart_script])
            # Update menu after toggle
            self.update_menu()
            
    def is_autostart_enabled(self):
        """Check if autostart is enabled"""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, "SortingHat")
                return True
            except:
                return False
        except ImportError:
            # Not on Windows or winreg not available
            return False
            
    def exit_app(self, icon):
        """Clean exit from the application"""
        if self.system_active:
            self.stop_system()
        icon.stop()
        
    def get_menu_items(self):
        """Generate menu items based on current state"""
        is_running = self.system_active
        autostart_enabled = self.is_autostart_enabled()
        
        return [
            pystray.MenuItem(f"{'Stop' if is_running else 'Start'} Sorting Hat", 
                            self.stop_system if is_running else self.start_system),
            pystray.MenuItem("Open Dashboard", self.open_dashboard),
            pystray.MenuItem("Open Organized Folder", self.open_folder),
            pystray.MenuItem("Run Troubleshooter", self.run_troubleshooter),
            pystray.MenuItem(f"{'Disable' if autostart_enabled else 'Enable'} Auto-Start", 
                            self.toggle_autostart),
            pystray.MenuItem("Exit", self.exit_app)
        ]
        
    def update_menu(self):
        """Update the system tray menu"""
        if self.icon:
            self.icon.menu = pystray.Menu(*self.get_menu_items())
            
    def run(self):
        """Run the system tray application"""
        # Create the icon
        self.icon = pystray.Icon("sorting_hat", self.create_icon(), "Sorting Hat")
        self.icon.menu = pystray.Menu(*self.get_menu_items())
        
        # Start the system by default
        self.start_system()
        
        # Run the icon
        self.icon.run()

if __name__ == "__main__":
    tray_app = SortingHatTray()
    tray_app.run()
