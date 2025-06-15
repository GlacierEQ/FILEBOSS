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

# DeepSoul component imports
from implementation.deepsoul_tensor_core import TensorCodeRepresentation, CodeUnderstandingEngine
from implementation.deepsoul_knowledge_system import (
    KnowledgeStore, KnowledgeAcquisition, KnowledgeRecommendation, CodeKnowledgeItem
)
from implementation.deepsoul_learning_system import (
    SelfLearningSystem, LearningConfig, CurriculumLearningManager
)
from implementation.deepsoul_code_comprehension import CodeUnderstandingEngine
from implementation.deepsoul_autonomy_manager import (
    TaskManager, AutonomousAgent, ResourceMonitor, Task, TaskPriority
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("deepsoul.log")
    ]
)
logger = logging.getLogger("DeepSoul-System")


class DeepSoul:
    """
    Core integration class for DeepSoul system
    
    This class provides access to all DeepSoul components and orchestrates 
    their interaction to function as a unified system.
    """
    
    def __init__(self, 
                model_name: str = "deepseek-ai/deepseek-coder-1.3b-instruct",
                device: Optional[str] = None,
                load_all_components: bool = True,
                memory_efficient: bool = True,
                max_memory_usage: float = 0.9):
        """
        Initialize the DeepSoul system
        
        Args:
            model_name: Name or path of the underlying model
            device: Device to use (None for auto-detect)
            load_all_components: Whether to load all components immediately
            memory_efficient: Use memory efficiency techniques
            max_memory_usage: Maximum memory usage fraction (0.0-1.0)
        """
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.memory_efficient = memory_efficient
        self.max_memory_usage = max_memory_usage
        
        # Component storage
        self.components = {}
        self.initialized = False
        
        # Configuration
        config_dir = Path("deepsoul_config")
        config_dir.mkdir(exist_ok=True)
        self.config_path = config_dir / "system_config.json"
        self.config = self._load_config()
        
        # Get memory manager
        self.memory_manager = get_memory_manager()
        
        # Register custom memory hooks
        setup_memory_protection(
            warning_hook=self._memory_warning_hook,
            critical_hook=self._memory_critical_hook
        )
        
        if load_all_components:
            self.initialize()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load system configuration from file"""
        default_config = {
            "model_name": self.model_name,
            "device": self.device,
            "knowledge_store_path": "knowledge_store.db",
            "learning_output_dir": "fine_tuned_models",
            "task_checkpoint_dir": "task_checkpoints",
            "max_concurrent_tasks": 4,
            "auto_learning_enabled": False,
            "auto_knowledge_acquisition": False
        }
        
        try:
            if self.config_path.exists():
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                # Update with default values for missing keys
                for k, v in default_config.items():
                    if k not in config:
                        config[k] = v
                return config
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
        
        # Save default config
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Save system configuration to file"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")
    
    def _memory_warning_hook(self, data: Dict[str, Any]) -> None:
        """Custom memory warning hook"""
        if "gpu_usage" in data and self.device == "cuda":
            logger.warning(f"DeepSoul: High GPU memory usage detected: {data['gpu_usage']:.1%}")
        elif "ram_usage" in data:
            logger.warning(f"DeepSoul: High RAM usage detected: {data['ram_usage']:.1%}")
    
    def _memory_critical_hook(self, data: Dict[str, Any]) -> None:
        """Custom memory critical hook"""
        if "gpu_usage" in data and self.device == "cuda":
            logger.critical(f"DeepSoul: Critical GPU memory usage detected: {data['gpu_usage']:.1%}")
            
            # Take immediate action to reduce memory usage
            self._emergency_memory_cleanup()
            
        elif "ram_usage" in data:
            logger.critical(f"DeepSoul: Critical RAM usage detected: {data['ram_usage']:.1%}")
            
            # Take immediate action to reduce memory usage
            self._emergency_memory_cleanup()
    
    def _emergency_memory_cleanup(self) -> None:
        """Perform emergency memory cleanup when critical memory threshold is reached"""
        logger.warning("Emergency memory cleanup initiated")
        
        try:
            # 1. Clear CUDA cache
            if self.device == "cuda":
                torch.cuda.empty_cache()
            
            # 2. Run garbage collection
            gc.collect()
            
            # 3. Reduce model precision
            if self.model is not None:
                for name, param in self.model.named_parameters():
                    param.data = param.data.half()
            
            # 4. Offload model to CPU
            if self.device == "cuda" and self.model is not None:
                self.model = self.model.to("cpu")
            
            # 5. Create a memory dump for debugging
            self.memory_manager.memory_dump("emergency")
            
        except Exception as e:
            logger.error(f"Error during emergency memory cleanup: {str(e)}")
    
    def initialize(self) -> bool:
        """Initialize all system components"""
        if self.initialized:
            logger.info("DeepSoul system already initialized")
            return True
        
        logger.info(f"Initializing DeepSoul system with model: {self.model_name}")
        logger.info(f"Using device: {self.device}")
        
        try:
            # Use memory-efficient context for initialization
            with MemoryEfficientContext():
                # Load model and tokenizer
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name, 
                    trust_remote_code=True
                )
                
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name, 
                    trust_remote_code=True,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                    low_cpu_mem_usage=True
                )
                
                # Move to device
                self.model = self.model.to(self.device)
                
                # Optimize model for inference
                if self.memory_efficient:
                    logger.info("Optimizing model for memory efficiency")
                    
                    # Use tensor optimizer
                    optimizer = TensorOptimizer(device=self.device)
                    
                    # Optimize model weights
                    for name, param in self.model.named_parameters():
                        param.data = optimizer.optimize_dtype(param.data)
                    
                    # Set to eval mode
                    self.model.eval()
                    
                    # Clear CUDA cache
                    if self.device == "cuda":
                        torch.cuda.empty_cache()
                
                # Initialize auto-offload
                if self.device == "cuda":
                    logger.info("Initializing auto-offload system")
                    self.auto_offload = AutoOffload(model=self.model)
                    self.auto_offload.start_monitoring()
                
                # Initialize components
                self._init_knowledge_system()
                self._init_learning_system()
                self._init_code_comprehension()
                self._init_autonomy()
                self._init_tensor_core()
                
                self.initialized = True
                logger.info("DeepSoul system initialization complete")
                return True
            
        except Exception as e:
            logger.error(f"Error initializing DeepSoul system: {str(e)}")
            logger.error(traceback.format_exc())
            # Create memory dump for debugging
            self.memory_manager.memory_dump("initialization_error")
            return False
    
    def _init_knowledge_system(self):
        """Initialize knowledge system components"""
        logger.info("Initializing knowledge system...")
        
        # Create knowledge store
        knowledge_store = KnowledgeStore(self.config["knowledge_store_path"])
        
        # Create acquisition and recommendation systems
        knowledge_acquisition = KnowledgeAcquisition(knowledge_store, self.model, self.tokenizer)
        knowledge_recommendation = KnowledgeRecommendation(knowledge_store, self.model, self.tokenizer)
        
        # Store components
        self.components["knowledge_store"] = knowledge_store
        self.components["knowledge_acquisition"] = knowledge_acquisition
        self.components["knowledge_recommendation"] = knowledge_recommendation
    
    def _init_learning_system(self):
        """Initialize learning system components"""
        logger.info("Initializing learning system...")
        
        # Create learning config
        learning_config = LearningConfig(
            output_dir=self.config["learning_output_dir"],
            fp16=(self.device == "cuda")
        )
        
        # Create self-learning system
        learning_system = SelfLearningSystem(self.model, self.tokenizer, learning_config)
        
        # Create curriculum learning manager
        curriculum_manager = CurriculumLearningManager(learning_system)
        
        # Store components
        self.components["learning_system"] = learning_system
        self.components["curriculum_manager"] = curriculum_manager
    
    def _init_code_comprehension(self):
        """Initialize code comprehension components"""
        logger.info("Initializing code comprehension...")
        
        # Create code understanding engine
        code_understanding = CodeUnderstandingEngine(self.model, self.tokenizer)
        
        # Store components
        self.components["code_understanding"] = code_understanding
    
    def _init_autonomy(self):
        """Initialize autonomy components"""
        logger.info("Initializing autonomy system...")
        
        # Create task manager
        task_manager = TaskManager(
            max_concurrent_tasks=self.config["max_concurrent_tasks"],
            checkpoint_dir=self.config["task_checkpoint_dir"]
        )
        
        # Start task manager
        task_manager.start()
        
        # Create autonomous agent
        agent = AutonomousAgent("DeepSoul", task_manager, self.model, self.tokenizer)
        
        # Create resource monitor
        resource_monitor = ResourceMonitor(task_manager)
        resource_monitor.start()
        
        # Store components
        self.components["task_manager"] = task_manager
        self.components["autonomous_agent"] = agent
        self.components["resource_monitor"] = resource_monitor
    
    def _init_tensor_core(self):
        """Initialize tensor core components"""
        logger.info("Initializing tensor core...")
        
        # Create tensor code representation
        from implementation.deepsoul_tensor_core import CodeUnderstandingConfig
        config = CodeUnderstandingConfig()
        tensor_core = TensorCodeRepresentation(config, self.tokenizer)
        
        # Store components
        self.components["tensor_core"] = tensor_core
    
    def get_component(self, component_name: str) -> Any:
        """Get a specific system component by name"""
        if not self.initialized:
            raise RuntimeError("DeepSoul system not initialized")
        
        return self.components.get(component_name)
    
    def shutdown(self):
        """Shutdown all system components gracefully"""
        logger.info("Shutting down DeepSoul system...")
        
        # Stop auto-offload
        if hasattr(self, "auto_offload") and self.auto_offload:
            self.auto_offload.stop_monitoring()
        
        # Stop task manager and resource monitor if initialized
        if "task_manager" in self.components:
            self.components["resource_monitor"].stop()
            self.components["task_manager"].stop()
        
        # Clear model from GPU
        if hasattr(self, "model") and self.model is not None:
            self.model = self.model.to("cpu")
            self.model = None
            torch.cuda.empty_cache()
        
        logger.info("DeepSoul system shutdown complete")
    
    def analyze_code(self, 
                    code: str, 
                    language: str = "python") -> Dict[str, Any]:
        """
        Analyze code using the code comprehension system
        
        Args:
            code: The code to analyze
            language: Programming language of the code
            
        Returns:
            Dictionary with analysis results
        """
        if not self.initialized:
            self.initialize()
        
        # Use code understanding engine
        code_understanding = self.components["code_understanding"]
        
        # Use a temporary file for the code
        import tempfile
        with tempfile.NamedTemporaryFile('w', suffix=f'.{language}', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Process the file
            entities = code_understanding.process_file(temp_file)
            
            # Get complexity metrics for all entities
            complexity_metrics = {}
            for entity in entities:
                complexity_metrics[entity.name] = code_understanding.analyze_code_complexity(entity.name)
            
            # Generate summaries for all entities
            summaries = {}
            for entity in entities:
                summaries[entity.name] = code_understanding.generate_code_summary(entity.name)
            
            # Return the analysis results
            return {
                "entities": [entity.to_dict() for entity in entities],
                "complexity_metrics": complexity_metrics,
                "summaries": summaries
            }
        finally:
            # Clean up the temporary file
            os.unlink(temp_file)
    
    def enhance_code(self, 
                   code: str, 
                   language: str = "python",
                   enhancement_type: str = "optimize") -> str:
        """
        Enhance code using the model
        
        Args:
            code: The code to enhance
            language: Programming language of the code
            enhancement_type: Type of enhancement (optimize, document, refactor)
            
        Returns:
            Enhanced code
        """
        if not self.initialized:
            self.initialize()
        
        # Create prompt based on enhancement type
        if enhancement_type == "optimize":
            prompt = f"Optimize this {language} code for better performance while maintaining functionality:\n\n```{language}\n{code}\n```\n\nOptimized code:"
        elif enhancement_type == "document":
            prompt = f"Add comprehensive documentation to this {language} code:\n\n```{language}\n{code}\n```\n\nDocumented code:"
        elif enhancement_type == "refactor":
            prompt = f"Refactor this {language} code to improve readability and maintainability:\n\n```{language}\n{code}\n```\n\nRefactored code:"
        else:
            prompt = f"Improve this {language} code:\n\n```{language}\n{code}\n```\n\nImproved code:"
        
        # Generate enhanced code
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        outputs = self.model.generate(**inputs, max_new_tokens=512)
        enhanced_code = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return enhanced_code