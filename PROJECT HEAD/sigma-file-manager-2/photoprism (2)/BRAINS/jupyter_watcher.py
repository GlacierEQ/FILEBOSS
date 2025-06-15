import asyncio
import json
import os
import queue
import threading
import time
from pathlib import Path

import nest_asyncio

# Apply nest_asyncio to allow nested event loops in Jupyter
nest_asyncio.apply()

from src.watch_utils import Handler, SafePathManager
from src.watch_utils import create_file_tree as create_watch_file_tree
from watchdog.observers import Observer

class JupyterWatcher:
    """Helper class to run file watchers safely within Jupyter notebooks"""
    
    def __init__(self, path=None):
        """Initialize a file watcher that works within Jupyter"""
        self.path = SafePathManager.get_safe_path(path)
        self.result_queue = queue.Queue()
        self.observer = None
        self.handler = None
        self.thread = None
        self.running = False
        
        print(f"🔍 Initialized watcher for path: {self.path}")
        
    async def start(self):
        """Start the watcher asynchronously"""
        if self.running:
            print("⚠️ Watcher is already running")
            return
            
        print(f"🚀 Starting file watcher in {self.path}")
        
        # Initialize handler and summaries
        self.handler = Handler(self.path, create_watch_file_tree, self.result_queue)
        await self.handler.set_summaries()
        
        # Start observer in separate thread to avoid blocking notebook
        self.observer = Observer()
        self.observer.schedule(self.handler, self.path, recursive=True)
        self.observer.start()
        self.running = True
        
        # Start processor thread
        self.thread = threading.Thread(target=self._process_results)
        self.thread.daemon = True
        self.thread.start()
        
        print("✅ Watcher started successfully. Use stop() to terminate.")
        
    def _process_results(self):
        """Process results from the watcher in background thread"""
        while self.running:
            try:
                result = self.result_queue.get(timeout=1)
                print("\n📋 Recommended file organization:")
                print(json.dumps(result, indent=2))
            except queue.Empty:
                time.sleep(0.1)
            except Exception as e:
                print(f"❌ Error processing results: {e}")
    
    def stop(self):
        """Stop the watcher"""
        if not self.running:
            print("⚠️ Watcher is not running")
            return
            
        print("⏹️ Stopping file watcher")
        self.running = False
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
            
        print("✅ Watcher stopped")
        
    def __del__(self):
        """Ensure resources are cleaned up"""
        self.stop()


# Example usage in Jupyter:
"""
# Import the watcher
from jupyter_watcher import JupyterWatcher

# Create and start watcher
watcher = JupyterWatcher("C:/Users/casey/OrganizeFolder")
await watcher.start()

# ... Do other work in notebook ...

# Stop watcher when done
watcher.stop()
"""
