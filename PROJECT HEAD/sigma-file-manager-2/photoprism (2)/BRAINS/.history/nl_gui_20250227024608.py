#!/usr/bin/env python
"""
Natural Language Organizer GUI

A graphical interface for the natural language file organization system.
"""
import os
import sys
import json
import asyncio
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import platform
from typing import Dict, List, Any, Optional

# Make sure we can import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the natural language organizer
try:
    from natural_language_organizer import NaturalLanguageOrganizer
    from safe_paths import SafePaths
except ImportError as e:
    print(f"Error: Could not import required modules: {e}")
    print("Make sure you're running this script from the correct directory.")
    sys.exit(1)

# Example commands for inspiration
EXAMPLES = [
    "Move all PDFs to the Documents folder and name them by date",
    "Create folders for photos by year and month, then organize all images",
    "Organize code files by language into the Programming folder",
    "Move large video files older than 30 days to the Archive folder",
    "Find all downloads from last week and sort them by type"
]

class NLOrganizerApp(tk.Tk):
    """Main application window for the Natural Language Organizer"""
    
    def __init__(self):
        super().__init__()
        
        self.title("Sorting Hat - Natural Language Organizer")
        self.geometry("850x600")
        self.minsize(650, 500)
        
        self.organizer = NaturalLanguageOrganizer()
        self.active_task = None
        
        self._create_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
    def _create_ui(self):
        """Create the user interface"""
        # Set up main frame with padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title and description
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="Natural Language File Organizer", font=("Segoe UI", 16, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # Instruction input area
        instruction_frame = ttk.LabelFrame(main_frame, text="Tell me what to organize", padding=10)
        instruction_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.instruction_var = tk.StringVar()
        self.instruction_entry = ttk.Entry(instruction_frame, textvariable=self.instruction_var, font=("Segoe UI", 12))
        self.instruction_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Example buttons
        examples_frame = ttk.Frame(instruction_frame)
        examples_frame.pack(fill=tk.X)
        
        ttk.Label(examples_frame, text="Examples:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 5))
        
        for i, example in enumerate(EXAMPLES[:3]):
            short_example = example[:30] + "..." if len(example) > 30 else example
            btn = ttk.Button(examples_frame, text=short_example, 
                          command=lambda ex=example: self._use_example(ex))
            btn.pack(side=tk.LEFT, padx=5)
        
        # Path selection
        path_frame = ttk.LabelFrame(main_frame, text="Where to organize", padding=10)
        path_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.path_var = tk.StringVar(value=SafePaths.DEFAULT_SAFE_PATH)
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_btn = ttk.Button(path_frame, text="Browse...", command=self._browse_path)
        browse_btn.pack(side=tk.RIGHT)
        
        # Action buttons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.organize_btn = ttk.Button(buttons_frame, text="Organize Files", command=self._start_organization)
        self.organize_btn.pack(side=tk.RIGHT, padx=5)
        
        self.cancel_btn = ttk.Button(buttons_frame, text="Cancel", command=self._cancel_organization, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.RIGHT, padx=5)
        
        # Progress indicator
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        self.status_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode="indeterminate")
        self.progress_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # Results area
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, font=("Consolas", 10))
        self.results_text.pack(fill=tk.BOTH, expand=True)
        self.results_text.config(state=tk.DISABLED)
        
        # Initial focus
        self.instruction_entry.focus_set()
        
    def _browse_path(self):
        """Open file dialog to browse for a directory"""
        path = filedialog.askdirectory(title="Select Directory to Organize",
                                      initialdir=self.path_var.get())
        if path:
            self.path_var.set(path)
            
    def _use_example(self, example):
        """Fill instruction field with an example"""
        self.instruction_var.set(example)
        
    def _start_organization(self):
        """Start the file organization process"""
        instruction = self.instruction_var.get().strip()
        path = self.path_var.get().strip()
        
        if not instruction:
            messagebox.showerror("Error", "Please enter an organization instruction.")
            self.instruction_entry.focus_set()
            return
            
        if not os.path.exists(path):
            answer = messagebox.askyesno("Path Not Found", 
                                       f"The path '{path}' does not exist. Create it?")
            if answer:
                try:
                    os.makedirs(path, exist_ok=True)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create directory: {e}")
                    return
            else:
                return
                
        # Disable UI during organization
        self._set_busy(True)
        
        # Clear previous results
        self._clear_results()
        self._add_result(f"Starting organization...\n")
        self._add_result(f"Instruction: {instruction}\n")
        self._add_result(f"Path: {path}\n\n")
        
        # Start organization in a separate thread
        self.active_task = threading.Thread(
            target=self._run_organization,
            args=(instruction, path)
        )
        self.active_task.daemon = True
        self.active_task.start()
        
    def _run_organization(self, instruction, path):
        """Run the organization task in a background thread"""
        try:
            # Create or get the event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            # Run the organization task
            result = loop.run_until_complete(self.organizer.organize(instruction, path))
            
            # Update UI with results
            self.after(0, lambda: self._show_results(result))
        except Exception as e:
            self.after(0, lambda: self._show_error(str(e)))
        finally:
            # Re-enable UI
            self.after(0, lambda: self._set_busy(False))
            
    def _cancel_organization(self):
        """Cancel the current organization task"""
        # Note: This doesn't actually cancel the organization process since
        # we don't have a mechanism for that, but it resets the UI state
        self._set_busy(False)
        self._add_result("\nOrganization canceled by user.\n")
        
    def _show_results(self, result):
        """Display organization results in the UI"""
        if result['success']:
            self._add_result(f"\n✓ Success: {result['message']}\n")
            self._add_result(f"Files moved: {result['files_moved']}\n")
            self._add_result(f"Time taken: {result['execution_time']:.2f}s\n\n")
            
            if result['files_moved'] > 0:
                self._add_result("Files organized:\n")
                for i, action in enumerate(result['actions'], 1):
                    source = os.path.basename(action['source'])
                    dest = os.path.basename(action['destination'])
                    status = "✓" if action.get('success', True) else "✗"
                    self._add_result(f"{status} {source} → {dest}\n")
        else:
            self._add_result(f"\n✗ Error: {result['message']}\n")
            
    def _show_error(self, error_message):
        """Display an error message in the results area"""
        self._add_result(f"\n❌ Error occurred: {error_message}\n")
        messagebox.showerror("Error", f"An error occurred during organization: {error_message}")
        
    def _add_result(self, text):
        """Add text to the results area"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.insert(tk.END, text)
        self.results_text.see(tk.END)
        self.results_text.config(state=tk.DISABLED)
        
    def _clear_results(self):
        """Clear the results area"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.config(state=tk.DISABLED)
        
    def _set_busy(self, busy):
        """Set the UI busy state during organization"""
        if busy:
            self.organize_btn.config(state=tk.DISABLED)
            self.cancel_btn.config(state=tk.NORMAL)
            self.progress_var.set("Organizing files...")
            self.progress_bar.start(10)
        else:
            self.organize_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.DISABLED)
            self.progress_var.set("Ready")
            self.progress_bar.stop()
            self.active_task = None
            
    def _on_close(self):
        """Handle window close event"""
        if self.active_task and self.active_task.is_alive():
            if messagebox.askyesno("Confirm Exit", 
                                  "An organization task is in progress. Exit anyway?"):
                self.destroy()
        else:
            self.destroy()

def main():
    """Launch the application"""
    # Configure platform-specific settings
    if platform.system() == "Windows":
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    
    # Create and run the application
    app = NLOrganizerApp()
    
    # Set window icon if available
    try:
        if platform.system() == "Windows":
            app.iconbitmap(default=os.path.join(os.path.dirname(__file__), "assets", "icon.ico"))
    except:
        pass
        
    # Start the application
    app.mainloop()

if __name__ == "__main__":
    main()
