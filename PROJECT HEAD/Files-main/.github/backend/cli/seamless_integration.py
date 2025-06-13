#!/usr/bin/env python3
"""
CodexFlō Seamless Integration System
Complete unified operation with all components working together
"""

import asyncio
import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.tree import Tree
import yaml
import json
from typing import Dict, Any, List, Optional, Union
import logging
from datetime import datetime
import subprocess
import sys
import os

# Import all components for unified operation
from .codexflo_cli import (
    app, console, setup_cleanup_handlers, validate_path,
    validate_config_schema, create_default_config, _active_processes
)
from .pipeline_prompt import CODEXFLO_PIPELINE_PROMPT, get_pipeline_instructions
from .enhanced_pipeline import (
    LegalIntelligenceEngine, QualityAssuranceEngine,
    SecurityComplianceEngine, DocumentMetadata, DocumentType
)

logger = logging.getLogger(__name__)

class SeamlessCodexFlowOrchestrator:
    """Master orchestrator for seamless system operation"""

    def __init__(self):
        self.config = {}
        self.system_components = {}
        self.active_services = {}
        self.monitoring_tasks = []
        self.health_status = {
            'backend': False,
            'frontend': False,
            'ai_engines': False,
            'modules': False,
            'monitoring': False
        }

    async def initialize_complete_system(self, config_path: Path) -> bool:
        """Initialize all system components for seamless operation"""

        console.print(Panel.fit(
            "🧠 CodexFlō Complete System Initialization\n"
            "Integrating all components for seamless operation",
            style="bold blue"
        ))

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=console
            ) as progress:

                # Phase 1: Core System Setup
                core_task = progress.add_task("Setting up core system...", total=100)
                await self._setup_core_system(config_path)
                progress.update(core_task, advance=100, description="✅ Core system ready")

                # Phase 2: AI Intelligence Engines
                ai_task = progress.add_task("Initializing AI engines...", total=100)
                await self._initialize_ai_engines()
                progress.update(ai_task, advance=100, description="✅ AI engines online")

                # Phase 3: Specialized Modules
                modules_task = progress.add_task("Loading specialized modules...", total=100)
                await self._load_specialized_modules()
                progress.update(modules_task, advance=100, description="✅ Modules loaded")

                # Phase 4: Backend Services
                backend_task = progress.add_task("Starting backend services...", total=100)
                await self._start_backend_services()
                progress.update(backend_task, advance=100, description="✅ Backend services running")

                # Phase 5: Frontend Interface
                frontend_task = progress.add_task("Launching frontend interface...", total=100)
                await self._start_frontend_interface()
                progress.update(frontend_task, advance=100, description="✅ Frontend interface ready")

                # Phase 6: Monitoring & Health Checks
                monitor_task = progress.add_task("Setting up monitoring...", total=100)
                await self._setup_monitoring_system()
                progress.update(monitor_task, advance=100, description="✅ Monitoring active")

                # Phase 7: Integration Verification
                verify_task = progress.add_task("Verifying integration...", total=100)
                await self._verify_seamless_integration()
                progress.update(verify_task, advance=100, description="✅ Integration verified")

            await self._display_system_status()
            return True

        except Exception as e:
            console.print(f"❌ System initialization failed: {e}")
            logger.exception("Complete system initialization error")
            return False

    async def run_seamless_pipeline(self, file_path: Path) -> Dict[str, Any]:
        """Execute complete processing pipeline seamlessly"""

        pipeline_start = datetime.now()

        console.print(f"\n🔄 Processing: {file_path.name}")
        console.print("=" * 60)

        pipeline_result = {
            'file_path': str(file_path),
            'processing_stages': {},
            'final_status': 'pending',
            'total_time': 0,
            'outputs': {}
        }

        try:
            # Stage 1: Intelligent Intake
            console.print("📥 Stage 1: Intelligent Document Intake")
            intake_result = await self._intelligent_intake_stage(file_path)
            pipeline_result['processing_stages']['intake'] = intake_result
            console.print(f"   ✅ Document classified as: {intake_result.get('type', 'unknown')}")

            # Stage 2: Legal Intelligence Analysis
            console.print("🧠 Stage 2: Legal Intelligence Analysis")
            analysis_result = await self._legal_analysis_stage(file_path, intake_result)
            pipeline_result['processing_stages']['analysis'] = analysis_result
            console.print(f"   ✅ Extracted {len(analysis_result.get('entities', []))} entities")

            # Stage 3: Quality Assurance
            console.print("🔍 Stage 3: Quality Assurance & Validation")
            qa_result = await self._quality_assurance_stage(analysis_result)
            pipeline_result['processing_stages']['qa'] = qa_result
            console.print(f"   ✅ Quality score: {qa_result.get('score', 0):.2f}")

            # Stage 4: Security & Compliance
            console.print("🔒 Stage 4: Security & Compliance Check")
            security_result = await self._security_compliance_stage(analysis_result)
            pipeline_result['processing_stages']['security'] = security_result
            console.print(f"   ✅ Security clearance: {security_result.get('clearance', 'pending')}")

            # Stage 5: Intelligent Organization
            console.print("📁 Stage 5: Intelligent Organization")
            org_result = await self._intelligent_organization_stage(file_path, analysis_result)
            pipeline_result['processing_stages']['organization'] = org_result
            console.print(f"   ✅ Organized to: {org_result.get('new_path', 'unknown')}")

            # Stage 6: Module Processing
            console.print("🧩 Stage 6: Specialized Module Processing")
            module_results = await self._module_processing_stage(analysis_result)
            pipeline_result['processing_stages']['modules'] = module_results
            console.print(f"   ✅ Processed by {len(module_results)} modules")

            # Stage 7: Case Integration
            console.print("🏗️ Stage 7: Case Integration & Building")
            case_result = await self._case_integration_stage(analysis_result, module_results)
            pipeline_result['processing_stages']['case_integration'] = case_result
            console.print(f"   ✅ Integrated into case: {case_result.get('case_id', 'new')}")

            # Stage 8: Knowledge Update
            console.print("📚 Stage 8: Knowledge Base Update")
            knowledge_result = await self._knowledge_update_stage(pipeline_result)
            pipeline_result['processing_stages']['knowledge'] = knowledge_result
            console.print("   ✅ Knowledge base updated")

            # Finalize pipeline
            total_time = (datetime.now() - pipeline_start).total_seconds()
            pipeline_result['total_time'] = total_time
            pipeline_result['final_status'] = 'completed'

            console.print(f"\n🎉 Pipeline completed successfully in {total_time:.2f}s")

        except Exception as e:
            pipeline_result['final_status'] = 'failed'
            pipeline_result['error'] = str(e)
            console.print(f"\n❌ Pipeline failed: {e}")
            logger.exception(f"Pipeline error for {file_path}")

        return pipeline_result

    async def monitor_seamless_operation(self) -> None:
        """Continuous monitoring for seamless operation"""

        console.print("👁️ Starting seamless operation monitoring...")

        monitoring_tasks = [
            asyncio.create_task(self._monitor_system_health()),
            asyncio.create_task(self._monitor_file_processing()),
            asyncio.create_task(self._monitor_case_building()),
            asyncio.create_task(self._monitor_performance_metrics())
        ]

        try:
            await asyncio.gather(*monitoring_tasks)
        except KeyboardInterrupt:
            console.print("\n🛑 Stopping monitoring...")
            for task in monitoring_tasks:
                task.cancel()

    # Core System Setup Methods

    async def _setup_core_system(self, config_path: Path) -> None:
        """Setup core system configuration and validation"""

        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Validate configuration
        errors = validate_config_schema(self.config)
        if errors:
            raise Exception(f"Configuration validation failed: {errors}")

        # Setup cleanup handlers
        setup_cleanup_handlers()

        # Initialize storage directories
        storage_path = Path(self.config['storage']['base_path'])
        for subdir in ['cases', 'uploads', 'exports', 'temp', 'logs', 'knowledge_base']:
            (storage_path / subdir).mkdir(parents=True, exist_ok=True)

    async def _initialize_ai_engines(self) -> None:
        """Initialize all AI processing engines"""

        # Legal Intelligence Engine
        self.system_components['legal_engine'] = LegalIntelligenceEngine(self.config)
        await self.system_components['legal_engine'].initialize()

        # Quality Assurance Engine
        self.system_components['qa_engine'] = QualityAssuranceEngine(self.config)
        await self.system_components['qa_engine'].initialize()

        # Security & Compliance Engine
        self.system_components['security_engine'] = SecurityComplianceEngine(self.config)
        await self.system_components['security_engine'].initialize()

        self.health_status['ai_engines'] = True

    async def _load_specialized_modules(self) -> None:
        """Load all specialized processing modules"""

        modules_config = self.config.get('modules', {})
        loaded_modules = {}

        # Codex Weaver - Timeline & Structure
        if modules_config.get('codex_weaver', True):
            loaded_modules['codex_weaver'] = await self._initialize_codex_weaver()

        # Contradiction Sweeper - Inconsistency Detection
        if modules_config.get('contradiction_sweeper', True):
            loaded_modules['contradiction_sweeper'] = await self._initialize_contradiction_sweeper()

        # Voice Vision - Multimedia Processing
        if modules_config.get('voice_vision', True):
            loaded_modules['voice_vision'] = await self._initialize_voice_vision()

        # Chrona Sync - Chronological Organization
        if modules_config.get('chrona_sync', True):
            loaded_modules['chrona_sync'] = await self._initialize_chrona_sync()

        # LawSpine Binder - Legal Motion Generation
        if modules_config.get('lawspine_binder', True):
            loaded_modules['lawspine_binder'] = await self._initialize_lawspine_binder()

        # GUI Copilot - Interface Assistant
        if modules_config.get('gui_copilot', True):
            loaded_modules['gui_copilot'] = await self._initialize_gui_copilot()

        self.system_components['modules'] = loaded_modules
        self.health_status['modules'] = True

    async def _start_backend_services(self) -> None:
        """Start all backend services"""

        port = self.config.get('server', {}).get('port', 8000)

        # Start main backend API
        backend_cmd = [
            sys.executable, "-m", "backend.main",
            "--config", str(self.config),
            "--port", str(port)
        ]

        backend_process = subprocess.Popen(
            backend_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        _active_processes.append(backend_process)
        self.active_services['backend'] = backend_process

        # Wait for backend to be ready
        await self._wait_for_service(f"http://localhost:{port}/health", timeout=30)
        self.health_status['backend'] = True

    async def _start_frontend_interface(self) -> None:
        """Start frontend interface if available"""

        frontend_dir = Path("frontend")
        if frontend_dir.exists():
            frontend_cmd = ["npm", "run", "dev"]

            try:
                frontend_process = subprocess.Popen(
                    frontend_cmd,
                    cwd=frontend_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                _active_processes.append(frontend_process)
                self.active_services['frontend'] = frontend_process

                # Wait for frontend to be ready
                await self._wait_for_service("http://localhost:3000", timeout=45)
                self.health_status['frontend'] = True

            except Exception as e:
                console.print(f"⚠️ Frontend not available: {e}")

    async def _setup_monitoring_system(self) -> None:
        """Setup comprehensive monitoring system"""

        # File system monitoring
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        class SeamlessFileHandler(FileSystemEventHandler):
            def __init__(self, orchestrator):
                self.orchestrator = orchestrator

            def on_created(self, event):
                if not event.is_directory:
                    asyncio.create_task(
                        self.orchestrator.run_seamless_pipeline(Path(event.src_path))
                    )

        self.file_observer = Observer()
        handler = SeamlessFileHandler(self)

        # Monitor configured directories
        watch_dirs = self.config.get('file_processing', {}).get('watch_directories', ['./'])
        for watch_dir in watch_dirs:
            self.file_observer.schedule(handler, watch_dir, recursive=True)

        self.file_observer.start()
        self.health_status['monitoring'] = True

    # Pipeline Stage Methods

    async def _intelligent_intake_stage(self, file_path: Path) -> Dict[str, Any]:
        """Stage 1: Intelligent document intake and classification"""

        legal_engine = self.system_components['legal_engine']

        # Extract content and metadata
        content = await legal_engine._extract_content(file_path)
        signature = legal_engine._generate_
