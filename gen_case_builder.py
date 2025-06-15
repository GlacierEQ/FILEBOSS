#!/usr/bin/env python3
"""
gen_case_builder.py

This script generates the complete project structure and files for the Mega CaseBuilder 3000 system.
It creates all necessary directories, Python modules, and configuration files.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional

# Project configuration
PROJECT_NAME = "case_builder"
REQUIRED_PACKAGES = [
    "grpcio",
    "grpcio-tools",
    "protobuf",
    "google-protobuf",
    "notion-client",
    "pinecone-client",
    "requests",
    "python-dotenv",
    "sqlalchemy",
    "alembic",
    "pydantic",
    "fastapi",
    "uvicorn",
    "python-jose[cryptography]",
    "passlib[bcrypt]",
    "python-multipart"
]

# Template for setup.py
SETUP_PY_TEMPLATE = """from setuptools import setup, find_packages

setup(
    name="{project_name}",
    version="0.1.0",
    packages=find_packages(),
    install_requires={install_requires},
    python_requires=">=3.8",
    entry_points={{
        'console_scripts': [
            'casebuilder={project_name}.cli:main',
        ],
    }},
)
"""

# Template for .env file
DOTENV_TEMPLATE = """# Database
DATABASE_URL=sqlite:///./casebuilder.db
DATABASE_TEST_URL=sqlite:///./test_casebuilder.db

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External Services
MEM0_API_KEY=your-mem0-api-key
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=your-pinecone-env
NOTION_API_KEY=your-notion-api-key
MEMORY_PLUGIN_TOKEN=your-memory-plugin-token
"""

def create_directory_structure(base_path: str) -> None:
    """Create the project directory structure."""
    dirs = [
        os.path.join(base_path, PROJECT_NAME),
        os.path.join(base_path, PROJECT_NAME, "api"),
        os.path.join(base_path, PROJECT_NAME, "core"),
        os.path.join(base_path, PROJECT_NAME, "db"),
        os.path.join(base_path, PROJECT_NAME, "models"),
        os.path.join(base_path, PROJECT_NAME, "schemas"),
        os.path.join(base_path, PROJECT_NAME, "services"),
        os.path.join(base_path, PROJECT_NAME, "utils"),
        os.path.join(base_path, "tests"),
        os.path.join(base_path, "protos")
    ]
    
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
        init_file = os.path.join(directory, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write("")

def create_file(filepath: str, content: str = "") -> None:
    """Create a file with the given content."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def install_dependencies() -> bool:
    """Install required Python packages."""
    print("\nInstalling required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False

def generate_proto_files(protos_dir: str) -> None:
    """Generate Python files from .proto files."""
    print("\nGenerating Python files from .proto files...")
    try:
        proto_files = [f for f in os.listdir(protos_dir) if f.endswith('.proto')]
        for proto_file in proto_files:
            cmd = [
                sys.executable, "-m", "grpc_tools.protoc",
                f"--python_out={os.path.join('case_builder', 'protos')}",
                f"--grpc_python_out={os.path.join('case_builder', 'protos')}",
                f"--proto_path={protos_dir}",
                proto_file
            ]
            subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print(f"Error generating proto files: {e}")

def create_project_files(base_path: str) -> None:
    """Create all project files."""
    print(f"\nCreating project files in {base_path}...")
    
    # Create setup.py
    setup_content = SETUP_PY_TEMPLATE.format(
        project_name=PROJECT_NAME,
        install_requires=REQUIRED_PACKAGES
    )
    create_file(os.path.join(base_path, "setup.py"), setup_content)
    
    # Create .env file
    create_file(os.path.join(base_path, ".env"), DOTENV_TEMPLATE)
    
    # Create README.md
    readme_content = """# Mega CaseBuilder 3000

An advanced AI-powered legal case management system.

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and settings
   ```

4. Run the application:
   ```bash
   uvicorn case_builder.api.main:app --reload
   ```

## Project Structure

- `case_builder/` - Main package
  - `api/` - FastAPI application and routes
  - `core/` - Core business logic
  - `db/` - Database models and migrations
  - `models/` - Pydantic models
  - `schemas/` - Database schemas
  - `services/` - Business logic services
  - `utils/` - Utility functions
- `tests/` - Test files
- `protos/` - Protocol Buffer definitions
"""
    create_file(os.path.join(base_path, "README.md"), readme_content)

    # Create main package files
    create_main_package_files(base_path)
    
    # Create proto files
    create_proto_files(os.path.join(base_path, "protos"))

def create_main_package_files(base_path: str) -> None:
    """Create main package files."""
    package_dir = os.path.join(base_path, PROJECT_NAME)
    
    # Create main __init__.py
    create_file(
        os.path.join(package_dir, "__init__.py"),
        """"""Mega CaseBuilder 3000 - Advanced Legal Case Management System"""

__version__ = "0.1.0"
"""
    )
    
    # Create core files
    create_file(
        os.path.join(package_dir, "core", "config.py"),
        """"""Application configuration."""
from pydantic import BaseSettings, PostgresDsn, validator
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Mega CaseBuilder 3000"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./casebuilder.db")
    TEST_DATABASE_URL: str = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_casebuilder.db")
    
    # External Services
    MEM0_API_KEY: Optional[str] = os.getenv("MEM0_API_KEY")
    PINECONE_API_KEY: Optional[str] = os.getenv("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT: Optional[str] = os.getenv("PINECONE_ENVIRONMENT")
    NOTION_API_KEY: Optional[str] = os.getenv("NOTION_API_KEY")
    MEMORY_PLUGIN_TOKEN: Optional[str] = os.getenv("MEMORY_PLUGIN_TOKEN")
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
"""
    )
    
    # Create API main.py
    create_file(
        os.path.join(package_dir, "api", "main.py"),
        """"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import cases, documents, evidence, timeline
from ..core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Mega CaseBuilder 3000 API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(cases.router, prefix="/api/v1/cases", tags=["cases"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(evidence.router, prefix="/api/v1/evidence", tags=["evidence"])
app.include_router(timeline.router, prefix="/api/v1/timeline", tags=["timeline"])

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}
"""
    )
    
    # Create routers
    create_file(
        os.path.join(package_dir, "api", "routers", "__init__.py"),
        """"""API routers package."""
from .cases import router as cases_router
from .documents import router as documents_router
from .evidence import router as evidence_router
from .timeline import router as timeline_router

__all__ = ["cases_router", "documents_router", "evidence_router", "timeline_router"]
"""
    )
    
    # Create example router
    create_file(
        os.path.join(package_dir, "api", "routers", "cases.py"),
        """"""Case-related API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..dependencies import get_db
from sqlalchemy.orm import Session
from ...schemas.case import Case, CaseCreate, CaseUpdate
from ...services.case_service import CaseService

router = APIRouter()

@router.get("/", response_model=List[Case])
def list_cases(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all cases with pagination."""
    cases = CaseService(db).get_cases(skip=skip, limit=limit)
    return cases

@router.post("/", response_model=Case, status_code=201)
def create_case(
    case: CaseCreate,
    db: Session = Depends(get_db)
):
    """Create a new case."""
    return CaseService(db).create_case(case)

@router.get("/{case_id}", response_model=Case)
def read_case(
    case_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific case by ID."""
    db_case = CaseService(db).get_case(case_id)
    if db_case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return db_case
"""
    )
    
    # Create other routers
    for router_name in ["documents.py", "evidence.py", "timeline.py"]:
        create_file(
            os.path.join(package_dir, "api", "routers", router_name),
            f""""""{router_name.split('.')[0].title()}-related API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..dependencies import get_db
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/")
async def list_items():
    """List all items."""
    return {{"message": "List of {router_name.split('.')[0]} items"}}
"""
        )
    
    # Create dependencies
    create_file(
        os.path.join(package_dir, "api", "dependencies.py"),
        """"""API dependencies."""
from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ...core.config import settings
from ...db.session import SessionLocal
from ...models.user import User
from ...schemas.token import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db() -> Generator:
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get the current user from the token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user
"""
    )

def create_proto_files(protos_dir: str) -> None:
    """Create .proto files."""
    # Deep Soul Catalyst proto
    create_file(
        os.path.join(protos_dir, "deep_soul_catalyst.proto"),
        """syntax = "proto3";

package ascension;

option java_package = "com.kekoa.ascension";
option go_package = "github.com/kekoa/ascension";
option optimize_for = SPEED;

// Core Deep Soul Catalyst schema with recursive iteration capabilities
message DeepSoulCatalyst {
  // Identity and metadata
  string id = 1;
  string version = 2;
  string title = 3;
  string description = 4;
  map<string, string> labels = 5; // Key-value labels for quick filtering

  // Core catalyst components
  AnalysisEngine analysis_engine = 10;
  RecursiveIterator recursive_iterator = 11;
  CodeForge code_forge = 12;
  InnovationMatrix innovation_matrix = 13;
  EvolutionaryPath evolutionary_path = 14;

  // Domain-specific extensions
  LegalFramework legal_framework = 20;
  HomeInspectionProtocol home_inspection_protocol = 21;
  AIAscensionLadder ai_ascension_ladder = 22;
  TaskadeIntegration taskade_integration = 23;  // Added Taskade integration

  // Output and execution parameters
  repeated OutputArtifact expected_outputs = 30;
  InvocationProtocol invocation_protocol = 31;

  // Extensibility
  map<string, bytes> custom_extensions = 100;
}

// ... (rest of the proto definitions)
"""
    )
    
    # Case File proto
    create_file(
        os.path.join(protos_dir, "case_file.proto"),
        """syntax = "proto3";

package kekoa.autocase;

option java_package = "com.kekoa.autocase";
option go_package = "github.com/kekoa/autocase";

// ProtoBuf definition for automatic case processing and management.
message CaseFile {
  string case_id = 1;
  string title = 2;
  string summary = 3;
  
  // References to external systems
  ExternalReferences external_references = 4;
  
  // Timeline data
  Timeline timeline = 5;
  
  // Actors involved in the case
  repeated Actor actors = 6;
  
  // Evidence related to the case
  EvidenceCollection evidence = 7;
  
  // Legal documents associated with the case
  LegalDocuments legal_docs = 8;
  
  // Summary of contradictions found in the case
  ContradictionSummary contradictions = 9;
  
  // Plan for executing the case, including tasks and automation
  ExecutionPlan execution_plan = 10;
  
  // Notes, insights, and metadata
  Metadata metadata = 11;
}

// ... (rest of the proto definitions)
"""
    )

def main() -> None:
    """Main function to generate the project structure and files."""
    print("\n=== Mega CaseBuilder 3000 Project Generator ===\n")
    
    # Get the current working directory
    base_path = os.getcwd()
    
    try:
        # Create directory structure
        create_directory_structure(base_path)
        
        # Create project files
        create_project_files(base_path)
        
        # Install dependencies
        if install_dependencies():
            print("\n✅ Project setup completed successfully!")
            print("\nNext steps:")
            print("1. Edit the .env file with your API keys and settings")
            print("2. Run 'python -m uvicorn case_builder.api.main:app --reload' to start the server")
            print("3. Open http://localhost:8000/docs to view the API documentation")
        else:
            print("\n❌ Error installing dependencies. Please install them manually.")
    
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
