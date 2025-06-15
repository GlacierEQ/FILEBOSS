"""
DeepSoul System - Core integration of all components for a unified system
"""
import os
import sys
import gc
import json
import torch
import logging
import threading
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from transformers import AutoTokenizer, AutoModelForCausalLM

# Add parent directory to path to enable imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import memory manager for OOM protection
from utils.memory_manager import get_memory_manager, setup_memory_protection

# Import OOM protection utilities
from implementation.oom_protected_execution import oom_protected, MemoryEfficientContext, adaptive_batch_size
from utils.memory_efficient_generation import create_generator
from utils.tensor_optimization import TensorOptimizer
from utils.auto_offload import AutoOffload

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("deepsoul_system.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("DeepSoul-System")


class DeepSoul:
    """
    DeepSoul Code Intelligence System - Integrates all components for a unified system
    """
    
    def __init__(self, model_name: str = "deepseek-ai/deepseek-coder-1.3b-instruct",
                 device: Optional[str] = None,
                 low_memory: bool = False):
        """
        Initialize the DeepSoul system
        
        Args:
            model_name: Name or path of the pre-trained model
            device: Device to use for computation (cuda or cpu)
            low_memory: Optimize for systems with limited memory
        """
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.low_memory = low_memory
        self.initialized = False
        self.config = self._load_config()
        
        # Initialize components
        self.components = {}
        self.tokenizer = None
        self.model = None
        
        # Memory protection setup
        self.memory_manager = get_memory_manager()
        
        # Initialize tensor optimizer
        self.tensor_optimizer = TensorOptimizer(device=torch.device(self.device))
        
        # Auto-offload utility
        self.auto_offload = AutoOffload(device=self.device)
        
        # Load model and tokenizer
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name, 
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            ).to(self.device)
            
            # Optimize model for inference
            self.model = self.tensor_optimizer.optimize_for_inference(self.model, self.device)
            
            # Set initialized flag
            self.initialized = True
            logger.info("DeepSoul system initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing DeepSoul: {str(e)}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load system configuration from file"""
        config_path = Path("deepsoul_config/system_config.json")
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading system config: {str(e)}")
        
        # Default configuration
        return {
            "model_name": self.model_name,
            "device": self.device,
            "knowledge_store_path": "knowledge_store.db",
            "learning_output_dir": "fine_tuned_models",
            "task_checkpoint_dir": "task_checkpoints",
            "max_concurrent_tasks": 4,
            "auto_learning_enabled": False,
            "auto_knowledge_acquisition": False
        }
    
    def initialize(self) -> None:
        """Initialize DeepSoul components"""
        try:
            from implementation.deepsoul_knowledge_system import KnowledgeAcquisition
            from implementation.deepsoul_learning_system import LearningSystem
            from implementation.deepsoul_code_comprehension import CodeComprehension
            from implementation.deepsoul_autonomy_manager import AutonomyManager
            
            # Initialize components
            self.components["knowledge_acquisition"] = KnowledgeAcquisition(
                knowledge_store_path=self.config.get("knowledge_store_path", "knowledge_store.db")
            )
            self.components["learning_system"] = LearningSystem(
                model=self.model,
                tokenizer=self.tokenizer,
                output_dir=self.config.get("learning_output_dir", "fine_tuned_models"),
                task_checkpoint_dir=self.config.get("task_checkpoint_dir", "task_checkpoints")
            )
            self.components["code_comprehension"] = CodeComprehension(
                model=self.model,
                tokenizer=self.tokenizer
            )
            self.components["autonomy_manager"] = AutonomyManager()
            
            logger.info("DeepSoul components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing DeepSoul components: {str(e)}")
    
    def get_component(self, name: str) -> Any:
        """Get a DeepSoul component by name"""
        return self.components.get(name)
    
    @oom_protected(retry_on_cpu=True)
    def analyze_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Analyze a code snippet"""
        try:
            code_comprehension = self.get_component("code_comprehension")
            if code_comprehension:
                return code_comprehension.analyze_code(code, language)
            else:
                return {"error": "Code comprehension component not available"}
        except Exception as e:
            logger.error(f"Error analyzing code: {str(e)}")
            return {"error": str(e)}
    
    @oom_protected(retry_on_cpu=True)
    def enhance_code(self, code: str, language: str = "python", enhancement_type: str = "optimize") -> str:
        """Enhance a code snippet"""
        try:
            code_comprehension = self.get_component("code_comprehension")
            if code_comprehension:
                return code_comprehension.enhance_code(code, language, enhancement_type)
            else:
                return "Error: Code comprehension component not available"
        except Exception as e:
            logger.error(f"Error enhancing code: {str(e)}")
            return f"Error: {str(e)}"
    
    @oom_protected(retry_on_cpu=True)
    def acquire_knowledge(self, source: str, source_type: str = "auto") -> List[str]:
        """Acquire knowledge from a source"""
        try:
            knowledge_acquisition = self.get_component("knowledge_acquisition")
            if knowledge_acquisition:
                return knowledge_acquisition.acquire_knowledge(source, source_type)
            else:
                return ["Error: Knowledge acquisition component not available"]
        except Exception as e:
            logger.error(f"Error acquiring knowledge: {str(e)}")
            return [f"Error: {str(e)}"]
    
    def shutdown(self) -> None:
        """Shutdown DeepSoul and release resources"""
        logger.info("Shutting down DeepSoul...")
        
        # Stop all components
        for name, component in self.components.items():
            try:
                if hasattr(component, "stop"):
                    component.stop()
                logger.info(f"Component '{name}' stopped")
            except Exception as e:
                logger.error(f"Error stopping component '{name}': {str(e)}")
        
        # Clear memory
        self.memory_manager.clear_memory(move_models_to_cpu=True)
        
        # Release model and tokenizer
        if self.model:
            del self.model
        if self.tokenizer:
            del self.tokenizer
        
        # Run garbage collection
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("DeepSoul shutdown complete")