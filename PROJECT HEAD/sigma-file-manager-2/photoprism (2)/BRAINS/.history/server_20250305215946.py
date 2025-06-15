from transformers import pipeline  # Added import for HuggingFace transformers
import json
import logging

import os
import queue
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any

import agentops
import nest_asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks, Body
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from watchdog.observers import Observer

from src.loader import get_dir_summaries
from src.tree_generator import create_file_tree
from src.watch_utils import Handler
from src.watch_utils import create_file_tree as create_watch_file_tree

from dotenv import load_dotenv
load_dotenv()

agentops.init(tags=["llama-fs"],
              auto_start_session=False)


class Request(BaseModel):
    path: Optional[str] = None
    instruction: Optional[str] = None
    incognito: Optional[bool] = False


class CommitRequest(BaseModel):
    base_path: str
    src_path: str  # Relative to base_path
    dst_path: str  # Relative to base_path


class FeedbackRequest(BaseModel):
    src_path: str
    recommended_path: str
    actual_path: str
    feedback: Optional[str] = None


class EvolutionRequest(BaseModel):
    force_rebuild: Optional[bool] = False


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize evolutionary system if available
if has_evolution:
    evolution = EvolutionaryPrompt()
else:
    evolution = None


@app.get("/")
async def root():
    """
    Returns a simple welcome message.

    **Responses**:
    - 200: Returns a welcome message.
    """
    return {"message": "Hello World"}


@app.post("/batch")
async def batch(request: Request):
    session = agentops.start_session(tags=["LlamaFS"])
    path = request.path
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

    tr = LeftAligned(draw=BoxStyle(gfx=BOX_LIGHT, horiz_len=1))
    print(tr(tree))

    # Prepend base path to dst_path
    for file in files:
        file["summary"] = summaries[files.index(file)]["summary"]

    agentops.end_session(
        "Success", end_state_reason="Reorganized directory structure")
    return files


@app.post("/watch")
async def watch(request: Request):
    path = request.path
    if not os.path.exists(path):
        raise HTTPException(
            status_code=400, detail="Path does not exist in filesystem")

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
    print('*'*80)
    print(request)
    print(request.base_path)
    print(request.src_path)
    print(request.dst_path)
    print('*'*80)

    src = os.path.join(request.base_path, request.src_path)
    dst = os.path.join(request.base_path, request.dst_path)

    if not os.path.exists(src):
        raise HTTPException(
            status_code=400, detail="Source path does not exist in filesystem"
        )

    # Ensure the destination directory exists
    dst_directory = os.path.dirname(dst)
    os.makedirs(dst_directory, exist_ok=True)

    try:
        # If src is a file and dst is a directory, move the file into dst with the original filename.
        if os.path.isfile(src) and os.path.isdir(dst):
            shutil.move(src, os.path.join(dst, os.path.basename(src)))
        else:
            shutil.move(src, dst)
    except Exception as e:
        logging.error("Error occurred while moving resource: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while moving the resource: {e}"
        )

    return {"message": "Commit successful"}
