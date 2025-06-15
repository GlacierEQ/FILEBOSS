import json
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

# Default templates for different sorting operations
DEFAULT_TEMPLATES = {
    "chat": [
        {
            "path": "C:/Users/casey/Documents",
            "instruction": "Sort all files into the following structured categories: \n"
                          "- Legal: Court Filings, Evidence, Lawyer Communications, Financial Disclosures, Custody & Visitation, Child Support, Restraining Orders, Appeals & Complaints.\n"
                          "- Financial: Taxes, Bank Statements, Bills & Receipts, Investments & Retirement, Credit Reports, Insurance, Loans & Debts.\n"
                          "- Real Estate: Mortgage & Rent, Home Inspections, Repair & Maintenance, Utilities, Property Documents, Moving & Storage.\n"
                          "- Family: Parenting (Visitation, School Reports, Medical Records), Health & Wellness (Doctor Visits, Fitness & Diet), Travel, Important Contacts, Family History.\n"
                          "- Business: Clients, Contracts & Agreements, Invoices & Payments, Marketing & Branding, Legal & Compliance, Business Plans, HR, Networking.\n"
                          "- Education: Courses, Certificates, Study Notes, Research Papers, Ebooks, AI & Programming, Personal Development.\n"
                          "- Creativity: Photos (Family, Events, Nature), Videos, Music, Graphic Design, Writing & Drafts, Screenplays, AI Projects.\n"
                          "- Technology: Code & Projects (GitHub Repos, AI Dev), Software & Tools, Scripts & Automation, Troubleshooting, Hardware, Cloud Backups.\n"
                          "- Miscellaneous: Random Downloads, Temporary Files, Things to Review, Experimental Projects, Old Stuff.\n"
                          "Use smart rules to rename and organize files based on content, date, and relevance. Apply logical subfolder structures where applicable.",
            "incognito": False
        },
        {
            "path": "C:/Users/casey/Documents",
            "instruction": "Sort all files into folders based on file type: PDFs, Word docs, images, videos, and spreadsheets.",
            "incognito": False
        },
        {
            "path": "C:/Users/casey/Documents",
            "instruction": "Move all files related to legal matters into 'Legal', financial statements into 'Financial', and personal files into 'Personal'.",
            "incognito": False
        },
        {
            "path": "C:/Users/casey/OneDrive/Documents",
            "instruction": "Organize all files into year/month folders based on their last modified date.",
            "incognito": False
        },
        {
            "path": "D:/Work/Projects",
            "instruction": "Group all files into project folders based on keywords in their filename. Use existing folder structures when possible.",
            "incognito": False
        }
    ],
    "batch": [
        {
            "path": "C:/Users/casey/Documents/Reports",
            "instruction": "Rename all report files to match the format 'YYYY-MM-DD_Report_Title.ext'.",
            "incognito": False
        },
        {
            "path": "C:/Users/casey/Downloads",
            "instruction": "Scan for duplicate files and suggest merging or renaming based on content similarity.",
            "incognito": False
        },
        {
            "path": "E:/Photos",
            "instruction": "Sort all images into folders by year and event based on EXIF metadata.",
            "incognito": False
        },
        {
            "path": "D:/Storage",
            "instruction": "Move all files larger than 500MB to a separate 'Large Files' folder.",
            "incognito": False
        }
    ],
    "watch": [
        {
            "path": "C:/Users/casey/Downloads",
            "instruction": "Automatically move new downloads into categorized folders: Documents, Images, Installers, and Videos.",
            "incognito": False
        },
        {
            "path": "C:/Users/casey/Desktop",
            "instruction": "Whenever a new file is added, rename it to follow a standard naming format based on its type.",
            "incognito": False
        },
        {
            "path": "C:/Users/casey/OrganizeFolder",
            "instruction": "Only move non-repository files out of the directory to prevent breaking projects.",
            "incognito": False
        }
    ],
    "commit": [
        {
            "base_path": "C:/Users/casey/Documents",
            "src_path": "OldDocs/report1.docx",
            "dst_path": "Legal/Contracts/report1.docx"
        },
        {
            "base_path": "D:/Organized",
            "src_path": "financial_statement_2024.xlsx",
            "dst_path": "D:/Organized/Financial/2024/financial_statement_2024.xlsx"
        }
    ],
    "feedback": [
        {
            "src_path": "C:/Users/casey/Documents/MisplacedFile.pdf",
            "recommended_path": "C:/Users/casey/Documents/Legal",
            "actual_path": "C:/Users/casey/Documents/Financial",
            "feedback": "This should go under Legal, not Financial."
        },
        {
            "src_path": "D:/NewFiles/NewInvoice.pdf",
            "recommended_path": "D:/Financial/Invoices",
            "actual_path": "D:/RandomFiles",
            "feedback": "Invoices should go into an 'Invoices' folder instead of 'Financial'."
        }
    ],
    "advanced": [
        {
            "path": "C:/Users/casey/Documents",
            "instruction": "Move all files older than 2 years into an 'Archive' folder.",
            "incognito": False
        },
        {
            "path": "D:/ScannedDocs",
            "instruction": "Run OCR on all PDFs and save a searchable version in the same folder.",
            "incognito": False
        },
        {
            "path": "C:/Temp",
            "instruction": "Delete all files in this folder that have not been accessed in 30 days.",
            "incognito": False
        }
    ],
    # Smart folder categories for organizing by topic
    "folder_structures": {
        "general_categories": [
            "Inbox",
            "Work",
            "Personal",
            "School",
            "Business",
            "Media",
            "Archives",
            "Shared"
        ],
        "legal": [
            "Court_Filings/Motions",
            "Court_Filings/Orders",
            "Court_Filings/Hearings",
            "Evidence/Screenshots",
            "Evidence/Emails",
            "Evidence/Audio_Video",
            "Lawyer_Communications",
            "Financial_Disclosures",
            "Custody_Visitation",
            "Child_Support",
            "Restraining_Orders",
            "Appeals_Complaints"
        ],
        "financial": [
            "Taxes/2023",
            "Taxes/2024",
            "Bank_Statements",
            "Bills_Receipts",
            "Investments_Retirement",
            "Credit_Reports",
            "Insurance",
            "Loans_Debts"
        ],
        "real_estate": [
            "Mortgage_Rent",
            "Home_Inspections",
            "Repair_Maintenance",
            "Utilities_Bills",
            "Property_Documents",
            "Moving_Storage"
        ],
        "family": [
            "Parenting/Visitation",
            "Parenting/School_Reports",
            "Parenting/Medical_Records",
            "Health_Wellness/Doctor_Visits",
            "Health_Wellness/Fitness_Diet",
            "Travel_Vacation",
            "Important_Contacts",
            "Family_History_Genealogy",
            "Personal_Projects"
        ],
        "business": [
            "Clients",
            "Contracts_Agreements",
            "Invoices_Payments",
            "Marketing_Branding",
            "Legal_Compliance",
            "Business_Plans_Proposals",
            "Employees_HR",
            "Expenses_Budgeting",
            "Networking_Contacts"
        ],
        "education": [
            "Courses",
            "Certificates",
            "Study_Notes",
            "Research_Papers",
            "Ebooks_PDFs",
            "AI_Programming",
            "Personal_Development"
        ],
        "creativity": [
            "Photos/Family",
            "Photos/Events",
            "Photos/Nature",
            "Videos",
            "Music",
            "Graphic_Design",
            "Writing_Drafts",
            "Screenplays_Scripts",
            "AI_Projects"
        ],
        "technology": [
            "Code_Projects/GitHub_Repos",
            "Code_Projects/AI_Development",
            "Software_Tools",
            "Scripts_Automation",
            "Troubleshooting_Fixes",
            "Hardware_Builds",
            "Cloud_Backups"
        ],
        "miscellaneous": [
            "Random_Downloads",
            "Temporary_Files",
            "Things_to_Review",
            "Experimental_Projects",
            "Old_Stuff"
        ]
    }
}

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
    """Get welcome message and default templates for chat endpoint"""
    return {
        "reply": "Welcome to the chat!",
        "templates": DEFAULT_TEMPLATES["chat"]
    }


@app.post("/chat")
async def chat(request: Request = None):
    """Process chat request or return default templates if no request provided"""
    # If request is None or missing path/instruction, return default templates
    if not request or (not request.path and not request.instruction):
        return {"default_templates": DEFAULT_TEMPLATES["chat"]}
    
    # Process the actual request
    try:
        data = await request.json()
        user_message = data.get("message", "")
        
        # Here you would process the chat message with your AI
        ai_response = f"Processed request: {user_message}"
        
        return {"reply": ai_response}
    except Exception as e:
        return {"reply": f"Error processing request: {str(e)}"}


@app.get("/templates/{template_type}")
async def get_templates(template_type: str):
    """Get default templates for a specific endpoint"""
    if template_type not in DEFAULT_TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Template type '{template_type}' not found")
    
    return {"templates": DEFAULT_TEMPLATES[template_type]}


@app.get("/folder_structures/{category}")
async def get_folder_structure(category: str = None):
    """Get default folder structure templates for organizing files"""
    folder_structures = DEFAULT_TEMPLATES["folder_structures"]
    
    if category and category not in folder_structures:
        raise HTTPException(status_code=404, detail=f"Folder structure category '{category}' not found")
    
    if category:
        return {"structure": folder_structures[category]}
    else:
        return {"categories": list(folder_structures.keys())}


@app.post("/batch")
async def batch(request: Request):
    # If missing path/instruction, return default templates
    if not request.path and not request.instruction:
        return {"default_templates": DEFAULT_TEMPLATES["batch"]}
    
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
    # If missing path/instruction, return default templates
    if not request.path and not request.instruction:
        return {"default_templates": DEFAULT_TEMPLATES["watch"]}
    
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
async def commit(request: CommitRequest = None):
    # Return default examples if no request provided
    if not request:
        return {"default_templates": DEFAULT_TEMPLATES["commit"]}
    
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
async def feedback(request: FeedbackRequest = None):
    """Submit feedback on file organization recommendations"""
    # Return default examples if no request provided
    if not request:
        return {"default_templates": DEFAULT_TEMPLATES["feedback"]}
    
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
    """Trigger the evolution process to extract new patterns"""
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
    """Get a report on the current state of evolution"""
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
    """Get current active organizational patterns"""
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


@app.get("/help")
async def help():
    """Get help information about available endpoints and examples"""
    return {
        "endpoints": {
            "/chat": "Sort files once based on a specific rule",
            "/batch": "Process multiple sorting tasks at once",
            "/watch": "Monitor folder for real-time auto-sorting",
            "/commit": "Approve file moves before execution",
            "/feedback": "Train AI on sorting accuracy",
            "/evolution/trigger": "Improve sorting with AI learning",
            "/evolution/report": "Get AI sorting report",
            "/evolution/patterns": "Retrieve active sorting patterns",
            "/templates/{type}": "Get default templates for an endpoint",
            "/folder_structures/{category}": "Get smart folder structure templates"
        },
        "examples": {
            "Get help": "GET /help",
            "Get chat templates": "GET /templates/chat",
            "Get folder structures": "GET /folder_structures",
            "Get specific folder structure": "GET /folder_structures/legal",
            "Sort files by type": "POST /chat with appropriate JSON body",
            "Monitor downloads folder": "POST /watch with appropriate JSON body"
        }
    }
