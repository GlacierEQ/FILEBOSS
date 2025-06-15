import json
import os
import queue
import threading
from pathlib import Path
from typing import Optional, List

import agentops
import nest_asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks, Body
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from watchdog.observers import Observer

from src.loader import get_dir_summaries
from src.tree_generator import create_file_tree
from src.watch_utils import Handler
from src.watch_utils import create_file_tree as create_watch_file_tree
from safe_paths import SafePaths

# Try to import evolutionary components
try:
    from evolutionary_prompts import EvolutionaryPrompt
    has_evolution = True
    print("Evolution system available")
except ImportError:
    has_evolution = False
    print("Evolution system not available")

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
    
    # Get file tree (using evolutionary prompts if available)
    if has_evolution:
        # Use evolution-enhanced tree creation
        prompt = evolution.generate_organization_prompt()
        files = create_file_tree(summaries, session)
        evolution.track_recommendations(files)
    else:
        # Use standard tree creation
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
        try:
            observer.start()
            while True:
                pass  # Keep running until server stops
        except Exception as e:
            print(f"Observer error in server: {e}")
        finally:
            observer.stop()
            observer.join()
            
    background_tasks.add_task(run_observer)

    def stream():
        while True:
            try:
                response = response_queue.get(timeout=1)  # Timeout to prevent blocking
                yield json.dumps(response) + "\n"
            except queue.Empty:
                continue
            except Exception as e:
                yield json.dumps({"error": f"Unexpected error occurred: {e}"}) + "\n"

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

    # Track in evolution system before move
    if has_evolution:
        rel_src = os.path.relpath(src, base_path)
        rel_dst = os.path.relpath(dst, base_path)
        evolution.track_outcome(rel_src, rel_dst, rel_dst)

    # Use safe_move from SafePaths
    success = SafePaths.safe_move(src, dst)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to safely move the file"
        )

    return {"message": "Commit successful", "src": src, "dst": dst}


# New Evolution System Endpoints
@app.post("/feedback")
async def feedback(request: FeedbackRequest):
    """
    Submit feedback on file organization recommendations
    """
    if not has_evolution:
        return {"message": "Evolution system not available"}
    
    evolution.track_outcome(
        request.src_path, 
        request.recommended_path, 
        request.actual_path, 
        request.feedback
    )
    
    return {"message": "Feedback recorded successfully"}


@app.post("/evolution/trigger")
async def trigger_evolution(request: EvolutionRequest = Body(...)):
    """
    Trigger the evolution process to extract new patterns
    """
    if not has_evolution:
        return {"message": "Evolution system not available"}
    
    try:
        new_patterns = evolution.evolve()
        return {
            "message": "Evolution process completed successfully",
            "new_patterns_count": len(new_patterns),
            "new_patterns": new_patterns
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Evolution process failed: {str(e)}"
        )


@app.get("/evolution/report")
async def evolution_report():
    """
    Get a report on the current state of evolution
    """
    if not has_evolution:
        return {"message": "Evolution system not available"}
    
    try:
        report = evolution.get_evolution_report()
        return report
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate evolution report: {str(e)}"
        )


@app.get("/evolution/patterns")
async def evolution_patterns(min_confidence: float = 0.5):
    """
    Get current active organizational patterns
    """
    if not has_evolution:
        return {"message": "Evolution system not available"}
    
    try:
        patterns = evolution.tracker.get_active_patterns(min_confidence=min_confidence)
        return {"patterns": patterns}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve patterns: {str(e)}"
        )
