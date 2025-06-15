from transformers import pipeline  # Added import for HuggingFace transformers
import json
import logging
import os
import pathlib
import queue
from collections import defaultdict
from pathlib import Path
from typing import Optional
import time
import shutil  # Add this import at the beginning of your file
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Initialize FastAPI app
app = FastAPI()

# Define the Sorting Hat path
SORTING_HAT_PATH = "C:/Users/casey/SortingHat"


class SortingHatHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            print(f"New file detected: {event.src_path}")
            # Call your sorting logic here
            self.sort_files(event.src_path)

    def sort_files(self, file_path):
        # Implement your sorting logic here
        print(f"Sorting file: {file_path}")


# Set up the observer
observer = Observer()
event_handler = SortingHatHandler()
observer.schedule(event_handler, path=SORTING_HAT_PATH, recursive=False)
observer.start()

try:
    while True:
        time.sleep(1)  # Keep the script running
except KeyboardInterrupt:
    observer.stop()
observer.join()
