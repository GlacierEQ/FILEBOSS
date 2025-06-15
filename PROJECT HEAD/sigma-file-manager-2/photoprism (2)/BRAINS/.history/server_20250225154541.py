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
    """
    Returns a simple welcome message.

    **Responses**:
    - 200: Returns a welcome message.
    """
    return {"message": "Hello World"}


@app.get("/chat/welcome")
async def welcome_chat():
    """
    Returns a welcome message for the chat interface.

    **Responses**:
    - 200: Returns a welcome message.
    """
    return {"reply": "Welcome to the chat!"}


@app.post("/chat/ai_interact")
async def ai_interact(request: dict):
    """
    This endpoint allows users to interact with multiple AI models.

    - **queries**: A list of user queries in natural language.
    - **session_config**: Configuration options for the session, including which models to use.

    **Example Request Body**:
    ```json
    {
      "queries": [{"user_input": "Explain how to rename multiple files in the system?"}],
      "session_config": {"models": ["model1", "model2"], "incognito": false}
    }
    ```

    **Responses**:
    - 200: Returns an array of AI-generated replies.
    - 422: Validation error if the request format is incorrect.
    """
    queries = request.get("queries", [])
    session_config = request.get("session_config", {})
    models = session_config.get(
        "models", ["default_model"])  # Specify models to use

    responses = []
    for query in queries:
        user_input = query.get("user_input")
        for model in models:
            # Here you would integrate with the specified AI model to get a response
            # Placeholder response
            ai_response = f"[{model}] You said: {user_input}"
            responses.append(
                {"input": user_input, "model": model, "reply": ai_response})

    return {"responses": responses}


@app.post("/chat/message")
async def chat_message(message: str):
    """
    This endpoint allows users to send a single message to the AI.

    **Request Body**:
    - **message**: The user's message.

    **Responses**:
    - 200: Returns the AI's reply.
    """
    ai_response = f"You said: {message}"  # Placeholder response
    return {"reply": ai_response}


@app.post("/batch")
async def batch(request: Request):
    """
    This endpoint allows users to perform batch operations.

    **Request Body**:
    - **path**: The path for the batch operation.

    **Responses**:
    - 200: Returns the results of the batch operation.
    """
    session = agentops.start_session(tags=["LlamaFS"])
    path = request.path
    if not os.path.exists(path):
        raise HTTPException(
            status_code=400, detail="Path does not exist in filesystem")

    summaries = await get_dir_summaries(path)
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

    for file in files:
        file["summary"] = summaries[files.index(file)]["summary"]

    agentops.end_session(
        "Success", end_state_reason="Reorganized directory structure")
    return files


@app.post("/watch")
async def watch(request: Request):
    """
    This endpoint allows users to watch a directory for changes.

    **Request Body**:
    - **path**: The path to watch.

    **Responses**:
    - 200: Returns a stream of changes.
    """
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

    def stream():
        while True:
            response = response_queue.get()
            yield json.dumps(response) + "\n"

    return StreamingResponse(stream())


@app.post("/commit")
async def commit(request: CommitRequest):
    """
    This endpoint allows users to commit changes to files.

    **Request Body**:
    - **base_path**: The base path for the commit.
    - **src_path**: The source path for the commit.
    - **dst_path**: The destination path for the commit.

    **Responses**:
    - 200: Returns a success message.
    """
    src = os.path.join(request.base_path, request.src_path)
    dst = os.path.join(request.base_path, request.dst_path)

    if not os.path.exists(src):
        raise HTTPException(
            status_code=400, detail="Source path does not exist in filesystem"
        )

    dst_directory = os.path.dirname(dst)
    os.makedirs(dst_directory, exist_ok=True)

    try:
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
