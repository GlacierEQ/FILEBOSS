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
from src.model_utils import (
    load_chat_model, detect_instruction, format_prompt, 
    process_response, SYSTEM_PROMPTS
)

from dotenv import load_dotenv
load_dotenv()

SAFE_BASE_PATH = os.path.realpath(
    "C:/Users/casey/OneDrive/Documents/GitHub/llama-fs")


def is_safe_path(path: str) -> bool:
    return os.path.realpath(path).startswith(SAFE_BASE_PATH)


def sanitize_path(path: str) -> bool:
    # Reject any path containing ".." to prevent path traversal attacks.
    return ".." not in path


def validate_path(path: str) -> str:
    """
    Centralized validation for file paths.
    Checks: existence, safe base, and no path traversal.
    """
    if not path or not (is_safe_path(path) and sanitize_path(path)):
        logging.warning("Access denied for path: %s", path)
        raise HTTPException(status_code=403, detail="Access Denied")
    if not os.path.exists(path):
        logging.warning("Path does not exist: %s", path)
        raise HTTPException(status_code=400, detail="Path does not exist in filesystem")
    return path


def validate_commit_paths(base_path: str, src_path: str, dst_path: str) -> (str, str):
    """
    Constructs and validates full paths for commit.
    """
    src = os.path.join(base_path, src_path)
    dst = os.path.join(base_path, dst_path)
    if not (is_safe_path(src) and sanitize_path(src) and is_safe_path(dst) and sanitize_path(dst)):
        logging.warning("Access denied for source: %s or destination: %s", src, dst)
        raise HTTPException(status_code=403, detail="Access Denied")
    if not os.path.exists(src):
        logging.warning("Source path does not exist: %s", src)
        raise HTTPException(status_code=400, detail="Source path does not exist in filesystem")
    return src, dst


# Initialize an improved chat generator
chat_generator = load_chat_model()

# Chat history storage (simple in-memory store - would use a database in production)
chat_histories = {}

# Configure logging
logging.basicConfig(level=logging.INFO)

agentops.init(api_key=os.getenv("GROQ_API_KEY"), tags=["llama-fs"],

              auto_start_session=False)

MAX_PROMPT_LENGTH = 500  # Maximum allowed characters for prompts


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
    - **session_config**: Configuration options for the session, including which models to use and dynamic prompts.

    **Example Request Body**:
    ```json
    {
      "queries": [{"user_input": "Explain how to rename multiple files in the system?"}],
      "session_config": {
          "models": ["model1", "model2"],
          "incognito": false,
          "dynamic_prompts": {
              "tone": "friendly",
              "focus": "detailed",
              "style": "step-by-step"
          }
      }
    }
    ```

    **Responses**:
    - 200: Returns an array of AI-generated replies.
    - 422: Validation error if the request format is incorrect, including issues with dynamic prompts.

    """
    queries = request.get("queries", [])
    session_config = request.get("session_config", {})
    models = session_config.get(
        "models", ["default_model"])  # Specify models to use

    # Check the size of the incoming request
    if len(json.dumps(request)) > 1048576:  # Limit to 1 MB
        raise HTTPException(status_code=400, detail="Request body too large")
    responses = []

    # Repair logic for files during sorting
    for query in queries:
        user_input = query.get("user_input")
        # Repair logic: Rename files to YYMMDDname format
        from datetime import datetime
        date_str = datetime.now().strftime("%y%m%d")
        new_name = f"{date_str}{user_input[:20]}".ljust(
            30)  # Ensure the name is 30 characters
        user_input = new_name.strip()  # Remove any extra spaces

        if "repair" in user_input:
            # Implement your file repair logic here
            user_input = user_input.replace("repair", "fixed")
            logging.info("File repair logic applied: %s", user_input)

    tone = session_config.get("dynamic_prompts", {}).get("tone", "neutral")
    focus = session_config.get("dynamic_prompts", {}).get("focus", "general")
    style = session_config.get("dynamic_prompts", {}).get("style", "standard")

    for query in queries:
        user_input = query.get("user_input")
        for model in models:
            # Here you would integrate with the specified AI model to get a response
            # Placeholder response
            ai_response = f"[{model}] You said: {user_input}. Tone: {tone}, Focus: {focus}, Style: {style}"
            responses.append(
                {"input": user_input, "model": model, "reply": ai_response})

    # Log the responses
    logging.info("Responses: %s", responses)
    logging.info("AI interaction completed for queries: %s", queries)
    return {"responses": responses}


@app.post("/chat/message")
async def chat_message(request: dict):
    """
    Enhanced endpoint for chat messages with natural language instruction detection.
    
    **Request Body**:
    - **message**: The user's message
    - **session_id**: Optional session identifier for chat history
    - **system_prompt**: Optional system prompt style ("general", "technical", "creative")
    
    **Responses**:
    - 200: Returns the AI's reply and any detected instructions
    """
    message = request.get("message", "")
    session_id = request.get("session_id", "default")
    system_prompt_type = request.get("system_prompt", "general")
    
    # Check message length
    if len(message) > MAX_PROMPT_LENGTH:
        raise HTTPException(status_code=400, detail="Message too large")
    
    # Get or initialize chat history
    if session_id not in chat_histories:
        chat_histories[session_id] = []
    
    # Add user message to history
    chat_histories[session_id].append({"user": message})
    
    # Select system prompt
    system_prompt = SYSTEM_PROMPTS.get(system_prompt_type, SYSTEM_PROMPTS["general"])
    
    # Check for natural language instructions
    instruction_type, params = detect_instruction(message)
    
    # If instruction detected, handle it
    if instruction_type:
        if instruction_type == "list" and params.get("path"):
            try:
                path = validate_path(params.get("path", ""))
                files = os.listdir(path)
                ai_response = f"Here are the files in {path}:\n" + "\n".join(files)
            except Exception as e:
                ai_response = f"I couldn't list files: {str(e)}"
        elif instruction_type == "evolve" and params.get("prompt"):
            try:
                prompt = params.get("prompt")
                generation = chat_generator(
                    f"Improve the following: {prompt}", 
                    max_length=200, 
                    do_sample=True
                )
                ai_response = f"Here's an improved version:\n{process_response(generation[0]['generated_text'])}"
            except Exception as e:
                ai_response = f"I couldn't evolve that: {str(e)}"
        else:
            # Format the prompt with history and system prompt
            formatted_prompt = format_prompt(
                message, 
                system_prompt=system_prompt,
                history=chat_histories[session_id][:-1]  # Exclude current message
            )
            
            # Generate response
            generation = chat_generator(formatted_prompt, max_length=200, do_sample=True)
            ai_response = process_response(generation[0]['generated_text'])
            
            # Add instruction detection info
            ai_response += f"\n\nI detected a {instruction_type} instruction."
    else:
        # Standard response for non-instruction messages
        formatted_prompt = format_prompt(
            message, 
            system_prompt=system_prompt,
            history=chat_histories[session_id][:-1]
        )
        
        generation = chat_generator(formatted_prompt, max_length=200, do_sample=True)
        ai_response = process_response(generation[0]['generated_text'])
    
    # Add response to history
    chat_histories[session_id].append({"assistant": ai_response})
    
    # Limit history size
    if len(chat_histories[session_id]) > 10:
        chat_histories[session_id] = chat_histories[session_id][-10:]
    
    return {
        "reply": ai_response,
        "instruction_detected": instruction_type is not None,
        "instruction_type": instruction_type
    }


@app.post("/evolve")
async def evolve(request: dict):
    """
    Enhanced endpoint for evolving prompts with more control.
    
    **Request Body**:
    - **prompt**: Content to evolve
    - **style**: Evolution style (concise, detailed, creative, technical)
    - **focus**: What to focus on improving
    
    **Responses**:
    - 200: Returns the evolved content
    """
    prompt = request.get("prompt", "")
    style = request.get("style", "general")
    focus = request.get("focus", "")
    
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required for evolution")
    if len(prompt) > MAX_PROMPT_LENGTH:
        raise HTTPException(status_code=400, detail="Prompt too large")
    
    # Create a focused evolution prompt based on style and focus
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
    """
    This endpoint allows users to perform batch operations.

    **Request Body**:
    - **path**: The path for the batch operation.

    **Responses**:
    - 200: Returns the results of the batch operation.
    """
    # Consolidated path validation.
    path = validate_path(request.path)
    session = agentops.start_session(tags=["LlamaFS"])
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
    # Consolidated path validation.
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
    """
    This endpoint allows users to commit changes to files.

    **Request Body**:
    - **base_path**: The base path for the commit.
    - **src_path**: The source path for the commit.
    - **dst_path**: The destination path for the commit.

    **Responses**:
    - 200: Returns a success message.
    """
    src, dst = validate_commit_paths(
        request.base_path, request.src_path, request.dst_path)
    dst_directory = os.path.dirname(dst)
    os.makedirs(dst_directory, exist_ok=True)

    try:
        if os.path.isfile(src) and os.path.isdir(dst):
            shutil.move(src, os.path.join(dst, os.path.basename(src)))
        else:
            shutil.move(src, dst)
    except Exception as e:
        logging.error("Error occurred while moving resource: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while moving the resource: {e}"
        ) from e  # Explicitly re-raise the exception

    return {"message": "Commit successful"}
