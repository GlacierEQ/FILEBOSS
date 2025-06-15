#!/usr/bin/env python
"""
Log Viewer for Sorting Hat

Provides a graphical interface for viewing and searching log files.
"""
import os
import sys
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import threading
import re
import datetime
from typing import List, Dict, Optional, Any

# Set up path for importing local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import log manager
try:
    from log_manager import get_log_manager
except ImportError:
    print("Log manager not found, creating basic version")
    
    class DummyLogManager:
        def __init__(self):
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
            self.logs_dir = os.path.join(self.base_dir, 'logs')
            self.main_log_file = os.path.join(self.logs_dir, 'sorting_hat.log')
            
        def get_log_tail(self, log_file=None, lines=100):
            file_path = self.main_log_file
            if not os.path.exists(file_path):
                return [f"Log file not found: {file_path}"]
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return list(f.readlines())[-lines:]
            except Exception as e:
                return [f"Error reading log file: {e}"]
                
    def get_log_manager():
        return DummyLogManager()

class LogViewer(tk.Tk):
    """Log viewer window for viewing and searching log files"""
    
    def __init__(self):
        """Initialize the log viewer window"""
        super().__init__()
        
        # Initialize log manager
        self.log_manager = get_log_manager()
        
        # Set up window
        self.title("Sorting Hat - Log Viewer")
        self.geometry("1000x700")
        self.minsize(800, 600)
        
        # Set up UI variables
        self.log_file = tk.StringVar(value="sorting_hat.log")
        self.auto_refresh = tk.BooleanVar(value=True)
        self.filter_text = tk.StringVar()
        self.highlight_text = tk.StringVar()
        self.status_text = tk.StringVar(value="Ready")
        self.lines_to_show = tk.IntVar(value=500)
        
        # Update handling
        self.update_thread = None
        self.stopping = False
        
        # Create UI elements
        self._create_menu()
        self._create_toolbar()
        self._create_log_view()
        self._create_status_bar()
        
        # Load initial logs
        self.load_logs()
        
        # Start auto-refresh if enabled
        self._start_auto_refresh()
        
        # Bind events
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.filter_text.trace("w", self._on_filter_changed)
        self.highlight_text.trace("w", self._apply_highlights)
    
    def _create_menu(self):
        """Create application menu bar"""
        menu_bar = tk.Menu(self)
        
        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open Log File...", command=self.open_log_file)
        file_menu.add_command(label="Save Log View...", command=self.save_log_view)
        file_menu.add_separator()
        file_menu.add_command(label="Export Logs...", command=self.export_logs)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)
        menu_bar.add_cascade(label="File", menu=file_menu)
        
        # View menu
        view_menu = tk.Menu(menu_bar, tearoff=0)
        view_menu.add_checkbutton(label="Auto Refresh", variable=self.auto_refresh, 
                                command=self._toggle_auto_refresh)
        view_menu.add_separator()
        view_menu.add_command(label="Refresh Now", command=self.load_logs)
        view_menu.add_command(label="Clear View", command=self.clear_view)
        
        # Submenu for limiting lines
        lines_menu = tk.Menu(view_menu, tearoff=0)
        for lines in [100, 500, 1000, 5000, "All"]:
            lines_menu.add_radiobutton(
                label=f"Show {lines} lines",
                value=0 if lines == "All" else lines,
                variable=self.lines_to_show,
                command=self.load_logs
            )
        view_menu.add_cascade(label="Line Limit", menu=lines_menu)
        
        menu_bar.add_cascade(label="View", menu=view_menu)
        
        # Log select menu
        logs_menu = tk.Menu(menu_bar, tearoff=0)
        logs_menu.add_radiobutton(label="Main Log", variable=self.log_file, 
                              value="sorting_hat.log", command=self.load_logs)
        logs_menu.add_radiobutton(label="Error Log", variable=self.log_file, 
                               value="error.log", command=self.load_logs)
        logs_menu.add_radiobutton(label="Access Log", variable=self.log_file, 
                              value="access.log", command=self.load_logs)
        logs_menu.add_separator()
        
        # Add component-specific logs
        for component in ["watchdog", "scheduler", "evolution", "server"]:
            logs_menu.add_radiobutton(label=f"{component.capitalize()} Log", variable=self.log_file, 
                                   value=f"{component}.log", command=self.load_logs)
            
        menu_bar.add_cascade(label="Logs", menu=logs_menu)
        
        # Help menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.config(menu=menu_bar)
    
    def _create_toolbar(self):
        """Create toolbar with common actions and filters"""
        toolbar_frame = ttk.Frame(self)
        toolbar_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Left side - controls
        controls_frame = ttk.Frame(toolbar_frame)
        controls_frame.pack(side=tk.LEFT)
        
        ttk.Button(controls_frame, text="Refresh", command=self.load_logs).pack(side=tk.LEFT, padx=2)
        ttk.Checkbutton(controls_frame, text="Auto", variable=self.auto_refresh,
                    command=self._toggle_auto_refresh).pack(side=tk.LEFT, padx=10)
                    
        # Right side - search and filter
        filter_frame = ttk.Frame(toolbar_frame)
        filter_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=5)
        filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_text, width=20)
        filter_entry.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        ttk.Label(filter_frame, text="Highlight:").pack(side=tk.LEFT, padx=5)
        highlight_entry = ttk.Entry(filter_frame, textvariable=self.highlight_text, width=20)
        highlight_entry.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # Add combobox for log level filtering
        ttk.Label(filter_frame, text="Level:").pack(side=tk.LEFT, padx=5)
        self.level_var = tk.StringVar(value="ALL")
        level_combo = ttk.Combobox(filter_frame, textvariable=self.level_var, 
                                width=8, values=["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        level_combo.pack(side=tk.LEFT, padx=2)
        level_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())
    
    def _create_log_view(self):
        """Create the main log view area"""
        # Create main frame for logs
        log_frame = ttk.Frame(self)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create log text view with scrollbar
        self.log_text = ScrolledText(log_frame, wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for styling
        self.log_text.tag_configure("error", foreground="red")
        self.log_text.tag_configure("warning", foreground="orange")
        self.log_text.tag_configure("info", foreground="black")
        self.log_text.tag_configure("debug", foreground="gray")
        self.log_text.tag_configure("highlight", background="yellow", foreground="black")
        
        # Add right-click context menu
        self._setup_context_menu()
    
    def _setup_context_menu(self):
        """Set up right-click context menu for log view"""
        context_menu = tk.Menu(self.log_text, tearoff=0)
        context_menu.add_command(label="Copy", command=self._copy_selection)
        context_menu.add_command(label="Copy All", command=self._copy_all)
        context_menu.add_separator()
        context_menu.add_command(label="Select All", command=self._select_all)
        context_menu.add_separator()
        context_menu.add_command(label="Clear", command=self.clear_view)
        
        # Bind right-click to show menu
        self.log_text.bind("<Button-3>", lambda e: context_menu.tk_popup(e.x_root, e.y_root))
    
    def _create_status_bar(self):
        """Create status bar at bottom of window"""
        status_bar = ttk.Frame(self)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Status message (left side)
        status_label = ttk.Label(status_bar, textvariable=self.status_text, anchor=tk.W)
        status_label.pack(side=tk.LEFT, padx=5)
        
        # Line count (right side)
        self.line_count_var = tk.StringVar(value="0 lines")
        line_count = ttk.Label(status_bar, textvariable=self.line_count_var, anchor=tk.E)
        line_count.pack(side=tk.RIGHT, padx=5)
    
    def _start_auto_refresh(self):
        """Start auto-refresh thread if enabled"""
        if not self.update_thread or not self.update_thread.is_alive():
            self.stopping = False
            self.update_thread = threading.Thread(target=self._auto_refresh_loop)
            self.update_thread.daemon = True
            self.update_thread.start()
    
    def _auto_refresh_loop(self):
        """Background thread that periodically refreshes logs"""
        while not self.stopping:
            if self.auto_refresh.get():
                # Schedule log refresh in main thread
                self.after(0, self.load_logs)
            # Wait before next refresh
            for _ in range(30):  # 3 seconds with checks every 100ms
                if self.stopping:
                    break
                time.sleep(0.1)
    
    def _toggle_auto_refresh(self):
        """Toggle auto-refresh on or off"""
        if self.auto_refresh.get() and (not self.update_thread or not self.update_thread.is_alive()):
            self._start_auto_refresh()
    
    def load_logs(self):
        """Load log contents from the selected file"""
        # Show busy cursor during loading
        self.config(cursor="watch")
        self.update_idletasks()
        
        try:
            # Get the selected log file
            log_file_name = self.log_file.get()
            if log_file_name == "sorting_hat.log":
                log_file = None  # use default
            else:
                log_file = log_file_name
                
            # Get line limit (0 means all lines)
            line_limit = self.lines_to_show.get()
            if line_limit <= 0:
                line_limit = 100000  # arbitrary large number
                
            # Fetch log contents
            log_lines = self.log_manager.get_log_tail(log_file, line_limit)
            
            # Clear existing content
            self.clear_view(update_status=False)
            
            # Insert log lines with formatting
            for line in log_lines:
                line_text = line.strip()
                self._insert_log_line(line_text)
            
            # Apply filters
            self._apply_filters()
            
            # Update status with line count
            self.status_text.set(f"Loaded log: {log_file_name}")
            self.line_count_var.set(f"{len(log_lines)} lines")
            
        except Exception as e:
            self.status_text.set(f"Error loading logs: {e}")
        finally:
            # Restore cursor
            self.config(cursor="")
    
    def _insert_log_line(self, line):
        """Insert a log line with appropriate formatting"""
        # Determine log level tag
        tag = None
        if "ERROR" in line or "CRITICAL" in line:
            tag = "error"
        elif "WARNING" in line:
            tag = "warning"
        elif "INFO" in line:
            tag = "info"
        elif "DEBUG" in line:
            tag = "debug"
            
        # Insert with tag if available
        self.log_text.insert(tk.END, line + "\n", tag)
    
    def _apply_filters(self):
        """Apply filters to the log view"""
        # Show all text first
        self.log_text.tag_remove("hide", "1.0", tk.END)
        
        # Apply level filter
        level = self.level_var.get()
        if level != "ALL":
            # Hide lines that don't match the selected level
            start_line = 1
            while True:
                line_start = f"{start_line}.0"
                line_end = f"{start_line}.end"
                
                # Check if we've reached the end
                if not self.log_text.get(line_start, line_end):
                    break
                    
                line_text = self.log_text.get(line_start, line_end)
                if level not in line_text:
                    self.log_text.tag_add("hide", line_start, f"{start_line + 1}.0")
                    
                start_line += 1
                
        # Apply text filter
        filter_text = self.filter_text.get().strip()
        if filter_text:
            start_line = 1
            while True:
                line_start = f"{start_line}.0"
                line_end = f"{start_line}.end"
                
                # Check if we've reached the end
                if not self.log_text.get(line_start, line_end):
                    break
                    
                line_text = self.log_text.get(line_start, line_end)
                if filter_text.lower() not in line_text.lower():
                    self.log_text.tag_add("hide", line_start, f"{start_line + 1}.0")
                    
                start_line += 1
        
        # Configure hide tag to make text invisible
        self.log_text.tag_configure("hide", elide=True)
        
        # Apply highlights
        self._apply_highlights()
    
    def _on_filter_changed(self, *args):
        """Handle filter text changes"""
        # Reapply filters after a short delay (debounce)
        self.after(300, self._apply_filters)
    
    def _apply_highlights(self, *args):
        """Apply highlighting to matched text"""
        # Remove existing highlights
        self.log_text.tag_remove("highlight", "1.0", tk.END)
        
        # Get highlight text
        highlight_text = self.highlight_text.get().strip()
        if not highlight_text:
            return
            
        # Search and highlight text
        start_idx = "1.0"
        while True:
            start_idx = self.log_text.search(
                highlight_text, start_idx, tk.END, 
                nocase=True, regexp=False
            )
            if not start_idx:
                break
                
            end_idx = f"{start_idx}+{len(highlight_text)}c"
            self.log_text.tag_add("highlight", start_idx, end_idx)
            start_idx = end_idx
    
    def clear_view(self, update_status=True):
        """Clear the log view"""
        self.log_text.delete(1.0, tk.END)
        if update_status:
            self.status_text.set("View cleared")
            self.line_count_var.set("0 lines")
    
    def open_log_file(self):
        """Open a log file directly"""
        file_path = filedialog.askopenfilename(
            title="Open Log File",
            initialdir=self.log_manager.logs_dir,
            filetypes=[("Log files", "*.log"), ("All files", "*.*")]
        )
        
        if file_