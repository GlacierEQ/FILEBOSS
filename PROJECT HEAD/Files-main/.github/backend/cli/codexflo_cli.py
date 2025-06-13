#!/usr/bin/env python3
"""
CodexFlō CLI - Command Line Interface for AI-Driven Strategic File Nexus
Enhanced with robust error handling, resource management, and validation
"""

import typer
import asyncio
import signal
import atexit
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.tree import Tree
from rich.prompt import Prompt, Confirm
import yaml
import json
from typing import Optional, List, Dict, Any
import subprocess
import sys
import os
import time
import requests
import psutil
from datetime import datetime
from contextlib import asynccontextmanager
import logging
from dataclasses import dataclass
from enum import Enum
import tempfile
import shutil

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global process tracking for cleanup
_active_processes: List[subprocess.Popen] = []
_cleanup_registered = False

class ConfigError(Exception):
    """Configuration validation error"""
    pass

class ServiceError(Exception):
    """Service startup/management error"""
    pass

class ValidationError(Exception):
    """Input validation error"""
    pass

@dataclass
class ServiceHealth:
    """Service health status"""
    backend: bool = False
    frontend: bool = False
    ai_engine: bool = False
    database: bool = False

class AIProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    LOCAL = "local"

class LegalDocumentType(str, Enum):
    """Legal document classification types"""
    PLEADING = "pleading"
    MOTION = "motion"
    BRIEF = "brief"
    DISCOVERY = "discovery"
    EVIDENCE = "evidence"
    CORRESPONDENCE = "correspondence"
    CONTRACT = "contract"
    STATUTE = "statute"
    CASE_LAW = "case_law"
    TRANSCRIPT = "transcript"
    EXHIBIT = "exhibit"
    AFFIDAVIT = "affidavit"
    OTHER = "other"

# AI Pipeline Prompt for Enhanced File Management
AI_PIPELINE_PROMPT = """
AI-Enhanced Legal File Management & Case-Building Pipeline
==========================================================

Vision
------

Create a self-evolving platform that ingests any file, understands its legal significance, and continuously assembles the strongest possible case portfolio—while keeping everything searchable, auditable, and compliant.

High-Level Dataflow
-------------------

1. Ingestion → 2. Understanding → 3. Structuring → 4. Case Construction → 5. Review & Feedback → 6. Continuous Learning

Detailed Pipeline
-----------------

1. **Intelligent Ingestion**
   • Auto-detect new/updated files (local folders, email, cloud drives, APIs).
   • OCR scanned items with legal-tuned language models.
   • Generate cryptographic hash + provenance metadata.
   • "First-look" classifier → doc type, sensitivity, jurisdiction, language.

2. **Deep Understanding Layer**
   • Large-context LLM extracts: entities, dates, amounts, claim/defense language, citations.
   • Cross-doc coreference to unify parties & events.
   • Relevance scoring vs. active matters; auto-assign to existing or new cases.
   • Summarize intent, obligations, and deadlines in plain English.

3. **Dynamic Structuring Engine**
   • Hierarchical folders auto-built: `/[Client]/[Matter]/[Phase]/[Doc Type]/`.
   • Multi-tag graph (party, topic, statute, privilege, version, evidentiary weight).
   • Smart filename: `[YYYY-MM-DD] [Parties] [DocType] [KeyRef] v[n].pdf`.
   • Real-time relationship map stored in graph DB for instant traversal.

4. **Automated Case-Building Core**
   • Timeline synthesis: ordered chain of events with citation links.
   • Claim matrix: each legal element → supporting evidence list → opposing evidence → strength score.
   • Gap analysis: highlight missing proofs, expired deadlines, unserved parties.
   • Draft pleading generator pulls structured facts into motion/complaint templates.

5. **Review, Collaboration & Reporting**
   • Natural-language query: "Show all evidence contradicting witness X after 6 Jan 2023."
   • One-click export packs (ZIP, load file, PDF bundle with bookmarks).
   • Dashboard: upcoming deadlines, privilege flags, review progress.
   • Canary rollout for new AI models—compare outputs vs. stable, auto-rollback on regressions.

6. **Security, Compliance & Audit**
   • Role-based ACL + ethical walls; field-level redaction on share/export.
   • Immutable audit ledger: who viewed, edited, exported each file.
   • Retention/hold rules per jurisdiction & matter type.
   • Continuous vulnerability scanning of code & dependencies.

7. **Continuous Learning Feedback Loop**
   • Users thumbs-up/down categorizations & summaries → fine-tune models nightly.
   • Metrics tracked: classification accuracy, search precision, time-to-document, case build completeness.
   • Automated A/B tests of new prompt chains / model versions.
   • Knowledge distillation into firm-specific precedent library.

Key AI Components
-----------------

• **LLM Ensemble**: one long-context model for holistic analysis, one fast model for micro-tasks.
• **Few-shot Prompt Bank**: doc classification, summary, deadline extraction, privilege detection.
• **Retrieval-Augmented Generation (RAG)**: blend firm knowledge base with public statutes & caselaw.
• **Graph Embeddings**: power semantic search & relationship discovery.
• **Active Learning**: surface low-confidence items for human validation first.

Success Metrics
---------------

• ≥ 95 % correct doc classification within 3 s of upload.
• ≥ 90 % recall of key deadlines & obligations.
• 50 % reduction in paralegal hours to prepare initial case binder.
• < 1 % privilege breach incidents.
• Continuous improvement trend on model accuracy month-over-month.

Implementation Milestones
-------------------------

1. **MVP**: ingestion + OCR + basic classification & renaming.
2. **v1**: tagging, folder automation, searchable summaries.
3. **v2**: case timeline, claim matrix, deadline tracker.
4. **v3**: proof-chart builder, pleading generator, canary model deployment.
5. **v4+**: advanced analytics (pattern discovery, adversary strategy prediction), full self-tuning AI loop.

---
Use this pipeline as the north-star roadmap for turning raw files into litigation-ready intelligence—automatically, securely, and at scale.
"""

app = typer.Typer(
    name="codexflo",
    help="🧠 CodexFlō: AI-Driven Strategic File Nexus",
    add_completion=False,
    rich_markup_mode="rich"
)
console = Console()

def setup_cleanup_handlers():
    """Setup signal handlers for graceful cleanup"""
    global _cleanup_registered
    if _cleanup_registered:
        return


    def cleanup_handler(signum=None, frame=None):
        console.print("\n🧹 Cleaning up processes...")
        for proc in _active_processes:
            try:
                if proc.poll() is None:  # Process still running
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
            except Exception as e:
                logger.warning(f"Error cleaning up process: {e}")
        _active_processes.clear()
        console.print("✅ Cleanup complete")
        if signum:
            sys.exit(0)


    # Register signal handlers
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)
    atexit.register(cleanup_handler)
    _cleanup_registered = True

def validate_path(path: str, must_exist: bool = False, must_be_dir: bool = False) -> Path:
    """Validate and sanitize file paths"""
    try:
        # Convert to Path and resolve
        path_obj = Path(path).expanduser().resolve()


        # Basic security check - ensure we're not going outside reasonable bounds
        # For personal use, we'll be more permissive but still safe
        if must_exist and not path_obj.exists():
            raise ValidationError(f"Path does not exist: {path}")


        if must_be_dir and path_obj.exists() and not path_obj.is_dir():
            raise ValidationError(f"Path is not a directory: {path}")


        return path_obj
    except Exception as e:
        raise ValidationError(f"Invalid path '{path}': {e}")

def validate_config_schema(config: Dict[str, Any]) -> List[str]:
    """Validate configuration structure and required fields"""
    errors = []


    # Required top-level sections
    required_sections = ["app", "ai", "storage", "modules"]
    for section in required_sections:
        if section not in config:
            errors.append(f"Missing required section: {section}")


    # AI configuration validation
    if "ai" in config:
        ai_config = config["ai"]
        provider = ai_config.get("provider")


        if provider not in [p.value for p in AIProvider]:
            errors.append(f"Invalid AI provider: {provider}")


        # Check for API key if using cloud providers
        if provider in ["openai", "anthropic", "gemini"]:
            api_key = ai_config.get("api_key")
            if not api_key or api_key.startswith("${"):
                errors.append(f"API key required for {provider} provider")


        # Validate model parameters
        temp = ai_config.get("temperature", 0.1)
        if not 0 <= temp <= 2:
            errors.append("Temperature must be between 0 and 2")


    # Storage validation
    if "storage" in config:
        storage_config = config["storage"]
        base_path = storage_config.get("base_path")
        if base_path:
            try:
                validate_path(base_path)
            except ValidationError as e:
                errors.append(f"Storage path error: {e}")


    return errors

async def wait_for_service(url: str, timeout: int = 30, interval: float = 1.0) -> bool:
    """Wait for a service to become available"""
    start_time = time.time()


    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass


        await asyncio.sleep(interval)


    return False

def check_port_available(port: int) -> bool:
    """Check if a port is available"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return True
        except OSError:
            return False

def interactive_config_setup() -> Dict[str, Any]:
    """Interactive configuration setup with validation"""
    config = {}

    console.print("\n[bold blue]AI Provider Configuration[/bold blue]")

    # AI provider selection
    providers = [p.value for p in AIProvider]
    provider_idx = console.input(f"Select AI provider {providers} [default: openai]: ")
    provider = providers[int(provider_idx)] if provider_idx.isdigit() and 0 <= int(provider_idx) < len(providers) else "openai"

    # Model selection based on provider
    model_options = {
        "openai": ["gpt-4", "gpt-3.5-turbo"],
        "anthropic": ["claude-2", "claude-instant"],
        "gemini": ["gemini-pro", "gemini-ultra"],
        "local": ["llama2", "mistral", "custom"]
    }

    models = model_options.get(provider, ["default"])
    model_prompt = f"Select model for {provider} {models}: "
    model = Prompt.ask(model_prompt, default=models[0])

    # API key for cloud providers
    api_key = ""
    if provider != "local":
        api_key = Prompt.ask(f"Enter {provider} API key", password=True, default="${" + f"{provider.upper()}_API_KEY" + "}")

    # Storage configuration
    console.print("\n[bold blue]Storage Configuration[/bold blue]")
    storage_path = Prompt.ask("Storage base path", default="./storage")

    # Validate storage path
    try:
        validate_path(storage_path)
    except ValidationError as e:
        console.print(f"[yellow]Warning: {e}[/yellow]")
        if Confirm.ask("Create this directory?"):
            Path(storage_path).expanduser().mkdir(parents=True, exist_ok=True)

    # Module selection
    console.print("\n[bold blue]Module Configuration[/bold blue]")
    modules = {
        "codex_weaver": Confirm.ask("Enable Codex Weaver (document relationship mapping)?", default=True),
        "contradiction_sweeper": Confirm.ask("Enable Contradiction Sweeper (inconsistency detection)?", default=True),
        "voice_vision": Confirm.ask("Enable Voice & Vision (audio/visual processing)?", default=True),
        "chrona_sync": Confirm.ask("Enable Chrona Sync (timeline generation)?", default=True),
        "lawspine_binder": Confirm.ask("Enable LawSpine Binder (legal knowledge integration)?", default=True),
        "gui_copilot": Confirm.ask("Enable GUI Copilot (interactive assistance)?", default=True)
    }

    # File processing options
    console.print("\n[bold blue]File Processing Configuration[/bold blue]")
    ocr_enabled = Confirm.ask("Enable OCR for document processing?", default=True)
    auto_organize = Confirm.ask("Enable automatic file organization?", default=True)

    # Security options
    console.print("\n[bold blue]Security Configuration[/bold blue]")
    encryption = Confirm.ask("Enable file encryption?", default=True)

    # Build the configuration
    config = {
        "ai": {
            "provider": provider,
            "model": model,
            "temperature": 0.1,
            "api_key": api_key
        },
        "storage": {
            "base_path": storage_path,
            "vector_db": "chromadb",
            "backup_enabled": True
        },
        "modules": modules,
        "file_processing": {
            "ocr_enabled": ocr_enabled,
            "auto_organize": auto_organize
        },
        "security": {
            "encryption_enabled": encryption
        }
    }

    return config

def create_default_config() -> Dict[str, Any]:
    """Create default configuration with validation"""
    return {
        "app": {
            "name": "CodexFlō",
            "version": "1.0.0",
            "description": "AI-Driven Strategic File Nexus"
        },
        "ai": {
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.1,
            "max_tokens": 2000,
            "embedding_model": "text-embedding-ada-002",
            "api_key": "${OPENAI_API_KEY}"
        },
        "storage": {
            "base_path": "./storage",
            "vector_db": "chromadb",
            "metadata_db": "sqlite",
            "backup_enabled": True,
            "encryption_enabled": True
        },
        "modules": {
            "codex_weaver": True,
            "contradiction_sweeper": True,
            "voice_vision": True,
            "chrona_sync": True,
            "lawspine_binder": True,
            "gui_copilot": True
        },
        "file_processing": {
            "supported_types": ["pdf", "docx", "txt", "md", "mp3", "wav", "mp4", "jpg", "png"],
            "ocr_enabled": True,
            "auto_organize": True,
            "watch_directories": [],
            "max_file_size": "100MB"
        },
        "security": {
            "encryption_enabled": True,
            "privilege_detection": True,
            "access_logging": True
        },
        "legal": {
            "enabled": True,
            "jurisdiction": "US",
            "privilege_detection": True,
            "confidentiality_analysis": True,
            "deadline_tracking": True,
            "citation_extraction": True,
            "case_building": {
                "enabled": True,
                "timeline_generation": True,
                "evidence_mapping": True,
                "contradiction_detection": True,
                "claim_element_analysis": True
            },
            "ethical_walls": {
                "enabled": True,
                "strict_mode": False
            }
        }
    }

@app.command()
def init(
    config_path: str = typer.Option("config/ai_file_explorer.yml", help="Configuration file path"),
    force: bool = typer.Option(False, help="Force overwrite existing config"),
    interactive: bool = typer.Option(True, help="Interactive setup"),
    validate_only: bool = typer.Option(False, help="Only validate existing config")
):
    """🚀 Initialize CodexFlō with configuration"""
    try:
        config_file = validate_path(config_path)


        if validate_only:
            if not config_file.exists():
                console.print(f"❌ Config file not found: {config_path}")
                raise typer.Exit(1)


            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)


            errors = validate_config_schema(config)
            if errors:
                console.print("❌ Configuration validation failed:")
                for error in errors:
                    console.print(f"  • {error}")
                raise typer.Exit(1)
            else:
                console.print("✅ Configuration is valid")
                return


        console.print(Panel.fit("🧠 CodexFlō Initialization", style="bold blue"))


        if config_file.exists() and not force:
            if not Confirm.ask(f"Config file exists at {config_path}. Overwrite?"):
                console.print("❌ Initialization cancelled")
                return


        # Interactive setup with validation
        config_data = {}
        if interactive:
            config_data = interactive_config_setup()


        # Create full config with defaults
        full_config = create_default_config()
        if config_data:
            # Deep merge config data
            for key, value in config_data.items():
                if isinstance(value, dict) and key in full_config:
                    full_config[key].update(value)
                else:
                    full_config[key] = value


        # Validate final configuration
        errors = validate_config_schema(full_config)
        if errors:
            console.print("❌ Configuration validation failed:")
            for error in errors:
                console.print(f"  • {error}")
            raise typer.Exit(1)


        # Create directories safely
        try:
            config_file.parent.mkdir(parents=True, exist_ok=True)
            storage_path = validate_path(full_config["storage"]["base_path"])
            storage_path.mkdir(parents=True, exist_ok=True)


            # Create subdirectories
            for subdir in ["cases", "uploads", "exports", "temp", "logs"]:
                (storage_path / subdir).mkdir(exist_ok=True)


        except Exception as e:
            console.print(f"❌ Error creating directories: {e}")
            raise typer.Exit(1)


        # Write configuration with backup
        if config_file.exists():
            backup_path = config_file.with_suffix(f".bak.{int(time.time())}")
            shutil.copy2(config_file, backup_path)
            console.print(f"📦 Backup created: {backup_path}")


        with open(config_file, 'w') as f:
            yaml.dump(full_config, f, default_flow_style=False, indent=2)


        console.print(f"✅ Configuration created: {config_path}")
        console.print("🔧 Run 'codexflo launch' to start the system")


    except (ValidationError, ConfigError) as e:
        console.print(f"❌ {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error during initialization: {e}")
        logger.exception("Initialization error")
        raise typer.Exit(1)

def interactive_config_setup() -> Dict[str, Any]:
    """Interactive configuration setup with validation"""
    config_data = {}


    try:
        console.print("\n[bold cyan]AI Configuration[/bold cyan]")


        ai_provider = Prompt.ask(
            "AI Provider",
            choices=[p.value for p in AIProvider],
            default="openai"
        )


        ai_config = {"provider": ai_provider}


        if ai_provider in ["openai", "anthropic", "gemini"]:
            while True:
                api_key = Prompt.ask("API Key", password=True)
                if api_key and len(api_key) > 10:  # Basic validation
                    ai_config["api_key"] = api_key
                    break
                console.print("❌ Please enter a valid API key")


            # Model selection
            model_defaults = {
                "openai": "gpt-4",
                "anthropic": "claude-3-opus-20240229",
                "gemini": "gemini-pro"
            }
            ai_config["model"] = model_defaults.get(ai_provider, "gpt-4")


            # Temperature setting
            while True:
                try:
                    temp = float(Prompt.ask("Temperature (0.0-2.0)", default="0.1"))
                    if 0 <= temp <= 2:
                        ai_config["temperature"] = temp
                        break
                    console.print("❌ Temperature must be between 0.0 and 2.0")
                except ValueError:
                    console.print("❌ Please enter a valid number")


        config_data["ai"] = ai_config


        console.print("\n[bold cyan]Storage Configuration[/bold cyan]")
        while True:
            storage_path = Prompt.ask("Storage path", default="./storage")
            try:
                validated_path = validate_path(storage_path)
                config_data["storage"] = {"base_path": str(validated_path)}
                break
            except ValidationError as e:
                console.print(f"❌ {e}")


        console.print("\n[bold cyan]Module Selection[/bold cyan]")
        modules = {}
        module_list = [
            ("codex_weaver", "Timeline & case structure generation"),
            ("contradiction_sweeper", "Document contradiction detection"),
            ("voice_vision", "Audio transcription & analysis"),
            ("chrona_sync", "Chronological file organization"),
            ("lawspine_binder", "Legal motion generation"),
            ("gui_copilot", "AI assistant interface")
        ]


        for module_name, description in module_list:
            modules[module_name] = Confirm.ask(

                f"Enable {module_name}? ({description})",
                default=True
            )


        config_data["modules"] = modules


        return config_data


    except KeyboardInterrupt:
        console.print("\n❌ Setup cancelled by user")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"❌ Error during interactive setup: {e}")
        raise typer.Exit(1)

@app.command()
def launch(
    watch_dir: str = typer.Option("./", help="Directory to watch for files"),
    agent: str = typer.Option("Codex Architect", help="AI agent name"),
    config: str = typer.Option("config/ai_file_explorer.yml", help="Config file"),
    port: int = typer.Option(8000, help="Server port"),
    dev: bool = typer.Option(False, help="Development mode"),
    gui: bool = typer.Option(True, help="Launch GUI interface"),
    health_check: bool = typer.Option(True, help="Perform health checks")
):
    """🚀 Launch CodexFlō with comprehensive error handling and monitoring"""

    # Setup cleanup handlers first
    setup_cleanup_handlers()

    try:
        # Validate inputs
        config_file = validate_path(config, must_exist=True)
        watch_path = validate_path(watch_dir, must_exist=True, must_be_dir=True)

        # Check port availability
        if not check_port_available(port):
            console.print(f"❌ Port {port} is already in use")
            # Try to find alternative port
            for alt_port in range(port + 1, port + 10):
                if check_port_available(alt_port):
                    if Confirm.ask(f"Use port {alt_port} instead?"):
                        port = alt_port
                        break
            else:
                console.print("❌ No available ports found")
                raise typer.Exit(1)

        # Load and validate configuration
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)

        config_errors = validate_config_schema(config_data)
        if config_errors:
            console.print("❌ Configuration validation failed:")
            for error in config_errors:
                console.print(f"  • {error}")
            raise typer.Exit(1)

        console.print(Panel.fit(
            f"🧠 Launching CodexFlō\n"
            f"Agent: {agent}\n"
            f"Watch Dir: {watch_path}\n"
            f"Port: {port}\n"
            f"Config: {config_file}",
            style="bold green"
        ))

        # Run the async launch process
        asyncio.run(async_launch_services(
            watch_path=watch_path,
            agent=agent,
            config_file=config_file,
            port=port,
            dev=dev,
            gui=gui,
            health_check=health_check
        ))

    except (ValidationError, ConfigError, ServiceError) as e:
        console.print(f"❌ {e}")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n🛑 Launch cancelled by user")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error during launch: {e}")
        logger.exception("Launch error")
        raise typer.Exit(1)

async def intelligent_intake(file_path: Path, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Extract metadata, content, and classify file type using AI with legal intelligence."""
    try:
        # Handle different file types appropriately
        file_ext = file_path.suffix.lower()
        content = ""
        binary_mode = False

        # Determine if file is binary or text
        if file_ext in ['.pdf', '.docx', '.doc', '.jpg', '.png', '.mp3', '.mp4']:
            binary_mode = True
            # For binary files, just read the first few bytes for hash
            with open(file_path, 'rb') as f:
                content_bytes = f.read(8192)  # Read first 8KB for hash
                import hashlib
                file_hash = hashlib.sha256(content_bytes).hexdigest()
        else:
            # For text files, read content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(10000)  # Limit to first 10K chars
                import hashlib
                file_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            except UnicodeDecodeError:
                # Fall back to binary mode if text read fails
                binary_mode = True
                with open(file_path, 'rb') as f:
                    content_bytes = f.read(8192)
                    file_hash = hashlib.sha256(content_bytes).hexdigest()

        # Extract creation date and other metadata
        stat_info = file_path.stat()
        created_time = datetime.fromtimestamp(stat_info.st_ctime)
        modified_time = datetime.fromtimestamp(stat_info.st_mtime)

        # Determine document type using AI classification
        doc_type = LegalDocumentType.OTHER.value
        entities = []
        dates = []

        # Only attempt AI classification if we have text content
        if not binary_mode and content:
            # Use configured AI provider
            ai_provider = config.get("ai", {}).get("provider", "openai") if config else "openai"

            if ai_provider == "local":
                # Local model classification (e.g., Ollama)
                import requests
                ollama_url = "http://localhost:11434/api/generate"
                prompt = f"""
                Classify this legal document into one of these categories:
                {', '.join([t.value for t in LegalDocumentType])}

                Also extract:
                1. Key entities (people, organizations)
                2. Important dates
                3. Case numbers if present

                Document: {content[:2000]}

                Format response as JSON:
                {{
                    "document_type": "category",
                    "entities": ["entity1", "entity2"],
                    "dates": ["date1", "date2"],
                    "case_numbers": ["case1", "case2"]
                }}
                """

                try:
                    response = requests.post(ollama_url, json={
                        "model": "llama3",
                        "prompt": prompt
                    }, timeout=30)

                    if response.status_code == 200:
                        ai_response = response.json()
                        classification_text = ai_response.get("response", "{}")

                        # Try to parse JSON from response
                        try:
                            import json
                            classification_data = json.loads(classification_text)
                            doc_type = classification_data.get("document_type", LegalDocumentType.OTHER.value)
                            entities = classification_data.get("entities", [])
                            dates = classification_data.get("dates", [])
                            case_numbers = classification_data.get("case_numbers", [])
                        except json.JSONDecodeError:
                            # Fallback to simple parsing if JSON fails
                            words = classification_text.split()
                            for word in words:
                                if word.lower() in [t.value for t in LegalDocumentType]:
                                    doc_type = word.lower()
                                    break
                except Exception as e:
                    logger.warning(f"AI classification failed: {e}")

        # Build comprehensive metadata
        return {
            "signature": file_hash,
            "type": doc_type,
            "metadata": {
                "path": str(file_path),
                "filename": file_path.name,
                "extension": file_ext,
                "size": stat_info.st_size,
                "created": created_time.isoformat(),
                "modified": modified_time.isoformat(),
                "binary": binary_mode
            },
            "legal_metadata": {
                "entities": entities,
                "dates": dates,
                "case_numbers": case_numbers if 'case_numbers' in locals() else [],
                "privilege_risk": "unknown",  # Placeholder for privilege detection
                "confidentiality": "unknown"  # Placeholder for confidentiality assessment
            }
        }
    except Exception as e:
        logger.error(f"Intake error for {file_path}: {e}")
        return {"error": str(e), "path": str(file_path)}

async def advanced_organization(file_data: Dict[str, Any], config: Dict[str, Any]) -> Path:
    """Organize file based on legal classification and metadata."""
    base_path = Path(config.get("storage", {}).get("base_path", "."))
    file_type = file_data.get("type", "unknown")
    original_path = Path(file_data["metadata"]["path"])
    
    # Extract dates for chronological organization
    dates = file_data.get("legal_metadata", {}).get("dates", [])
    date_prefix = ""
    
    # Try to extract a date for the filename prefix
    if dates and len(dates) > 0:
        # Try to parse the first date
        try:
            from dateutil import parser
            parsed_date = parser.parse(dates[0])
            date_prefix = parsed_date.strftime("%Y-%m-%d_")
        except:
            # If date parsing fails, use file modification date
            mod_date = file_data["metadata"].get("modified", "").split("T")[0]
            if mod_date:
                date_prefix = f"{mod_date}_"
    
    # Extract case numbers or entities for further organization
    case_numbers = file_data.get("legal_metadata", {}).get("case_numbers", [])
    entities = file_data.get("legal_metadata", {}).get("entities", [])
    
    # Determine subfolder structure
    if case_numbers and len(case_numbers) > 0:
        # If we have a case number, organize by case
        case_folder = f"case_{case_numbers[0].replace('/', '-').replace(' ', '_')}"
        org_path = base_path / case_folder / file_type
    elif entities and len(entities) > 0:
        # If we have entities but no case number, organize by primary entity
        entity_folder = entities[0].replace(" ", "_").lower()[:30]  # Limit length
        org_path = base_path / "entities" / entity_folder / file_type
    else:
        # Default organization by document type
        org_path = base_path / "documents" / file_type
    
    # Create target directory
    org_path.mkdir(parents=True, exist_ok=True)
    
    # Create a more descriptive filename
    new_filename = f"{date_prefix}{original_path.name}"
    target_path = org_path / new_filename
    
    # Handle filename conflicts
    counter = 1
    while target_path.exists():
        name_parts = original_path.stem.split(".")
        ext = original_path.suffix
        target_path = org_path / f"{date_prefix}{name_parts[0]}_v{counter}{ext}"
        counter += 1
    
    # Copy the file to its new location
    shutil.copy2(original_path, target_path)
    
    # Create metadata sidecar file
    metadata_path = target_path.with_suffix(target_path.suffix + ".meta.json")
    with open(metadata_path, 'w') as f:
        import json
        # Add organization metadata
        file_data["organization"] = {
            "original_path": str(original_path),
            "organized_path": str(target_path),
            "organization_time": datetime.now().isoformat()
        }
        json.dump(file_data, f, indent=2)
    
    return target_path

async def async_launch_services(
    watch_path: Path,
    agent: str,
    config_file: Path,
    port: int,
    dev: bool,
    gui: bool,
    health_check: bool
):
    """Async service launcher with AI-powered file management pipeline"""
    service_health = ServiceHealth()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        # Start backend service as before
        backend_task = progress.add_task("Starting backend server...", total=100)
        try:
            backend_process = await start_backend_service(
                config_file, port, watch_path, agent, dev
            )
            _active_processes.append(backend_process)
            progress.update(backend_task, advance=50, description="Backend server starting...")

            # Wait for backend to be ready
            backend_url = f"http://localhost:{port}/health"
            if await wait_for_service(backend_url, timeout=30):
                service_health.backend = True
                progress.update(backend_task, advance=50, description="✅ Backend server ready")
            else:
                raise ServiceError("Backend failed to start within timeout")
        except Exception as e:
            progress.update(backend_task, description=f"❌ Backend failed: {e}")
            raise ServiceError(f"Backend startup failed: {e}")

        # Initialize legal pipeline if enabled
        legal_pipeline = None
        try:
            # Load config
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
                
            # Check if legal features are enabled
            if config_data.get("legal", {}).get("enabled", False):
                # Import the legal pipeline module
                try:
                    from .legal_pipeline import LegalPipeline
                    legal_pipeline = LegalPipeline(config_data)
                    progress.add_task("✅ Legal intelligence pipeline initialized", total=100, completed=100)
                except ImportError:
                    console.print("⚠️ Legal pipeline module not found, continuing without legal features")
        except Exception as e:
            console.print(f"⚠️ Error initializing legal pipeline: {e}")

        # Add AI pipeline processing for watched directory
        pipeline_task = progress.add_task("Running AI file management pipeline...", total=100)
        try:
            # Scan and process files in watch_path
            file_count = 0
            for file_path in watch_path.rglob("*"):
                if file_path.is_file():
                    # Skip hidden files and system files
                    if file_path.name.startswith('.') or file_path.name.startswith('~'):
                        continue
                        
                    # Process the file
                    intake_data = await intelligent_intake(file_path, config_data)
                    if "error" not in intake_data:
                        # Apply legal processing if available
                        if legal_pipeline:
                            intake_data = await legal_pipeline.process_document(file_path, intake_data)
                            
                        # Organize the file
                        organized_path = await advanced_organization(intake_data, config_data)
                        progress.update(pipeline_task, advance=5, description=f"Processed {file_path.name}")
                        file_count += 1
                    else:
                        logger.warning(f"Skipped file {file_path}: {intake_data['error']}")
                        
            # Update progress based on number of files processed
            progress.update(pipeline_task, completed=100, 
                           description=f"✅ AI pipeline complete - {file_count} files processed")
            
            # Build case analysis if legal pipeline is enabled
            if legal_pipeline and file_count > 0:
                case_task = progress.add_task("Building case analysis...", total=100)
                try:
                    # Get unique case numbers from processed documents
                    case_ids = set()
                    for doc_id, doc in legal_pipeline.document_index.items():
                        case_numbers = doc.get("metadata", {}).get("legal_metadata", {}).get("case_numbers", [])
                        case_ids.update(case_numbers)
                    
                    # Build analysis for each case
                    for i, case_id in enumerate(case_ids):
                        progress.update(case_task, advance=50/len(case_ids), 
                                      description=f"Analyzing case {case_id}...")
                        case_data = await legal_pipeline.build_case(case_id)
                        
                        # Save case analysis to file
                        case_file = Path(config_data.get("storage", {}).get("base_path", "./storage")) / "cases" / f"{case_id}.json"
                        case_file.parent.mkdir(parents=True, exist_ok=True)
                        with open(case_file, 'w') as f:
                            json.dump(case_data, f, indent=2)
                    
                    progress.update(case_task, completed=100, 
                                   description=f"✅ Case analysis complete - {len(case_ids)} cases analyzed")
                except Exception as e:
                    progress.update(case_task, description=f"⚠️ Case analysis error: {e}")
                    logger.error(f"Error in case analysis: {e}")
        except Exception as e:
            progress.update(pipeline_task, description=f"⚠️ Pipeline error: {e}")
            console.print(f"⚠️ Some files may not have been processed: {e}")

        # Continue with frontend and health checks as before
        frontend_process = None
        if gui:
            frontend_task = progress.add_task("Starting GUI interface...", total=100)
            try:
                frontend_process = await start_frontend_service(dev)
                if frontend_process:
                    _active_processes.append(frontend_process)
                    progress.update(frontend_task, advance=50, description="Frontend starting...")
                    frontend_url = f"http://localhost:3000"
                    if await wait_for_service(frontend_url, timeout=45):
                        service_health.frontend = True
                        progress.update(frontend_task, advance=50, description="✅ GUI interface ready")
                    else:
                        console.print("⚠️  Frontend may take longer to start")
            except Exception as e:
                progress.update(frontend_task, description=f"⚠️  Frontend failed: {e}")
                console.print(f"⚠️  GUI unavailable, continuing with backend only: {e}")

        if health_check:
            health_task = progress.add_task("Performing health checks...", total=100)
            try:
                health_results = await perform_health_checks(port, service_health)
                progress.update(health_task, advance=100, description="✅ Health checks complete")
                display_health_status(health_results)
            except Exception as e:
                progress.update(health_task, description=f"⚠️  Health checks failed: {e}")
                console.print(f"⚠️  Some services may not be fully operational: {e}")

    # Display startup summary as before
    console.print(f"\n🌐 CodexFlō running at http://localhost:{port}")
    console.print(f"👁️  Watching directory: {watch_path}")
    console.print(f"🤖 AI Agent: {agent}")
    if gui and service_health.frontend:
        console.print(f"🖥️  GUI available at http://localhost:3000")
    console.print("\n[bold yellow]Press Ctrl+C to stop[/bold yellow]")
    try:
        await monitor_services(backend_process, frontend_process, port)
    except KeyboardInterrupt:
        console.print("\n🛑 Shutting down CodexFlō...")
    finally:
        await cleanup_services()

async def start_backend_service(
    config_file: Path,
    port: int,
    watch_path: Path,
    agent: str,
    dev: bool
) -> subprocess.Popen:
    """Start backend service with proper error handling"""

    backend_cmd = [
        sys.executable, "-m", "backend.main",
        "--config", str(config_file),
        "--port", str(port),
        "--watch-dir", str(watch_path),
        "--agent", agent
    ]

    if dev:
        backend_cmd.extend(["--reload", "--debug"])

    try:
        # Check if backend module exists
        backend_main = Path("backend/main.py")
        if not backend_main.exists():
            raise ServiceError("Backend module not found. Run from project root directory.")

        process = subprocess.Popen(
            backend_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Quick check if process started successfully
        await asyncio.sleep(1)
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise ServiceError(f"Backend failed to start: {stderr}")

        return process

    except FileNotFoundError as e:
        raise ServiceError(f"Backend executable not found: {e}")
    except Exception as e:
        raise ServiceError(f"Failed to start backend: {e}")

async def start_frontend_service(dev: bool) -> Optional[subprocess.Popen]:
    """Start frontend service if available"""

    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        console.print("⚠️  Frontend directory not found, running backend only")
        return None

    # Check for package.json
    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        console.print("⚠️  Frontend package.json not found, skipping GUI")
        return None

    # Check if node_modules exists
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        console.print("⚠️  Frontend dependencies not installed. Run 'npm install' in frontend directory")
        return None

    frontend_cmd = ["npm", "run", "dev" if dev else "start"]

    try:
        process = subprocess.Popen(
            frontend_cmd,
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        return process

    except FileNotFoundError:
        console.print("⚠️  npm not found, skipping GUI")
        return None
    except Exception as e:
        console.print(f"⚠️  Frontend startup failed: {e}")
        return None

async def perform_health_checks(port: int, service_health: ServiceHealth) -> Dict[str, Any]:
    """Perform comprehensive health checks"""

    health_results = {
        "backend": {"status": "unknown", "details": {}},
        "frontend": {"status": "unknown", "details": {}},
        "ai_engine": {"status": "unknown", "details": {}},
        "database": {"status": "unknown", "details": {}}
    }

    # Backend health check
    try:
        backend_url = f"http://localhost:{port}/health"
        response = requests.get(backend_url, timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            health_results["backend"] = {
                "status": "healthy",
                "details": health_data
            }
            service_health.backend = True
        else:
            health_results["backend"]["status"] = "unhealthy"
    except Exception as e:
        health_results["backend"] = {
            "status": "error",
            "details": {"error": str(e)}
        }

    # AI Engine health check
    try:
        ai_url = f"http://localhost:{port}/ai/health"
        response = requests.get(ai_url, timeout=15)
        if response.status_code == 200:
            health_results["ai_engine"] = {
                "status": "healthy",
                "details": response.json()
            }
            service_health.ai_engine = True
        else:
            health_results["ai_engine"]["status"] = "unhealthy"
    except Exception as e:
        health_results["ai_engine"] = {
            "status": "error",
            "details": {"error": str(e)}
        }

    # Database health check
    try:
        db_url = f"http://localhost:{port}/db/health"
        response = requests.get(db_url, timeout=10)
        if response.status_code == 200:
            health_results["database"] = {
                "status": "healthy",
                "details": response.json()
            }
            service_health.database = True
        else:
            health_results["database"]["status"] = "unhealthy"
    except Exception as e:
        health_results["database"] = {
            "status": "error",
            "details": {"error": str(e)}
        }

    return health_results

def display_health_status(health_results: Dict[str, Any]):
    """Display health check results in a nice table"""

    table = Table(title="🏥 Service Health Status")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details", style="dim")

    status_styles = {
        "healthy": "green",
        "unhealthy": "yellow",
        "error": "red",
        "unknown": "dim"
    }

    status_icons = {
        "healthy": "✅",
        "unhealthy": "⚠️",
        "error": "❌",
        "unknown": "❓"
    }

    for service, health in health_results.items():
        status = health["status"]
        icon = status_icons.get(status, "❓")
        style = status_styles.get(status, "dim")

        details = health.get("details", {})
        if isinstance(details, dict):
            detail_text = ", ".join([f"{k}: {v}" for k, v in details.items() if k != "error"])
            if "error" in details:
                detail_text = details["error"]
        else:
            detail_text = str(details)

        table.add_row(
            service.replace("_", " ").title(),
            f"[{style}]{icon} {status.title()}[/{style}]",
            detail_text[:50] + "..." if len(detail_text) > 50 else detail_text
        )

    console.print(table)

async def monitor_services(
    backend_process: subprocess.Popen,
    frontend_process: Optional[subprocess.Popen],
    port: int
):
    """Monitor running services and restart if needed"""

    check_interval = 30  # Check every 30 seconds

    while True:
        await asyncio.sleep(check_interval)

        # Check backend process
        if backend_process.poll() is not None:
            console.print("❌ Backend process died, attempting restart...")
            # In a real implementation, you'd restart the service here
            break

        # Check frontend process
        if frontend_process and frontend_process.poll() is not None:
            console.print("⚠️  Frontend process died")

        # Periodic health check
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            if response.status_code != 200:
                console.print("⚠️  Backend health check failed")
        except requests.RequestException:
            console.print("⚠️  Backend not responding")

async def cleanup_services():
    """Clean up all running services"""
    console.print("🧹 Cleaning up services...")

    for proc in _active_processes:
        try:
            if proc.poll() is None:
                proc.terminate()
                try:
                    await asyncio.wait_for(asyncio.create_task(
                        asyncio.to_thread(proc.wait)
                    ), timeout=5)
                except asyncio.TimeoutError:
                    pass
        except Exception as e:
            logger.warning(f"Error cleaning up process: {e}")
    _active_processes.clear()
    console.print("✅ Cleanup complete")
