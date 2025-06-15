import asyncio
import json
import os
import time

from groq import Groq
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from src.loader import get_dir_summaries, get_file_summary

# Add nest_asyncio for Jupyter compatibility
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    print("nest_asyncio not found. If running in Jupyter, install it with: pip install nest_asyncio")

class Handler(FileSystemEventHandler):
    def __init__(self, base_path, callback, queue):
        # Safety check for GitHub repos
        if "GitHub" in base_path:
            print("Skipping because it's in the GitHub repo.")
            self.active = False
            return
        
        # Use provided path or fallback to safe path
        self.base_path = base_path
        self.safe_path = "C:/Users/casey/OrganizeFolder"
        
        # Verify we're in a safe location
        if not os.path.exists(self.base_path) or "GitHub" in os.path.abspath(self.base_path):
            print(f"Using safe path {self.safe_path} instead")
            self.base_path = self.safe_path
            
        self.callback = callback
        self.queue = queue
        self.events = []
        self.summaries = []
        self.summaries_cache = {}
        self.active = True
        print(f"Watching directory {self.base_path}")
        
        # Initialize summaries asynchronously
        try:
            asyncio.create_task(self.set_summaries())
        except RuntimeError:
            # Fallback for non-async environments
            loop = asyncio.get_event_loop()
            if loop.is_running():
                print("Using existing event loop to initialize summaries")
                loop.create_task(self.set_summaries())
            else:
                print("Running set_summaries synchronously")
                loop.run_until_complete(self.set_summaries())

    async def set_summaries(self):
        print(f"Getting summaries for {self.base_path}")
        self.summaries = await get_dir_summaries(self.base_path)
        self.summaries_cache = {s["file_path"]: s for s in self.summaries}
        print(f"Loaded {len(self.summaries)} file summaries")

    def is_safe_path(self, path):
        """Check if the path is safe to process"""
        abs_path = os.path.abspath(path)
        if "GitHub" in abs_path:
            print(f"Skipping unsafe path: {path}")
            return False
        return True
    
    def update_summary(self, file_path):
        if not self.active or not self.is_safe_path(file_path):
            return
            
        print(f"Updating summary for {file_path}")
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
        """Process file event and trigger callback if needed"""
        if not self.active:
            return
            
        if event_type == "moved":
            self.events.append({"src_path": src_path, "dst_path": dst_path})
            self.update_summary(src_path)
            self.update_summary(dst_path)
        else:
            self.update_summary(src_path)
            
        # Only call callback for significant events
        if event_type in ["moved", "created", "deleted"]:
            files = self.callback(
                summaries=self.summaries, 
                fs_events=json.dumps({"files": self.events})
            )
            self.queue.put(files)

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
            
        src_path = os.path.relpath(event.src_path, self.base_path)
        print(f"Created {src_path}")
        self.process_event("created", src_path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
            
        src_path = os.path.relpath(event.src_path, self.base_path)
        print(f"Deleted {src_path}")
        self.process_event("deleted", src_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
            
        src_path = os.path.relpath(event.src_path, self.base_path)
        print(f"Modified {src_path}")
        self.process_event("modified", src_path)

    def on_moved(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
            
        src_path = os.path.relpath(event.src_path, self.base_path)
        dest_path = os.path.relpath(event.dest_path, self.base_path)
        print(f"Moved {src_path} > {dest_path}")
        self.process_event("moved", src_path, dest_path)


def create_file_tree(summaries, fs_events):

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
{fs_events}
```

Include the above items in your response exactly as is, along all other proposed changes.
""".strip()

    client = Groq()
    cmpl = client.chat.completions.create(
        messages=[
            {"content": FILE_PROMPT, "role": "system"},
            {"content": json.dumps(summaries), "role": "user"},
            {"content": WATCH_PROMPT, "role": "system"},
            {"content": json.dumps(fs_events), "role": "user"},
        ],
        model="llama-3.1-70b-versatile",
        response_format={"type": "json_object"},
        temperature=0,
    )
    return json.loads(cmpl.choices[0].message.content)["files"]
