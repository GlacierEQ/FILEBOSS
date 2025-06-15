import json
import os
import queue
import threadingng
from pathlib import Path
from typing import Optional, List
from typing import Optional
import agentops
import nest_asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks, Body
from fastapi.responses import StreamingResponsekgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModelmport CORSMiddleware
from watchdog.observers import Observer
from watchdog.observers import Observer
from src.loader import get_dir_summaries
from src.tree_generator import create_file_tree
from src.watch_utils import Handlerte_file_tree
from src.watch_utils import create_file_tree as create_watch_file_tree
from safe_paths import SafePathste_file_tree as create_watch_file_tree
from safe_paths import SafePaths
# Try to import evolutionary components
try: for Jupyter compatibility
    from evolutionary_prompts import EvolutionaryPromptnest_asyncio.apply()
    has_evolution = True
except ImportError:mport load_dotenv
    has_evolution = Falseload_dotenv()

# Apply nest_asyncio for Jupyter compatibilityPI_KEY"), tags=["llama-fs"],
nest_asyncio.apply()              auto_start_session=False)

from dotenv import load_dotenv
load_dotenv()

agentops.init(api_key=os.getenv("GROQ_API_KEY"), tags=["llama-fs"],
              auto_start_session=False)    incognito: Optional[bool] = False


class Request(BaseModel):t(BaseModel):
    path: Optional[str] = None
    instruction: Optional[str] = None
    incognito: Optional[bool] = False    dst_path: str  # Relative to base_path


class CommitRequest(BaseModel):app = FastAPI()
    base_path: str
    src_path: str  # Relative to base_path = [
    dst_path: str  # Relative to base_path   "*"
]

class FeedbackRequest(BaseModel):
    src_path: str
    recommended_path: str
    actual_path: strue,
    feedback: Optional[str] = None
   allow_headers=["*"],
)
app = FastAPI()

origins = [
    "*"
]    return {"message": "Hello World"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,    return {"reply": "Welcome to the chat!"}
    allow_methods=["*"],
    allow_headers=["*"],
)
):
# Initialize evolutionary system if available
if has_evolution:
    evolution = EvolutionaryPrompt()er_message}"
else:    return {"reply": ai_response}
    evolution = None


@app.get("/")
async def root():session = agentops.start_session(tags=["LlamaFS"])
    return {"message": "Hello World"}


@app.get("/chat")print(f"Using safe path for batch operation: {path}")
async def chat():
    return {"reply": "Welcome to the chat!"}th):

            status_code=400, detail="Path does not exist in filesystem")
@app.post("/chat")
async def chat(request: Request):it get_dir_summaries(path)
    data = await request.json()
    user_message = data.get("message")    files = create_file_tree(summaries, session)
    ai_response = f"You said: {user_message}"
    return {"reply": ai_response}vely create dictionary from file paths


@app.post("/batch")ile["dst_path"]).parts
async def batch(request: Request):
    session = agentops.start_session(tags=["LlamaFS"])
                current = current.setdefault(part, {})
    # Ensure safe path
    path = SafePaths.get_safe_path(request.path)    tree = {path: tree}
    print(f"Using safe path for batch operation: {path}")
     response
    if not os.path.exists(path):
        raise HTTPException(        file["summary"] = summaries[files.index(file)]["summary"]
            status_code=400, detail="Path does not exist in filesystem")

    summaries = await get_dir_summaries(path)", end_state_reason="Reorganized directory structure")
        return files
    # Get file tree (using evolutionary prompts if available)
    if has_evolution:
        # Use evolution-enhanced tree creation
        prompt = evolution.generate_organization_prompt()t: Request, background_tasks: BackgroundTasks):
        # You would need to modify create_file_tree to accept a custom prompt
        files = create_file_tree(summaries, session)
        evolution.track_recommendations(files)print(f"Using safe path for watch operation: {path}")
    else:
        # Use standard tree creationth):
        files = create_file_tree(summaries, session)
            status_code=400, detail="Path does not exist in filesystem")
    # Recursively create dictionary from file paths
    tree = {}    response_queue = queue.Queue()
    for file in files:
        parts = Path(file["dst_path"]).parts
        current = treee_watch_file_tree, response_queue)
        for part in parts:
            current = current.setdefault(part, {})observer.schedule(event_handler, path, recursive=True)

    tree = {path: tree} background task

    # Add summaries to response
    for file in files:art()
        file["summary"] = summaries[files.index(file)]["summary"]
 pass  # Keep running until server stops
    agentops.end_session(:
        "Success", end_state_reason="Reorganized directory structure")r in observer: {e}")
    return filespt Exception as e:
erver: {e}")

@app.post("/watch")
async def watch(request: Request, background_tasks: BackgroundTasks):r.stop()
    # Ensure safe pathrver.join()
    path = SafePaths.get_safe_path(request.path)
    print(f"Using safe path for watch operation: {path}")
    (run_observer)
    if not os.path.exists(path):
        raise HTTPException(    def stream():
            status_code=400, detail="Path does not exist in filesystem")():
            try:
    response_queue = queue.Queue()                response = response_queue.get(timeout=1)  # Timeout to prevent blocking
d json.dumps(response) + "\n"
    observer = Observer()
    event_handler = Handler(path, create_watch_file_tree, response_queue)e
    await event_handler.set_summaries()
    observer.schedule(event_handler, path, recursive=True)            continue
    
    # Start observer in background taskor occurred: {e}"}) + "\n"
    def run_observer():        except Exception as e:
        observer.start()on.dumps({"error": f"Unexpected error occurred: {e}"}) + "\n"
        try:
            while True:
                pass  # Keep running until server stops
        except:
            observer.stop()
            observer.join()
            
    background_tasks.add_task(run_observer)mmitRequest):

    def stream():path = SafePaths.get_safe_path(request.base_path)
        while True:    
            try:request.src_path)
                response = response_queue.get()st_path)
                yield json.dumps(response) + "\n"
            except Exception:check
                yield json.dumps({"error": "An error occurred while processing"}) + "\n"ath(src) or SafePaths.is_github_path(dst):

    return StreamingResponse(stream())
   detail="Operation rejected: Cannot operate on GitHub repository paths"
        )
@app.post("/commit")
async def commit(request: CommitRequest):    if not os.path.exists(src):



































    return {"message": "Commit successful", "src": src, "dst": dst}        )            detail="Failed to safely move the file"            status_code=500,        raise HTTPException(    if not success:        success = SafePaths.safe_move(src, dst)    # Use safe_move from SafePaths        evolution.track_outcome(rel_src, rel_dst, rel_dst)        rel_dst = os.path.relpath(dst, base_path)        rel_src = os.path.relpath(src, base_path)    if has_evolution:    # Track in evolution system before move        )            status_code=400, detail="Source path does not exist in filesystem"        raise HTTPException(    if not os.path.exists(src):        )            detail="Operation rejected: Cannot operate on GitHub repository paths"            status_code=400,         raise HTTPException(    if SafePaths.is_github_path(src) or SafePaths.is_github_path(dst):    # Extra safety check        dst = os.path.join(base_path, request.dst_path)    src = os.path.join(base_path, request.src_path)        base_path = SafePaths.get_safe_path(request.base_path)    # Ensure safe paths        raise HTTPException(
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
