import asyncio
import json
import os
import time
import threading

from groq import Groq
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from src.loader import get_dir_summaries, get_file_summary

# Add nest_asyncio for Jupyter compatibility
try:
    import nest_asyncio
    nest_asyncio.apply()
    print("Applied nest_asyncio for Jupyter compatibility")
except ImportError:
    print("nest_asyncio not found. If running in Jupyter, install with: pip install nest_asyncio")

# Import the evolutionary prompt system if available
try:
    from evolutionary_prompts import EvolutionaryPrompt
    has_evolution = True
    print("Evolutionary prompt system available")
except ImportError:
    has_evolution = False
    print("Evolutionary prompt system not available")

class SafePathManager:
    """Helper class to manage safe paths and protect GitHub repositories"""
    
    DEFAULT_SAFE_PATH = "C:/Users/casey/OrganizeFolder"
    
    @staticmethod
    def is_github_path(path):
        """Check if a path contains GitHub directories"""
        norm_path = os.path.normpath(path).lower()
        return "github" in norm_path
    
    @staticmethod
    def get_safe_path(path=None):
        """Return a safe path to use for file operations"""
        if path and os.path.exists(path) and not SafePathManager.is_github_path(path):
            return path
        
        # Create default safe path if it doesn't exist
        if not os.path.exists(SafePathManager.DEFAULT_SAFE_PATH):
            os.makedirs(SafePathManager.DEFAULT_SAFE_PATH, exist_ok=True)
            print(f"Created default safe directory: {SafePathManager.DEFAULT_SAFE_PATH}")
            
        return SafePathManager.DEFAULT_SAFE_PATH


class Handler(FileSystemEventHandler):
    def __init__(self, base_path, callback, queue):
        # Safety checks and path initialization
        if SafePathManager.is_github_path(base_path):
            print("⚠️ Skipping watch operation on GitHub repository path.")
            self.active = False
            return
            
        self.base_path = SafePathManager.get_safe_path(base_path)
        self.callback = callback
        self.queue = queue
        self.events = []
        self.summaries = []
        self.summaries_cache = {}
        self.active = True
        
        # Initialize evolutionary system if available
        self.evolution = EvolutionaryPrompt() if has_evolution else None
        
        print(f"🔍 Watching directory: {self.base_path}")
        
    async def set_summaries(self):
        """Initialize file summaries asynchronously with Jupyter compatibility"""
        if not self.active:
            return
            
        print(f"📄 Getting summaries for {self.base_path}")
        try:
            self.summaries = await get_dir_summaries(self.base_path)
            self.summaries_cache = {s["file_path"]: s for s in self.summaries}
            print(f"✅ Loaded {len(self.summaries)} file summaries")
        except RuntimeError as e:
            # Handle async issues in Jupyter environments
            if "This event loop is already running" in str(e):
                print("⚠️ Event loop conflict detected (likely in Jupyter). Using threaded approach.")
                self._set_summaries_threaded()
            else:
                raise

    def _set_summaries_threaded(self):
        """Alternative method to get summaries in a separate thread"""
        def run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            summaries = loop.run_until_complete(get_dir_summaries(self.base_path))
            loop.close()
            self.summaries = summaries
            self.summaries_cache = {s["file_path"]: s for s in self.summaries}
            print(f"✅ Loaded {len(self.summaries)} file summaries (via thread)")
            
        thread = threading.Thread(target=run_in_thread)
        thread.daemon = True
        thread.start()
        thread.join()  # Wait for completion
    
    def is_safe_operation(self, path):
        """Check if file operation is safe to perform"""
        if not self.active:
            return False
            
        # Skip GitHub repositories
        if SafePathManager.is_github_path(path):
            print(f"⚠️ Skipping unsafe path: {path}")
            return False
        return True

    def update_summary(self, file_path):
        """Update summary for a single file"""
        if not self.is_safe_operation(file_path):
            return
            
        print(f"🔄 Updating summary for {file_path}")
        path = os.path.join(self.base_path, file_path)
        if not os.path.exists(path):
            if file_path in self.summaries_cache:
                self.summaries_cache.pop(file_path)
            return
            
        self.summaries_cache[file_path] = get_file_summary(path)
        self.summaries = list(self.summaries_cache.values())
        self.queue.put(
            {
                "files": [
                    {
                        "src_path": file_path,
                        "dst_path": file_path,
                        "summary": self.summaries_cache[file_path]["summary"],
                    }
                ]
            }
        )

    def process_event(self, event_type, src_path, dst_path=None):
        """Process file events and trigger callbacks"""
        if not self.is_safe_operation(src_path):
            return
            
        # For move events, also check destination path safety
        if dst_path and not self.is_safe_operation(dst_path):
            return

        if event_type == "moved":
            self.events.append({"src_path": src_path, "dst_path": dst_path})
            self.update_summary(src_path)
            self.update_summary(dst_path)
            
            # Track move event in evolution system if available
            if self.evolution and event_type == "moved":
                self.evolution.track_outcome(src_path, src_path, dst_path)
        else:
            self.update_summary(src_path)
            
        # Call callback for important events to get recommendations
        if event_type in ["moved", "created", "deleted"]:
            print(f"📋 Processing {event_type} event")
            files = self.callback(
                summaries=self.summaries, 
                fs_events=json.dumps({"files": self.events})
            )
            
            # Track recommendations in evolution system
            if self.evolution and files:
                self.evolution.track_recommendations(files)
                
            self.queue.put(files)

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
            
        src_path = os.path.relpath(event.src_path, self.base_path)
        print(f"➕ Created {src_path}")
        self.process_event("created", src_path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
            
        src_path = os.path.relpath(event.src_path, self.base_path)
        print(f"❌ Deleted {src_path}")
        self.process_event("deleted", src_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
            
        src_path = os.path.relpath(event.src_path, self.base_path)
        print(f"✏️ Modified {src_path}")
        self.process_event("modified", src_path)

    def on_moved(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
            
        src_path = os.path.relpath(event.src_path, self.base_path)
        dest_path = os.path.relpath(event.dest_path, self.base_path)
        print(f"🔀 Moved {src_path} > {dest_path}")
        self.process_event("moved", src_path, dest_path)


def create_file_tree(summaries, fs_events):
    # Ensure we're not processing GitHub paths
    if isinstance(fs_events, str):
        fs_events_data = json.loads(fs_events)
    else:
        fs_events_data = fs_events
        
    # Extra safety check for GitHub paths
    filtered_files = []
    for file_event in fs_events_data.get("files", []):
        src_path = file_event.get("src_path", "")
        dst_path = file_event.get("dst_path", "")
        
        if SafePathManager.is_github_path(src_path) or SafePathManager.is_github_path(dst_path):
            print(f"⚠️ Skipping GitHub path in file tree creation: {src_path} or {dst_path}")
            continue
        filtered_files.append(file_event)
    
    # Replace with filtered files
    fs_events_data["files"] = filtered_files
    
    # Get evolutionary prompts if available
    try:
        from evolutionary_prompts import EvolutionaryPrompt
        evolution = EvolutionaryPrompt()
        FILE_PROMPT = evolution.generate_organization_prompt()
        WATCH_PROMPT = evolution.generate_watch_prompt(fs_events_data)
    except ImportError:
        # Fall back to default prompts
        FILE_PROMPT = """
You will be provided with list of source files and a summary of their contents. For each file, propose a new path and filename, using a directory structure that optimally organizes the files using known conventions and best practices.

If the file is already named well or matches a known convention, set the destination path to the same as the source path.

Your response must be a JSON object with the following schema:
```json
{
    "files": [
        {
            "src_path": "original file path",
            "dst_path": "new file path under proposed directory structure with proposed file name"
        }
    ]
}
```
""".strip()

        WATCH_PROMPT = f"""
Here are a few examples of good file naming conventions to emulate, based on the files provided:

```json
{json.dumps(fs_events_data)}
```

Include the above items in your response exactly as is, along all other proposed changes.
""".strip()

    client = Groq()
    cmpl = client.chat.completions.create(
        messages=[
            {"content": FILE_PROMPT, "role": "system"},
            {"content": json.dumps(summaries), "role": "user"},
            {"content": WATCH_PROMPT, "role": "system"},
            {"content": json.dumps(fs_events_data), "role": "user"},
        ],
        model="llama-3.1-70b-versatile",
        response_format={"type": "json_object"},
        temperature=0,
    )
    
    result = json.loads(cmpl.choices[0].message.content)["files"]
    
    # Track recommendations in evolution system if available
    try:
        if 'evolution' in locals():
            evolution.track_recommendations(result)
    except:
        pass
        
    return result
