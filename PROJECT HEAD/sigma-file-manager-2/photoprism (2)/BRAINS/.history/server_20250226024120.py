import json
import os
import queue
import threading
from pathlib import Path
from typing import Optional

import agentops
import nest_asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from watchdog.observers import Observer

from src.loader import get_dir_summaries
from src.tree_generator import create_file_tree
from src.watch_utils import Handler
from src.watch_utils import create_file_tree as create_watch_file_tree
from safe_paths import SafePaths

# Apply nest_asyncio for Jupyter compatibility
nest_asyncio.apply()

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
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/chat")
async def chat():
    return {"reply": "Welcome to the chat!"}


@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message")
    ai_response = f"You said: {user_message}"
    return {"reply": ai_response}


@app.post("/batch")
async def batch(request: Request):
    session = agentops.start_session(tags=["LlamaFS"])
    
    # Ensure safe path
    path = SafePaths.get_safe_path(request.path)
    print(f"Using safe path for batch operation: {path}")
    
    if not os.path.exists(path):
        raise HTTPException(
            status_code=400, detail="Path does not exist in filesystem")

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

    # Add summaries to response
    for file in files:
        file["summary"] = summaries[files.index(file)]["summary"]

    agentops.end_session(
        "Success", end_state_reason="Reorganized directory structure")
    return files


@app.post("/watch")
async def watch(request: Request, background_tasks: BackgroundTasks):
    # Ensure safe path
    path = SafePaths.get_safe_path(request.path)
    print(f"Using safe path for watch operation: {path}")
    
    if not os.path.exists(path):
        raise HTTPException(
            status_code=400, detail="Path does not exist in filesystem")

    response_queue = queue.Queue()

    observer = Observer()
    event_handler = Handler(path, create_watch_file_tree, response_queue)
    await event_handler.set_summaries()
    observer.schedule(event_handler, path, recursive=True)
    
    # Start observer in background task
    def run_observer():
        observer.start()
        try:
            while True:
                pass  # Keep running until server stops
        except:
            observer.stop()
            observer.join()
            
    background_tasks.add_task(run_observer)

    def stream():
        while True:
            try:
                response = response_queue.get()
                yield json.dumps(response) + "\n"
            except Exception:
                yield json.dumps({"error": "An error occurred while processing"}) + "\n"

    return StreamingResponse(stream())


@app.post("/commit")
async def commit(request: CommitRequest):
    # Ensure safe paths
    base_path = SafePaths.get_safe_path(request.base_path)
    
    src = os.path.join(base_path, request.src_path)
    dst = os.path.join(base_path, request.dst_path)
    
    # Extra safety check
    if SafePaths.is_github_path(src) or SafePaths.is_github_path(dst):
        raise HTTPException(
            status_code=400, 
            detail="Operation rejected: Cannot operate on GitHub repository paths"
        )

    if not os.path.exists(src):
        raise HTTPException(
            status_code=400, detail="Source path does not exist in filesystem"
        )

    # Use safe_move from SafePaths
    success = SafePaths.safe_move(src, dst)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to safely move the file"
        )

    return {"message": "Commit successful", "src": src, "dst": dst}
