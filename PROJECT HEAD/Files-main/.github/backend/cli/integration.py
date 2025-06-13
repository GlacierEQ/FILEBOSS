#!/usr/bin/env python3
"""
CodexFlō Integration Module
Connects all components of the legal intelligence pipeline for seamless operation
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import importlib
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodexFloIntegration:
    """Main integration class for CodexFlō components"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the integration with configuration"""
        self.config = config
        self.components = {}
        self.pipeline_modules = {}
        self.initialized = False
    
    async def initialize(self) -> bool:
        """Initialize all components and verify connections"""
        try:
            # 1. Import required modules
            await self._import_modules()
            
            # 2. Initialize legal pipeline
            if self.config.get("legal", {}).get("enabled", False):
                legal_pipeline = await self._init_legal_pipeline()
                if legal_pipeline:
                    self.components["legal_pipeline"] = legal_pipeline
            
            # 3. Initialize security components
            if self.config.get("security", {}).get("encryption_enabled", False):
                security_engine = await self._init_security_engine()
                if security_engine:
                    self.components["security_engine"] = security_engine
            
            # 4. Initialize AI components
            ai_engine = await self._init_ai_engine()
            if ai_engine:
                self.components["ai_engine"] = ai_engine
            
            # 5. Initialize storage components
            storage_manager = await self._init_storage_manager()
            if storage_manager:
                self.components["storage_manager"] = storage_manager
            
            # 6. Verify connections between components
            if await self._verify_connections():
                self.initialized = True
                logger.info("CodexFlō integration initialized successfully")
                return True
            else:
                logger.error("Failed to verify component connections")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing CodexFlō integration: {e}")
            return False
    
    async def process_file(self, file_path: Path) -> Dict[str, Any]:
        """Process a file through the integrated pipeline"""
        if not self.initialized:
            return {"error": "Integration not initialized"}
        
        try:
            result = {"file": str(file_path), "status": "processing"}
            
            # 1. File intake with AI classification
            if "ai_engine" in self.components:
                intake_result = await self.components["ai_engine"].process_file(file_path)
                result["classification"] = intake_result.get("classification", "unknown")
                result["metadata"] = intake_result.get("metadata", {})
            
            # 2. Legal processing if enabled
            if "legal_pipeline" in self.components:
                legal_result = await self.components["legal_pipeline"].process_document(
                    file_path, result.get("metadata", {})
                )
                result["legal_metadata"] = legal_result
            
            # 3. Security processing
            if "security_engine" in self.components:
                security_result = await self.components["security_engine"].process_document(file_path)
                result["security"] = security_result
            
            # 4. Storage organization
            if "storage_manager" in self.components:
                storage_result = await self.components["storage_manager"].organize_file(
                    file_path, result.get("metadata", {}), result.get("legal_metadata", {})
                )
                result["storage"] = storage_result
            
            result["status"] = "completed"
            return result
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return {"file": str(file_path), "status": "error", "error": str(e)}
    
    async def build_case(self, case_id: str) -> Dict[str, Any]:
        """Build a case using the legal pipeline"""
        if not self.initialized:
            return {"error": "Integration not initialized"}
        
        if "legal_pipeline" not in self.components:
            return {"error": "Legal pipeline not enabled"}
        
        try:
            # Build case using legal pipeline
            case_data = await self.components["legal_pipeline"].build_case(case_id)
            
            # Enhance with AI insights if available
            if "ai_engine" in self.components:
                ai_insights = await self.components["ai_engine"].analyze_case(case_data)
                case_data["ai_insights"] = ai_insights
            
            return case_data
            
        except Exception as e:
            logger.error(f"Error building case {case_id}: {e}")
            return {"case_id": case_id, "status": "error", "error": str(e)}
    
    async def generate_report(self, report_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate reports using the appropriate components"""
        if not self.initialized:
            return {"error": "Integration not initialized"}
        
        try:
            if report_type == "case_summary" and "legal_pipeline" in self.components:
                return await self.components["legal_pipeline"].generate_case_summary(
                    params.get("case_id", ""), params.get("format", "json")
                )
            elif report_type == "security_audit" and "security_engine" in self.components:
                return await self.components["security_engine"].generate_audit_report(
                    params.get("start_date", ""), params.get("end_date", "")
                )
            elif report_type == "storage_usage" and "storage_manager" in self.components:
                return await self.components["storage_manager"].generate_usage_report()
            else:
                return {"error": f"Unknown report type: {report_type}"}
                
        except Exception as e:
            logger.error(f"Error generating {report_type} report: {e}")
            return {"report_type": report_type, "status": "error", "error": str(e)}
    
    # Private helper methods
    
    async def _import_modules(self) -> None:
        """Import required modules dynamically"""
        try:
            # Add parent directory to path if needed
            parent_dir = str(Path(__file__).parent.parent)
            if parent_dir not in sys.path:
                sys.path.append(parent_dir)
            
            # Import modules
            from cli.legal_pipeline import LegalPipeline
            self.pipeline_modules["legal_pipeline"] = LegalPipeline
            
            # Import other modules as needed
            logger.info("Successfully imported required modules")
            
        except ImportError as e:
            logger.error(f"Error importing modules: {e}")
            raise
    
    async def _init_legal_pipeline(self) -> Any:
        """Initialize the legal pipeline"""
        try:
            if "legal_pipeline" in self.pipeline_modules:
                return self.pipeline_modules["legal_pipeline"](self.config)
            return None
        except Exception as e:
            logger.error(f"Error initializing legal pipeline: {e}")
            return None
    
    async def _init_security_engine(self) -> Any:
        """Initialize the security engine"""
        try:
            # Placeholder for security engine initialization
            # In a real implementation, this would initialize the actual security engine
            return {"encryption_enabled": self.config.get("security", {}).get("encryption_enabled", False)}
        except Exception as e:
            logger.error(f"Error initializing security engine: {e}")
            return None
    
    async def _init_ai_engine(self) -> Any:
        """Initialize the AI engine"""
        try:
            # Placeholder for AI engine initialization
            # In a real implementation, this would initialize the actual AI engine
            return {"provider": self.config.get("ai", {}).get("provider", "unknown")}
        except Exception as e:
            logger.error(f"Error initializing AI engine: {e}")
            return None
    
    async def _init_storage_manager(self) -> Any:
        """Initialize the storage manager"""
        try:
            # Placeholder for storage manager initialization
            # In a real implementation, this would initialize the actual storage manager
            storage_path = Path(self.config.get("storage", {}).get("base_path", "./storage"))
            storage_path.mkdir(parents=True, exist_ok=True)
            return {"base_path": str(storage_path)}
        except Exception as e:
            logger.error(f"Error initializing storage manager: {e}")
            return None
    
    async def _verify_connections(self) -> bool:
        """Verify connections between components"""
        # In a real implementation, this would check that all components can communicate
        return len(self.components) > 0

# Helper function to create integration instance
async def create_integration(config_path: str) -> CodexFloIntegration:
    """Create and initialize a CodexFloIntegration instance"""
    import yaml
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        integration = CodexFloIntegration(config)
        await integration.initialize()
        return integration
    except Exception as e:
        logger.error(f"Error creating integration: {e}")
        raise