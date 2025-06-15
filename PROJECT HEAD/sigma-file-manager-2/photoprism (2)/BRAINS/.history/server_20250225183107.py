import json
import logging
import os
import queue
import shutil
import time
from collections import defaultdict
from pathlib import Path
from typing import Optional, Union

# Third-party imports
import agentops
import colorama
import ollama
import threading
from asciitree import LeftAligned
from asciitree.drawing import BOX_LIGHT, BoxStyle
from fastapi import FastAPI, HTTPException, Request as FastAPIRequest
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from llama_index.core import SimpleDirectoryReader
from pydantic import BaseModel
from termcolor import colored
from watchdog.observers import Observer
from transformers import pipeline

# Local imports
from src.loader import get_dir_summaries
from src.tree_generator import create_file_tree
from src.watch_utils import Handler
from src.watch_utils import create_file_tree as create_watch_file_tree
from src.path_utils import validate_path, validate_commit_paths
from src.model_utils import (
    load_chat_model, detect_instruction, format_prompt, 
    process_response, SYSTEM_PROMPTS
)

from dotenv import load_dotenv
load_dotenv()

# Constants
MAX_PROMPT_LENGTH = 500
MAX_REQUEST_SIZE = 1048576  # 1 MB

# Initialize chat generator and session storage
chat_generator = load_chat_model()
chat_histories = {}

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize agentops
agentops.init(api_key=os.getenv("GROQ_API_KEY"), tags=["llama-fs"], auto_start_session=False)

# Models
class Request(BaseModel):
    path: Optional[str] = None
    instruction: Optional[str] = None
    incognito: Optional[bool] = False

class CommitRequest(BaseModel):
    base_path: str
    src_path: str  # Relative to base_path
    dst_path: str  # Relative to base_path

# App setup
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Returns a simple welcome message."""
    return {"message": "Hello World"}

@app.get("/chat/welcome")
async def welcome_chat():
    """Returns a welcome message for the chat interface."""
    return {"reply": "Welcome to the chat!"}

@app.post("/chat/ai_interact")
async def ai_interact(request: dict):
    """Handles multi-model chat interactions with configurable parameters."""
    # Check the size of the incoming request
    if len(json.dumps(request)) > MAX_REQUEST_SIZE:
        raise HTTPException(status_code=400, detail="Request body too large")
        
    queries = request.get("queries", [])
    session_config = request.get("session_config", {})
    models = session_config.get("models", ["default_model"])
    
    # Get prompt settings
    tone = session_config.get("dynamic_prompts", {}).get("tone", "neutral")
    focus = session_config.get("dynamic_prompts", {}).get("focus", "general")
    style = session_config.get("dynamic_prompts", {}).get("style", "standard")
    
    responses = []
    for query in queries:
        user_input = query.get("user_input", "")
        for model in models:
            ai_response = f"[{model}] You said: {user_input}. Tone: {tone}, Focus: {focus}, Style: {style}"
            responses.append({"input": user_input, "model": model, "reply": ai_response})
    
    logging.info("AI interaction completed for %d queries", len(queries))
    return {"responses": responses}

@app.post("/chat/message")
async def chat_message(request: Union[dict, str, FastAPIRequest]):
    """
    Enhanced endpoint that handles both string and dict requests for chat messages.
    Includes natural language instruction detection.
    """
    # Extract message from different possible request types
    if isinstance(request, str):
        message = request
        session_id = "default"
        system_prompt_type = "general"
    elif isinstance(request, dict):
        message = request.get("message", "")
        session_id = request.get("session_id", "default")
        system_prompt_type = request.get("system_prompt", "general")
    else:
        # Handle FastAPI Request object
        body = await request.json()
        message = body.get("message", "")
        session_id = body.get("session_id", "default")
        system_prompt_type = body.get("system_prompt", "general")
    
    # Check message length
    if len(message) > MAX_PROMPT_LENGTH:
        raise HTTPException(status_code=400, detail="Message too large")
    
    # Initialize or get chat history
    if session_id not in chat_histories:
        chat_histories[session_id] = []
    chat_histories[session_id].append({"user": message})
    
    # Get system prompt
    system_prompt = SYSTEM_PROMPTS.get(system_prompt_type, SYSTEM_PROMPTS["general"])
    
    # Check for natural language instructions
    instruction_type, params = detect_instruction(message)
    
    # Process based on instruction type or standard chat
    if instruction_type:
        ai_response = await process_instruction(instruction_type, params, system_prompt, 
                                               chat_histories[session_id])
    else:
        # Standard chat response
        formatted_prompt = format_prompt(
            message, 
            system_prompt=system_prompt,
            history=chat_histories[session_id][:-1]
        )
        generation = chat_generator(formatted_prompt, max_length=200, do_sample=True)
        ai_response = process_response(generation[0]['generated_text'])
    
    # Update history and manage size
    chat_histories[session_id].append({"assistant": ai_response})
    if len(chat_histories[session_id]) > 10:
        chat_histories[session_id] = chat_histories[session_id][-10:]
    
    return {
        "reply": ai_response,
        "instruction_detected": instruction_type is not None,
        "instruction_type": instruction_type
    }

async def process_instruction(instruction_type, params, system_prompt, history):
    """Helper to process natural language instructions in chat."""
    if instruction_type == "list" and params.get("path"):
        try:
            path = validate_path(params.get("path", ""))
            files = os.listdir(path)
            return f"Here are the files in {path}:\n" + "\n".join(files)
        except Exception as e:
            return f"I couldn't list files: {str(e)}"
    elif instruction_type == "evolve" and params.get("prompt"):
        try:
            prompt = params.get("prompt")
            generation = chat_generator(
                f"Improve the following: {prompt}", 
                max_length=200, 
                do_sample=True
            )
            return f"Here's an improved version:\n{process_response(generation[0]['generated_text'])}"
        except Exception as e:
            return f"I couldn't evolve that: {str(e)}"
    else:
        # For other instruction types
        formatted_prompt = format_prompt(
            f"Process this {instruction_type} instruction: {params}", 
            system_prompt=system_prompt,
            history=history[:-1]
        )
        generation = chat_generator(formatted_prompt, max_length=200, do_sample=True)
        response = process_response(generation[0]['generated_text'])
        return f"{response}\n\nI detected a {instruction_type} instruction."

@app.post("/evolve")
async def evolve(request: dict):
    """Enhanced endpoint for evolving text with different styles."""
    prompt = request.get("prompt", "")
    style = request.get("style", "general")
    focus = request.get("focus", "")
    
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required for evolution")
    if len(prompt) > MAX_PROMPT_LENGTH:
        raise HTTPException(status_code=400, detail="Prompt too large")
    
    # Build the evolution prompt with style and focus
    evolution_prompt = f"Improve the following"
    if style == "concise":
        evolution_prompt += " by making it more concise and direct"
    elif style == "detailed":
        evolution_prompt += " by adding more helpful details"
    elif style == "creative":
        evolution_prompt += " by making it more creative and engaging"
    elif style == "technical":
        evolution_prompt += " by adding technical precision"
    
    if focus:
        evolution_prompt += f", focusing on {focus}"
    
    evolution_prompt += f": {prompt}"
    
    generation = chat_generator(evolution_prompt, max_length=250, do_sample=True)
    evolution = process_response(generation[0]['generated_text'])
    
    return {
        "evolution": evolution,
        "style": style,
        "focus": focus
    }

@app.post("/batch")
async def batch(request: Request):
    """Batch file operation endpoint."""
    path = validate_path(request.path)
    session = agentops.start_session(tags=["LlamaFS"])
    
    summaries = await get_dir_summaries(path)
    files = create_file_tree(summaries, session)
    
    # Build file tree
    tree = {}
    for file in files:
        parts = Path(file["dst_path"]).parts
        current = tree
        for part in parts:
            current = current.setdefault(part, {})
    tree = {path: tree}
    
    # Display the tree
    tr = LeftAligned(draw=BoxStyle(gfx=BOX_LIGHT, horiz_len=1))
    print(tr(tree))
    
    # Add summaries to response
    for file in files:
        file["summary"] = summaries[files.index(file)]["summary"]
    
    agentops.end_session("Success", end_state_reason="Reorganized directory structure")
    return files

@app.post("/watch")
async def watch(request: Request):
    """File system change watching endpoint."""
    path = validate_path(request.path)
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
    """Commit file changes endpoint."""
    src, dst = validate_commit_paths(request.base_path, request.src_path, request.dst_path)
    dst_directory = os.path.dirname(dst)
    os.makedirs(dst_directory, exist_ok=True)
    
    try:
        if os.path.isfile(src) and os.path.isdir(dst):
            shutil.move(src, os.path.join(dst, os.path.basename(src)))
        else:
            shutil.move(src, dst)
    except Exception as e:
        logging.error("Error moving resource: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while moving the resource: {e}"
        )
    
    return {"message": "Commit successful"}
