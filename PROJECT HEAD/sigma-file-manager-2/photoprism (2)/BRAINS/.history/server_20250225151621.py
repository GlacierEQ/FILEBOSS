import json
import os
import pathlib
import queue
from collections import defaultdict
from pathlib import Path
from typing import Optional
import time
import shutil  # Add this import at the beginning of your file

import agentops
import colorama
import ollama
import threading
from asciitree import LeftAligned
from asciitree.drawing import BOX_LIGHT, BoxStyle
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from llama_index.core import SimpleDirectoryReader
from pydantic import BaseModel
from termcolor import colored
from watchdog.observers import Observer

from src.loader import get_dir_summaries
from src.tree_generator import create_file_tree
from src.watch_utils import Handler
from src.watch_utils import create_file_tree as create_watch_file_tree
from src.path_utils import validate_path, validate_commit_paths

from dotenv import load_dotenv
load_dotenv()

agentops.init(api_key=os.getenv("GROQ_API_KEY"), tags=["llama-fs"],
              auto_start_session=False)


class Request(BaseModel):
    path: Optional[str] = None
    instruction: Optional[str] = None
    incognito: Optional[bool] = False


class CommitRequest(BaseModel):
    base_path: str
    src_path: str  # Relative to base_path
    dst_path: str  # Relative to base_path


app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Or restrict to ['POST', 'GET', etc.]
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/chat/welcome")
async def welcome_chat():
    return {"reply": "Welcome to the chat!"}


@app.post("/chat")
async def chat(request: dict):
    """Handle chat requests with proper error handling"""
    try:
        user_message = request.get("message", "")
        if not user_message:
            return {"reply": "Please provide a message."}
            
        # Here you would integrate with your AI model to get a response
        ai_response = f"You said: {user_message}"  # Placeholder response
        return {"reply": ai_response}
    except Exception as e:
        return {"reply": f"Error processing your request: {str(e)}"}

@app.post("/batch")
async def batch(request: Request):
    # Validate path for security - already checks existence
    path = validate_path(request.path)
    
    session = agentops.start_session(tags=["LlamaFS"])
    summaries = await get_dir_summaries(path)
    # Get file tree
    files = create_file_tree(summaries, session)

    # Recursively create dictionary from file paths
    tree = {}
    for file in files:
        parts = Path(file["dst_path"]).parts
        current = tree
        for part in parts:
            current = current.setdefault(part, {})

    tree = {path: tree}

    tr = LeftAligned(draw=BoxStyle(gfx=BOX_LIGHT, horiz_len=1))
    print(tr(tree))

    # Prepend base path to dst_path
    for file in files:
        # file["dst_path"] = os.path.join(path, file["dst_path"])
        file["summary"] = summaries[files.index(file)]["summary"]

    agentops.end_session(
        "Success", end_state_reason="Reorganized directory structure")
    return files


@app.post("/watch")
async def watch(request: Request):
    # Validate path for security - already checks existence
    path = validate_path(request.path)
    
    response_queue = queue.Queue()

    observer = Observer()
    event_handler = Handler(path, create_watch_file_tree, response_queue)
    await event_handler.set_summaries()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    # background_tasks.add_task(observer.start)

    def stream():
        while True:
            response = response_queue.get()
            yield json.dumps(response) + "\n"
            # yield json.dumps({"status": "watching"}) + "\n"
            # time.sleep(5)

    return StreamingResponse(stream())


@app.post("/commit")
async def commit(request: CommitRequest):
    # Validate paths for security - already checks existence
    src, dst = validate_commit_paths(request.base_path, request.src_path, request.dst_path)
    
    # No need for another existence check here
    dst_directory = os.path.dirname(dst)
    os.makedirs(dst_directory, exist_ok=True)

    try:
        # If src is a file and dst is a directory, move the file into dst with the original filename.
        if os.path.isfile(src) and os.path.isdir(dst):
            shutil.move(src, os.path.join(dst, os.path.basename(src)))
        else:
            shutil.move(src, dst)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while moving the resource: {e}"
        )

    return {"message": "Commit successful"}
