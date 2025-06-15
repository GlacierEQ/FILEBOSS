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
from multi_ai_chat import MultiAIChat # Import MultiAIChat

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

# New models for chat functionality
class Query(BaseModel):
    user_input: str

class SessionConfig(BaseModel):
    models: List[str]
    incognito: bool

class ChatRequest(BaseModel):
    queries: List[Query]
    session_config: SessionConfig


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
has_evolution = False # Assuming for now, will need to check if this is defined elsewhere
if has_evolution:
    evolution = EvolutionaryPrompt()
else:
    evolution = None

# Initialize MultiAIChat
ai_chat_system = MultiAIChat(ai_models=["gpt2"]) # Using gpt2 as a default model


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


@app.post("/chat/ai_interact")
async def chat_with_ai(chat_request: ChatRequest):
    """
    Handles AI interaction for chat.
    """
    responses = []
    for query in chat_request.queries:
        # Use the models specified in session_config, or default to initialized models
        current_ai_models = chat_request.session_config.models if chat_request.session_config.models else ["gpt2"]
        # Re-initialize MultiAIChat if models change, or handle model switching within MultiAIChat
        # For simplicity, we'll assume a single instance for now and use the models from config if provided
        # In a real app, you might want to manage multiple MultiAIChat instances or dynamically load models.
        
        # Temporarily re-initialize with requested models for this request
        # A more robust solution would involve managing model instances more carefully
        temp_ai_chat_system = MultiAIChat(ai_models=current_ai_models)
        model_responses = temp_ai_chat_system.send_prompt(query.user_input)
        
        # Format responses for chatbox.html
        for model, reply_text in model_responses.items():
            responses.append({"model": model, "reply": reply_text})
            
    return JSONResponse(content={"responses": responses})
