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
                logger.info(f"Loaded system configuration from {self.config_path}")
                return config
        except Exception as e:
            logger.warning(f"Error loading configuration: {str(e)}")
        
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
            logger.info(f"Saved system configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
    
    def _memory_warning_hook(self, data: Dict[str, Any]) -> None:
        """Custom memory warning hook"""
        if "gpu_usage" in data and self.device == "cuda":
            logger.warning(f"DeepSoul: High GPU memory usage detected: {data['gpu_usage']:.1%}")
            
            # If we're approaching the threshold, clean up some memory
            if data["gpu_usage"] > 0.8:
                # Free up memory by offloading unused layers if possible
                self._offload_unused_layers()
                
        elif "ram_usage" in data:
            logger.warning(f"DeepSoul: High RAM usage detected: {data['ram_usage']:.1%}")
            
            # Run garbage collection to free up memory
            gc.collect()
    
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
    
    def _offload_unused_layers(self) -> None:
        """Offload unused model layers to CPU to save GPU memory"""
        if not hasattr(self, "model") or self.model is None:
            return
            
        try:
            # For transformers models, offload some layers if not currently used
            if hasattr(self.model, "transformer") and hasattr(self.model.transformer, "h"):
                # For GPT-like models, keep first and last few layers on GPU
                num_layers = len(self.model.transformer.h)
                keep_layers = min(4, max(2, num_layers // 4))  # Keep at least 2, at most 4 layers
                
                logger.info(f"Offloading middle transformer layers to CPU ({num_layers-2*keep_layers} layers)")
                
                for i, layer in enumerate(self.model.transformer.h):
                    # Keep first and last few layers on GPU
                    if keep_layers <= i < num_layers - keep_layers:
                        layer.to("cpu")
            
            # For encoder-decoder models
            elif hasattr(self.model, "encoder") and hasattr(self.model.encoder, "layer"):
                # Offload some encoder layers
                for i, layer in enumerate(self.model.encoder.layer):
                    if i < len(self.model.encoder.layer) // 2:
                        layer.to("cpu")
        except Exception as e:
            logger.error(f"Error offloading layers: {str(e)}")
    
    def _emergency_memory_cleanup(self) -> None:
        """Perform emergency memory cleanup when critical memory threshold is reached"""
        logger.warning("Emergency memory cleanup initiated")
        
        try:
            # 1. Clear CUDA cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            # 2. Run aggressive garbage collection
            gc.collect()
            
            # 3. Move model to CPU if on CUDA and critical
            if hasattr(self, "model") and self.model is not None:
                if next(self.model.parameters()).device.type == "cuda":
                    logger.warning("Moving model to CPU due to critical memory usage")
                    self.model = self.model.cpu()
            
            # 4. Clear component caches
            for component_name, component in self.components.items():
                if hasattr(component, "clear_cache"):
                    component.clear_cache()
                    logger.info(f"Cleared cache for component: {component_name}")
            
            # 5. Create a memory dump for debugging
            self.memory_manager.memory_dump("emergency")
            
        except Exception as e:
            logger.error(f"Error during emergency memory cleanup: {str(e)}")
    
    def initialize(self) -> bool:
        """Initialize the DeepSoul system and load components"""
        if self.initialized:
            logger.info("DeepSoul already initialized")
            return True
            
        try:
            # Use memory-efficient context for initialization
            with MemoryEfficientContext():
                # Load model and tokenizer with proper memory management
                logger.info(f"Loading model: {self.model_name}")
                
                # First, check if model is already loaded properly
                if self.model is not None and self.tokenizer is not None:
                    logger.info("Model already loaded")
                    
                else:
                    # Calculate optimal model loading parameters based on available memory
                    if self.memory_efficient and self.device == "cuda":
                        # Check available GPU memory
                        total_gpu_memory = torch.cuda.get_device_properties(0).total_memory
                        
                        # If less than 8GB of VRAM, use extra memory optimizations
                        use_quantization = total_gpu_memory < 8 * (1024**3)  # 8GB
                        use_low_cpu_mem_usage = True  # Always enable low CPU memory usage
                        
                        if use_quantization:
                            logger.info("Using quantization for low memory operation")
                            
                            # Import bitsandbytes if available
                            try:
                                import bitsandbytes as bnb
                                
                                # Load 8-bit model
                                logger.info("Loading model in 8-bit precision")
                                self.model = AutoModelForCausalLM.from_pretrained(
                                    self.model_name,
                                    trust_remote_code=True,
                                    torch_dtype=torch.float16,  # Use float16 for better compatibility
                                    device_map=self.device,
                                    load_in_8bit=True,
                                    low_cpu_mem_usage=use_low_cpu_mem_usage
                                )
                                self.tokenizer = AutoTokenizer.from_pretrained(
                                    self.model_name,
                                    trust_remote_code=True
                                )
                                
                                # Move to device
                                self.model = self.model.to(self.device)
                                
                                logger.info("Model loaded with 8-bit quantization")
                                return True
                            except ImportError:
                                logger.warning("bitsandbytes not installed. Cannot use 8-bit quantization.")
                    
                    # Load model and tokenizer
                    self.tokenizer = AutoTokenizer.from_pretrained(
                        self.model_name,
                        trust_remote_code=True
                    )
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        trust_remote_code=True,
                        torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                        device_map=self.device,
                        low_cpu_mem_usage=use_low_cpu_mem_usage
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
                
                logger.info("Model loaded successfully")
                
                # Initialize components
                self._init_knowledge_system()
                self._init_learning_system()
                self._init_code_comprehension()
                self._init_autonomy()
                self._init_tensor_core()
                
                # Mark as initialized
                self.initialized = True
                logger.info("DeepSoul system initialized successfully")
                return True
        
        except Exception as e:
            logger.error(f"Error initializing DeepSoul: {str(e)}")
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
        self_learning = SelfLearningSystem(
            model=self.model,
            tokenizer=self.tokenizer,
            config=learning_config
        )
        
        # Create curriculum learning manager
        curriculum_manager = CurriculumLearningManager(self_learning)
        
        # Store components
        self.components["learning_system"] = self_learning
        self.components["curriculum_manager"] = curriculum_manager
    
    def _init_code_comprehension(self):
        """Initialize code comprehension engine"""
        logger.info("Initializing code comprehension engine...")
        
        # Create code understanding engine
        code_understanding = CodeUnderstandingEngine()
        
        # Store component
        self.components["code_understanding"] = code_understanding
    
    def _init_autonomy(self):
        """Initialize autonomy management components"""
        logger.info("Initializing autonomy management...")
        
        # Create task manager
        task_manager = TaskManager(checkpoint_dir=self.config["task_checkpoint_dir"])
        
        # Create resource monitor
        resource_monitor = ResourceMonitor()
        
        # Create autonomous agent
        autonomous_agent = AutonomousAgent(
            model=self.model,
            tokenizer=self.tokenizer,
            task_manager=task_manager,
            resource_monitor=resource_monitor
        )
        
        # Store components
        self.components["task_manager"] = task_manager
        self.components["resource_monitor"] = resource_monitor
        self.components["autonomous_agent"] = autonomous_agent
    
    def _init_tensor_core(self):
        """Initialize tensor core components"""
        logger.info("Initializing tensor core...")
        
        # Create tensor code representation
        tensor_code = TensorCodeRepresentation(self.model, self.tokenizer)
        
        # Store component
        self.components["tensor_code"] = tensor_code
    
    def get_component(self, component_name: str) -> Any:
        """Get a system component by name"""
        return self.components.get(component_name)
    
    def shutdown(self):
        """Shutdown the DeepSoul system and release resources"""
        logger.info("Shutting down DeepSoul system...")
        
        # Stop auto-offload
        if hasattr(self, "auto_offload") and self.auto_offload:
            self.auto_offload.stop_monitoring()
        
        # Stop all components
        for name, component in self.components.items():
            try:
                if hasattr(component, "stop"):
                    component.stop()
                logger.info(f"Stopped component: {name}")
            except Exception as e:
                logger.error(f"Error stopping component {name}: {str(e)}")
        
        # Clear memory
        self.memory_manager.clear_memory(move_models_to_cpu=True)
        
        # Mark as not initialized
        self.initialized = False
        logger.info("DeepSoul system shutdown complete")
    
    @oom_protected(retry_on_cpu=True)
    def analyze_code(self, 
                    code: str, 
                    language: str = "python") -> Dict[str, Any]:
        """Analyze a code snippet"""
        try:
            # Get code understanding engine
            code_understanding = self.get_component("code_understanding")
            if not code_understanding:
                return {"error": "Code understanding component not available"}
            
            # Analyze code
            result = code_understanding.analyze_code(code, language)
            return result
        except Exception as e:
            logger.error(f"Error analyzing code: {str(e)}")
            return {"error": str(e)}
    
    @oom_protected(retry_on_cpu=True)
    def enhance_code(self, 
                   code: str, 
                   language: str = "python",
                   enhancement_type: str = "optimize") -> str:
        """Enhance a code snippet"""
        try:
            # Create a prompt for code enhancement
            prompt = f"""
            You are an expert code enhancer. Your task is to improve the given code snippet.
            
            Language: {language}
            Enhancement Type: {enhancement_type}
            
            Original Code:
            ```
            {code}
            ```
            
            Enhanced Code:
            ```
            """
            
            # Generate enhanced code
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            outputs = self.model.generate(
                input_ids=inputs.input_ids,
                attention_mask=inputs.attention_mask,
                max_length=1024,
                do_sample=True,
                top_p=0.95,
                temperature=0.7
            )
            enhanced_code = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract the code part (after the prompt)
            enhanced_code = enhanced_code[len(prompt):].strip()
            
            return enhanced_code
        
        except Exception as e:
            logger.error(f"Error enhancing code: {str(e)}")
            return f"Error: {str(e)}"
    
    @oom_protected(retry_on_cpu=True)
    def acquire_knowledge(self, source_path: str, source_type: str = "auto") -> List[str]:
        """Acquire knowledge from a file or directory"""
        try:
            # Get knowledge acquisition component
            knowledge_acquisition = self.get_component("knowledge_acquisition")
            if not knowledge_acquisition:
                logger.error("Knowledge acquisition component not available")
                return []
            
            # Ingest based on source type
            if source_type == "file":
                item_ids = knowledge_acquisition.ingest_file(source_path)
            elif source_type == "repo":
                item_ids = knowledge_acquisition.ingest_repository(source_path)
            else:
                # Auto-detect source type
                if os.path.isfile(source_path):
                    item_ids = knowledge_acquisition.ingest_file(source_path)
                elif os.path.isdir(source_path):
                    item_ids = knowledge_acquisition.ingest_repository(source_path)
                else:
                    logger.error(f"Invalid source path: {source_path}")
                    return []
            
            return item_ids
        
        except Exception as e:
            logger.error(f"Error acquiring knowledge: {str(e)}")
            return []