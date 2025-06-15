"""Main API application entry point."""
import os
import sys
from typing import Dict, Any, List

# Add the parent directory to sys.path to be able to import from sibling modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma

# Import our LawGlance class
from lawglance_main import Lawglance

# Load environment variables
load_dotenv()

# API version
API_VERSION = "v1"

app = FastAPI(
    title="LawGlance API",
    description="API for LawGlance project - AI-powered legal assistant",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Models
class Query(BaseModel):
    question: str = Field(..., example="What constitutes a valid contract?")

class Response(BaseModel):
    answer: str

class HealthCheck(BaseModel):
    status: str
    version: str

# Initialize LawGlance dependencies
def get_lawglance():
    """Initialize and return a LawGlance instance."""
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not found")
    
    try:
        model_name = os.getenv('MODEL_NAME', 'gpt-4o-mini')
        temperature = float(os.getenv('MODEL_TEMPERATURE', '0.9'))
        llm = ChatOpenAI(model=model_name, temperature=temperature, openai_api_key=openai_api_key)
        
        embeddings = OpenAIEmbeddings()
        
        # Make sure vector store directory exists
        vector_store_dir = os.getenv('VECTOR_STORE_DIR', 'chroma_db_legal_bot_part1')
        os.makedirs(vector_store_dir, exist_ok=True)
        
        vector_store = Chroma(persist_directory=vector_store_dir, embedding_function=embeddings)
        return Lawglance(llm, embeddings, vector_store)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize LawGlance: {str(e)}")

# Middleware for logging requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    print(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    return response

@app.get("/", response_model=HealthCheck)
async def root():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}

@app.post(f"/{API_VERSION}/ask", response_model=Response)
async def ask_question(query: Query, law: Lawglance = Depends(get_lawglance)):
    """
    Ask a legal question to LawGlance.
    
    This endpoint processes a legal question and returns an AI-generated answer
    based on the legal documents in the knowledge base.
    """
    try:
        result = law.conversational(query.question)
        return Response(answer=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

# Error handler
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
