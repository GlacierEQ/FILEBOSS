#!/usr/bin/env python3
"""
CodexFlō Integrated System - Seamless Legal Intelligence Platform
Complete integration of all components for unified operation
"""

import asyncio
import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
import yaml
import json
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

# Import all our components
from .codexflo_cli import (
    app, console, setup_cleanup_handlers, validate_path,
    validate_config_schema, create_default_config
)
from .pipeline_prompt import get_pipeline_instructions, get_processing_prompt
from .enhanced_pipeline import (
    LegalIntelligenceEngine, QualityAssuranceEngine,
    SecurityComplianceEngine, DocumentMetadata
)

logger = logging.getLogger(__name__)

class IntegratedCodexFlowSystem:
    """Main system orchestrator for seamless operation"""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = {}
        self.legal_engine = None
        self.qa_engine = None
        self.security_engine = None
        self.active_modules = {}
        self.system_status = {
            'initialized': False,
            'services_running': False,
            'ai_ready': False,
            'modules_loaded': False
        }

    async def initialize_system(self) -> bool:
        """Complete system initialization with all components"""
        try:
            console.print(Panel.fit("🧠 Initializing CodexFlō Integrated System", style="bold blue"))

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=console
            ) as progress:

                # Step 1: Load and validate configuration
                config_task = progress.add_task("Loading configuration...", total=100)
                await self._load_configuration()
                progress.update(config_task, advance=100, description="✅ Configuration loaded")

                # Step 2: Initialize AI engines
                ai_task = progress.add_task("Initializing AI engines...", total=100)
                await self._initialize_ai_engines()
                progress.update(ai_task, advance=100, description="✅ AI engines ready")

                # Step 3: Load active modules
                modules_task = progress.add_task("Loading modules...", total=100)
                await self._load_modules()
                progress.update(modules_task, advance=100, description="✅ Modules loaded")

                # Step 4: Setup security and compliance
                security_task = progress.add_task("Setting up security...", total=100)
                await self._setup_security()
                progress.update(security_task, advance=100, description="✅ Security configured")

                # Step 5: Verify system integrity
                verify_task = progress.add_task("Verifying system integrity...", total=100)
                await self._verify_system_integrity()
                progress.update(verify_task, advance=100, description="✅ System verified")

            self.system_status['initialized'] = True
            console.print("🎉 CodexFlō system successfully initialized!")
            return True

        except Exception as e:
            console.print(f"❌ System initialization failed: {e}")
            logger.exception("System initialization error")
            return False

    async def process_file_pipeline(self, file_path: Path) -> Dict[str, Any]:
        """Complete file processing pipeline with all intelligence layers"""

        pipeline_result = {
            'success': False,
            'metadata': None,
            'organized_path': None,
            'qa_results': None,
            'security_clearance': None,
            'module_outputs': {},
            'processing_time': 0
        }

        start_time = datetime.now()

        try:
            console.print(f"🔄 Processing file: {file_path.name}")

            # Step 1: Legal Intelligence Processing
            console.print("  📋 Extracting legal intelligence...")
            metadata = await self.legal_engine.process_document(file_path)
            pipeline_result['metadata'] = metadata

            # Step 2: Quality Assurance
            console.print("  🔍 Running quality assurance...")
            qa_results = await self.qa_engine.validate_processing(metadata)
            pipeline_result['qa_results'] = qa_results

            # Step 3: Security Clearance
            console.print("  🔒 Security compliance check...")
            security_clearance = await self.security_engine.validate_security(metadata)
            pipeline_result['security_clearance'] = security_clearance

            # Step 4: Intelligent Organization
            console.print("  📁 Organizing document...")
            organized_path = await self.legal_engine.organize_document(metadata)
            pipeline_result['organized_path'] = organized_path

            # Step 5: Module-Specific Processing
            console.print("  🧩 Running specialized modules...")
            module_outputs = await self._run_active_modules(metadata)
            pipeline_result['module_outputs'] = module_outputs

            # Step 6: Update System Knowledge
            await self._update_system_knowledge(metadata, module_outputs)

            processing_time = (datetime.now() - start_time).total_seconds()
            pipeline_result['processing_time'] = processing_time
            pipeline_result['success'] = True

            console.print(f"  ✅ File processed successfully in {processing_time:.2f}s")

        except Exception as e:
            console.print(f"  ❌ Processing failed: {e}")
            logger.exception(f"File processing error for {file_path}")
            pipeline_result['error'] = str(e)

        return pipeline_result

    async def build_comprehensive_case(self, case_id: str) -> Dict[str, Any]:
        """Build complete case with all available intelligence"""

        console.print(f"🏗️ Building comprehensive case: {case_id}")

        case_build = {
            'case_id': case_id,
            'timeline': None,
            'claim_matrix': None,
            'contradictions': [],
            'evidence_gaps': [],
            'strategic_recommendations': [],
            'motion_drafts': {},
            'compliance_status': {}
        }

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:

                # Build timeline
                timeline_task = progress.add_task("Building case timeline...", total=100)
                timeline = await self.legal_engine.build_case_timeline(case_id)
                case_build['timeline'] = timeline
                progress.update(timeline_task, advance=100, description="✅ Timeline complete")

                # Generate claim matrix
                claims_task = progress.add_task("Analyzing claims and evidence...", total=100)
                # Get primary legal theory from case
                legal_theory = await self._identify_primary_legal_theory(case_id)
                claim_matrix = await self.legal_engine.generate_claim_matrix(case_id, legal_theory)
                case_build['claim_matrix'] = claim_matrix
                progress.update(claims_task, advance=100, description="✅ Claims analysis complete")

                # Detect contradictions
                contradictions_task = progress.add_task("Detecting contradictions...", total=100)
                case_docs = self._get_case_documents(case_id)
                contradictions = await self.legal_engine.detect_contradictions(case_docs)
                case_build['contradictions'] = contradictions
                progress.update(contradictions_task, advance=100, description="✅ Contradiction analysis complete")

                # Generate strategic recommendations
                strategy_task = progress.add_task("Generating strategy recommendations...", total=100)
                recommendations = await self._generate_strategic_recommendations(case_build)
                case_build['strategic_recommendations'] = recommendations
                progress.update(strategy_task, advance=100, description="✅ Strategy recommendations ready")

                # Compliance check
                compliance_task = progress.add_task("Checking compliance status...", total=100)
                compliance = await self.security_engine.check_case_compliance(case_id)
                case_build['compliance_status'] = compliance
                progress.update(compliance_task, advance=100, description="✅ Compliance verified")

            console.print("🎯 Comprehensive case build complete!")

        except Exception as e:
            console.print(f"❌ Case building failed: {e}")
            logger.exception(f"Case building error for {case_id}")
            case_build['error'] = str(e)

        return case_build

    async def start_intelligent_monitoring(self, watch_directories: List[Path]) -> None:
        """Start intelligent file monitoring with real-time processing"""

        console.print("👁️ Starting intelligent file monitoring...")

        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        class IntelligentFileHandler(FileSystemEventHandler):
            def __init__(self, system_instance):
                self.system = system_instance

            async def on_created(self, event):
                if not event.is_directory:
                    file_path = Path(event.src_path)
                    await self.system.process_file_pipeline(file_path)

            async def on_modified(self, event):
                if not event.is_directory:
                    file_path = Path(event.src_path)
                    # Check if significant modification
                    if await self._is_significant_modification(file_path):
                        await self.system.process_file_pipeline(file_path)

        observer = Observer()
        handler = IntelligentFileHandler(self)

        for watch_dir in watch_directories:
            observer.schedule(handler, str(watch_dir), recursive=True)
            console.print(f"  📂 Monitoring: {watch_dir}")

        observer.start()
        console.print("✅ Intelligent monitoring active")

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            console.print("🛑 Monitoring stopped")

        observer.join()

    # Private helper methods

    async def _load_configuration(self) -> None:
        """Load and validate system configuration"""
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Validate configuration
        errors = validate_config_schema(self.config)
        if errors:
            raise Exception(f"Configuration validation failed: {errors}")

    async def _initialize_ai_engines(self) -> None:
        """Initialize all AI processing engines"""
        self.legal_engine = LegalIntelligenceEngine(self.config)
        self.qa_engine = QualityAssuranceEngine(self.config)
        self.security_engine = SecurityComplianceEngine(self.config)

        # Initialize AI models and knowledge bases
        await self.legal_engine.initialize()
        await self.qa_engine.initialize()
        await self.security_engine.initialize()

        self.system_status['ai_ready'] = True

    async def _load_modules(self) -> None:
        """Load and initialize active modules"""
        module_config = self.config.get('modules', {})

        if module_config.get('codex_weaver'):
            self.active_modules['codex_weaver'] = await self._load_codex_weaver()

        if module_config.get('contradiction_sweeper'):
            self.active_modules['contradiction_sweeper'] = await self._load_contradiction_sweeper()

        if module_config.get('voice_vision'):
            self.active_modules['voice_vision'] = await self._load_voice_vision()

        if module_config.get('chrona_sync'):
            self.active_modules['chrona_sync'] = await self._load_chrona_sync()

        if module_config.get('lawspine_binder'):
            self.active_modules['lawspine_binder'] = await self._load_lawspine_binder()

        if module_config.get('gui_copilot'):
            self.active_modules['gui_copilot'] = await self._load_gui_copilot()

        self.system_status['modules_loaded'] = True

    async def _setup_security(self) -> None:
        """Setup security and compliance systems"""
        await self.security_engine.setup_access_controls()
        await self.security_engine.initialize_audit_logging()
        await self.security_engine.setup_ethical_walls()

    async def _verify_system_integrity(self) -> None:
        """Verify all system components are working correctly"""
        # Test AI engines
        test_result = await self.legal_engine.self_test()
        if not test_result['success']:
            raise Exception(f"Legal engine self-test failed: {test_result['error']}")

        # Test modules
        for module_name, module in self.active_modules.items():
            test_result = await module.self_test()
            if not test_result['success']:
                console.print(f"⚠️ Module {module_name} self-test failed: {test_result['error']}")

    async def _run_active_modules(self, metadata: DocumentMetadata) -> Dict[str, Any]:
        """Run all active modules on the processed document"""
        module_outputs = {}

        for module_name, module in self.active_modules.items():
            try:
                output = await module.process_document(metadata)
                module_outputs[module_name] = output
            except Exception as e:
                logger.warning(f"Module {module_name} processing failed: {e}")
                module_outputs[module_name] = {'error': str(e)}

        return module_outputs

# Enhanced CLI commands for integrated system

@app.command()
def integrated_launch(
    config: str = typer.Option("config/ai_file_explorer.yml", help="Config file"),
    watch_dirs: List[str] = typer.Option(["./"], help="Directories to monitor"),
    case_id: Optional[str] = typer.Option(None, help="Specific case to build"),
    auto_build: bool = typer.Option(True, help="Auto-build cases as files are processed")
):
    """🚀 Launch integrated CodexFlō system with full intelligence pipeline"""

    async def run_integrated_system():
        # Setup cleanup handlers
        setup_cleanup_handlers()

        # Initialize system
        config_path = validate_path(config, must_exist=True)
        system = IntegratedCodexFlowSystem(config_path)

        if not await system.initialize_system():
            console.print("❌ System initialization failed")
            return

        # Process specific case if requested
        if case_id:
            case_result = await system.build_comprehensive_case(case_id)
            console.print(f"📊 Case build result: {case_result}")

        # Start monitoring if watch directories specified
        if watch_dirs:
            watch_paths = [validate_path(d, must_exist=True, must_be_dir=True) for d in watch_dirs]
            await system.start_intelligent_monitoring(watch_paths)

    try:
