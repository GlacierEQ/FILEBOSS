#!/usr/bin/env python
"""
System Tray Application with Natural Language Support

This script extends the system tray application to support natural language file organization.
"""
import os
import sys
import subprocess
import threading
import asyncio
from typing import Dict, Any, Optional

# Set up path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    # Install dependencies
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pystray", "pillow"])
    import pystray
    from PIL import Image, ImageDraw

# Import local modules if available
try:
    from integration.nl_bridge import process_instruction
    from natural_language_organizer import NaturalLanguageOrganizer
except ImportError:
    # Define fallback if modules are not available
    async def process_instruction(instruction, path=None, metadata=None):
        return {"success": False, "message": "Natural language module not available", "files_moved": 0}
    
    class NaturalLanguageOrganizer:
        async def organize(self, instruction, path=None):
            return await process_instruction(instruction, path)

class SystemTrayApp:
    """System tray application for Sorting Hat with NL support"""
    
    def __init__(self):
        """Initialize the system tray app"""
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.icon = None
        self.nl_organizer = NaturalLanguageOrganizer()
        self.running = False
        
    def create_image(self):
        """Create the system tray icon image"""
        width = 64
        height = 64
        color1 = (52, 152, 219)  # Blue
        color2 = (46, 204, 113)  # Green
        
        image = Image.new('RGB', (width, height), (255, 255, 255, 0))
        dc = ImageDraw.Draw(image)
        
        # Draw a hat shape
        dc.rectangle((5, 40, width-5, 50), fill=color1)  # Hat brim
        dc.ellipse((15, 15, width-15, 45), fill=color2)  # Hat top
        
        return image
    
    def run(self):
        """Run the system tray application"""
        self.running = True
        
        # Create the icon
        self.icon = pystray.Icon(
            "sorting_hat",
            self.create_image(),
            "Sorting Hat",
            menu=self.create_menu()
        )
        
        # Run the icon
        self.icon.run()
    
    def create_menu(self):
        """Create the system tray menu"""
        return pystray.Menu(
            pystray.MenuItem("Organize Files...", self.show_nl_dialog),
            pystray.MenuItem("Open Dashboard", self.open_dashboard),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open Safe Folder", self.open_safe_folder),
            pystray.MenuItem("Check Status", self.check_status),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.exit_app)
        )
    
    def show_nl_dialog(self, icon, item):
        """Show dialog for natural language organization"""
        # On Windows, use a native dialog with tkinter
        if sys.platform == 'win32':
            self.show_tk_dialog()
        else:
            # On other platforms, launch the GUI application
            subprocess.Popen([sys.executable, os.path.join(self.base_dir, "nl_gui.py")])
    
    def show_tk_dialog(self):
        """Show a Tkinter dialog for natural language input"""
        import tkinter as tk
        from tkinter import simpledialog, messagebox, filedialog
        
        # Create root window but don't show it
        root = tk.Tk()
        root.withdraw()
        
        # Show input dialog
        instruction = simpledialog.askstring(
            "Natural Language Organizer",
            "Enter your organization instruction:",
            parent=root
        )
        
        if instruction:
            # Ask for path (optional)
            use_custom_path = messagebox.askyesno(
                "Select Path",
                "Do you want to specify a custom path?\n"
                "(Default is the safe folder)"
            )
            
            path = None
            if use_custom_path:
                path = filedialog.askdirectory(
                    title="Select folder to organize",
                    parent=root
                )
                
                # User cancelled path selection
                if not path:
                    root.destroy()
                    return
            
            # Show processing indicator
            processing_window = tk.Toplevel(root)
            processing_window.title("Processing")
            processing_window.geometry("300x100")
            processing_window.resizable(False, False)
            processing_window.transient(root)
            
            # Center window
            processing_window.update_idletasks()
            width = processing_window.winfo_width()
            height = processing_window.winfo_height()
            x = (processing_window.winfo_screenwidth() // 2) - (width // 2)
            y = (processing_window.winfo_screenheight() // 2) - (height // 2)
            processing_window.geometry(f'{width}x{height}+{x}+{y}')
            
            # Add progress indicator
            tk.Label(
                processing_window, 
                text="Organizing files...",
                font=("Arial", 12)
            ).pack(pady=10)
            
            progress = tk.ttk.Progressbar(
                processing_window, 
                mode="indeterminate",
                length=250
            )
            progress.pack(pady=10, padx=20)
            progress.start(10)
            
            # Process instruction in background
            def process_in_background():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    self.nl_organizer.organize(instruction, path)
                )
                # Show result on UI thread
                root.after(0, lambda: self.show_result(result, root, processing_window))
            
            # Start background processing
            threading.Thread(target=process_in_background).start()
            
            # Keep UI responsive
            root.mainloop()
    
    def show_result(self, result, root, processing_window):
        """Show the organization result"""
        from tkinter import messagebox
        
        # Close the processing window
        processing_window.destroy()
        
        # Show result message
        if result.get("success", False):
            messagebox.showinfo(
                "Organization Complete",
                f"{result['message']}\n\n"
                f"Files moved: {result['files_moved']}\n"
                f"Time taken: {result.get('execution_time', 0):.2f}s"
            )
        else:
            messagebox.showerror(
                "Organization Failed",
                f"Error: {result['message']}"
            )
        
        # Clean up
        root.destroy()
    
    def open_dashboard(self, icon=None, item=None):
        """Open the web dashboard"""
        # Check for dashboard files in order of preference
        dashboard_files = [
            "spaceship_dashboard.html",
            "dashboard.html",
            "status_report.html"
        ]
        
        for filename in dashboard_files:
            path = os.path.join(self.base_dir, filename)
            if os.path.exists(path):
                self._open_file(path)
                return
                
        # If no dashboard found, launch the status check
        subprocess.Popen(
            [sys.executable, os.path.join(self.base_dir, "check_status.py"), "--web"]
        )
    
    def open_safe_folder(self, icon=None, item=None):
        """Open the safe folder"""
        # Try to import SafePaths
        try:
            from safe_paths import SafePaths
            safe_path = SafePaths.DEFAULT_SAFE_PATH
        except ImportError:
            # Fallback
            safe_path = os.path.join(os.path.expanduser("~"), "OrganizeFolder")
            
        # Create if it doesn't exist
        os.makedirs(safe_path, exist_ok=True)
        
        # Open the folder
        self._open_file(safe_path)
    
    def check_status(self, icon=None, item=None):
        """Check system status"""
        subprocess.Popen([sys.executable, os.path.join(self.base_dir, "check_status.py")])
    
    def exit_app(self, icon, item=None):
        """Exit the application"""
        icon.stop()
        self.running = False
    
    def _open_file(self, path):
        """Open a file with the default application"""
        if sys.platform == 'win32':
            os.startfile(path)
        elif sys.platform == 'darwin':  # macOS
            subprocess.call(['open', path])
        else:  # Linux
            subprocess.call(['xdg-open', path])

def main():
    """Main function to run the system tray app"""
    app = SystemTrayApp()
    try:
        app.run()
    except Exception as e:
        print(f"Error running system tray app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
