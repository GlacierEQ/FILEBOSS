"""
DeepSoul System - Core implementation of the DeepSeek-Coder AI system
"""
import os
import gc
import sys
import json
import time
import torch
import logging
import threading
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import utilities
from utils.model_loader import load_model, get_model_loader
from utils.memory_manager import get_memory_manager
from utils.auto_offload import get_auto_offload
from utils.memory_efficient_generation import create_generator
from implementation.deepsoul_knowledge_system import KnowledgeSystem
from implementation.deepsoul_code_comprehension import CodeComprehensionEngine

logger = logging.getLogger("DeepSoul-System")

class DeepSoul:
    """
    Core implementation of the DeepSeek-Coder AI system
    
    This class integrates components for knowledge management, code comprehension,
    code generation, and enhancement.
    """
    
    def __init__(self, 
               model_name: str = "deepseek-ai/deepseek-coder-1.3b-instruct", 
               device: str = "cuda",
               knowledge_store_path: Optional[str] = None,
               memory_settings: Optional[Dict[str, Any]] = None):
        """
        Initialize the DeepSoul system
        
        Args:
            model_name: Name of the transformer model to use
            device: Device to run inference on
            knowledge_store_path: Path to knowledge store database
            memory_settings: Memory optimization settings
        """
        self.model_name = model_name
        self.device = device
        self.knowledge_store_path = knowledge_store_path or "knowledge_store.db"
        
        # Parse memory settings
        self.memory_settings = {
            "low_memory": False,
            "use_flash_attention": True,
            "auto_offload": True
        }
        if memory_settings:
            self.memory_settings.update(memory_settings)
        
        # Initialize components
        self.memory_manager = get_memory_manager()
        self.auto_offload = get_auto_offload()
        
        # These will be initialized in initialize()
        self.model = None
        self.tokenizer = None
        self.generator = None
        self.knowledge_system = None
        self.code_comprehension = None
        
        # Thread lock for thread safety
        self.lock = threading.RLock()
    
    def initialize(self) -> bool:
        """
        Initialize the system components
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            with self.lock:
                # Load model and tokenizer
                logger.info(f"Loading model: {self.model_name}")
                
                self.model, self.tokenizer = load_model(
                    self.model_name, 
                    low_memory=self.memory_settings.get("low_memory", False)
                )
                
                # Set up efficient generator
                self.generator = create_generator(self.model, self.tokenizer)
                
                # Initialize knowledge system
                logger.info(f"Initializing knowledge system with store: {self.knowledge_store_path}")
                self.knowledge_system = KnowledgeSystem(self.knowledge_store_path)
                
                # Initialize code comprehension engine
                logger.info("Initializing code comprehension engine")
                self.code_comprehension = CodeComprehensionEngine(self.model, self.tokenizer)
                
                logger.info("DeepSoul initialization complete")
                return True
                
        except Exception as e:
            logger.error(f"Error initializing DeepSoul: {str(e)}")
            return False
    
    def analyze_code(self, code: str, language: str = None) -> Dict[str, Any]:
        """
        Analyze code and provide insights
        
        Args:
            code: Source code to analyze
            language: Programming language (auto-detected if None)
            
        Returns:
            Dictionary with analysis results
        """
        with self.lock:
            # Ensure system is initialized
            if not self.code_comprehension:
                logger.error("Code comprehension engine not initialized")
                return {"error": "System not initialized"}
            
            # Detect language if not provided
            if not language:
                language = self.code_comprehension.detect_language(code)
            
            # Perform analysis
            try:
                logger.info(f"Analyzing {language} code ({len(code)} chars)")
                
                # Run the analysis
                analysis = self.code_comprehension.analyze(code, language)
                
                # Check if there are relevant knowledge entries
                if self.knowledge_system:
                    relevant_knowledge = self.knowledge_system.find_relevant_knowledge(code, language, limit=5)
                    if relevant_knowledge:
                        analysis["relevant_knowledge"] = relevant_knowledge
                
                return analysis
                
            except Exception as e:
                logger.error(f"Error in code analysis: {str(e)}")
                return {"error": str(e)}
    
    def enhance_code(self, code: str, language: str = None, enhancement_type: str = "optimize") -> str:
        """
        Enhance code based on specified type
        
        Args:
            code: Source code to enhance
            language: Programming language (auto-detected if None)
            enhancement_type: Type of enhancement (optimize, document, refactor)
            
        Returns:
            Enhanced code
        """
        with self.lock:
            # Ensure system is initialized
            if not self.code_comprehension or not self.generator:
                logger.error("System not fully initialized")
                return "Error: System not initialized"
            
            # Detect language if not provided
            if not language:
                language = self.code_comprehension.detect_language(code)
            
            # Generate prompt based on enhancement type
            if enhancement_type == "optimize":
                prompt = f"Optimize the following {language} code for performance and readability. Maintain the same functionality but make it more efficient:\n\n```{language}\n{code}\n```\n\nOptimized code:\n\n```{language}\n"
            elif enhancement_type == "document":
                prompt = f"Add comprehensive documentation to the following {language} code. Add detailed comments explaining what the code does, including function/class purpose descriptions and parameter explanations:\n\n```{language}\n{code}\n```\n\nDocumented code:\n\n```{language}\n"
            elif enhancement_type == "refactor":
                prompt = f"Refactor the following {language} code to improve its design, maintainability, and readability. Follow best practices for {language}:\n\n```{language}\n{code}\n```\n\nRefactored code:\n\n```{language}\n"
            else:
                return "Error: Invalid enhancement type"
            
            # Generate enhanced code
            try:
                enhanced_code = self.generator.generate(prompt)
                return enhanced_code.strip()
                
            except Exception as e:
                logger.error(f"Error in code enhancement: {str(e)}")
                return f"Error: {str(e)}"
    
    def acquire_knowledge(self, source: str, source_type: str = "auto") -> List[str]:
        """
        Acquire knowledge from a specified source
        
        Args:
            source: Source to acquire knowledge from
            source_type: Type of source (e.g., "auto", "file", "url")
            
        Returns:
            List of acquired knowledge entries
        """
        with self.lock:
            # Ensure system is initialized
        if self.model:
            del self.model
        if self.tokenizer:
            del self.tokenizer
        
        # Run garbage collection
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("DeepSoul shutdown complete")