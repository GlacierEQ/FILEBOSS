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

# Initialize FastAPI app
app = FastAPI()

# Define the Sorting Hat path
SORTING_HAT_PATH = "C:/Users/casey/SortingHat"


def is_safe_path(target_path: str) -> bool:
    # Define the base path for your GitHub repositories
    github_base_path = os.path.realpath(
        "C:/Users/casey/OneDrive/Documents/GitHub/")

    # Check if the target path is within the GitHub base path
    return not target_path.startswith(github_base_path)


@app.post("/sort_files")
async def sort_files():
    # Example logic for sorting files in the Sorting Hat directory
    if not is_safe_path(SORTING_HAT_PATH):
        return {"error": "Operation not allowed in GitHub repository."}

    # Implement your sorting logic here
    # For example, move files from the Sorting Hat to organized folders
    return {"message": "Files sorted successfully."}
