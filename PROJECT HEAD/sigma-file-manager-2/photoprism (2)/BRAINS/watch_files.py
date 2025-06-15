import asyncio
import json
import os
import queue
import time
from pathlib import Path
from watchdog.observers import Observer

import sys
# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.watch_utils import Handler, create_file_tree

def process_files_callback(summaries, fs_events):
    """
    Process file events and return recommended file organization
    """
    print(f"Processing file events: {fs_events}")
    try:
        events_data = json.loads(fs_events) if isinstance(fs_events, str) else fs_events
        return create_file_tree(summaries, events_data)
    except Exception as e:
        print(f"Error processing files: {e}")
        return {"files": []}

async def main(watch_path=None):
    # Default to safe directory if none provided
    if not watch_path:
        watch_path = "C:/Users/casey/OrganizeFolder"
        
    # Create directory if it doesn't exist
    if not os.path.exists(watch_path):
        os.makedirs(watch_path)
        print(f"Created directory: {watch_path}")
        
    print(f"Starting file watcher in {watch_path}")
    
    # Queue for file processing results
    result_queue = queue.Queue()
    
    # Create observer and handler
    observer = Observer()
    event_handler = Handler(watch_path, process_files_callback, result_queue)
    
    # Schedule observer
    observer.schedule(event_handler, watch_path, recursive=True)
    observer.start()
    
    try:
        while True:
            # Check queue for results
            try:
                result = result_queue.get_nowait()
                print("\nRecommended file organization:")
                print(json.dumps(result, indent=2))
                
                # Implement file moves here if desired
                # for file_move in result:
                #     src = os.path.join(watch_path, file_move["src_path"])
                #     dst = os.path.join(watch_path, file_move["dst_path"])
                #     # Move the file or just log the recommendation
                
            except queue.Empty:
                pass
                
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping file watcher")
    finally:
        observer.stop()
        observer.join()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Watch a directory and organize files")
    parser.add_argument("--path", help="Directory path to watch", default=None)
    args = parser.parse_args()
    
    asyncio.run(main(args.path))
