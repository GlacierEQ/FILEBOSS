"""
DeepSoul Learning System - Self-improvement and continual learning for code intelligence
"""
import os
import time
import json
import torch
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple, Any, Callable
from dataclasses import dataclass, field
from torch.utils.data import Dataset, DataLoader
from transformers import (
    PreTrainedModel, 
    PreTrainedTokenizer, 
    Trainer, 
    TrainingArguments,
    DataCollatorForLanguageModeling
)
from datetime import datetime
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DeepSoul-Learning")

@dataclass
class LearningConfig:
    """Configuration for learning processes"""
    max_steps: int = 100
    batch_size: int = 4
    learning_rate: float = 5e-5
    warmup_steps: int = 10
    gradient_accumulation_steps: int = 1
    save_steps: int = 50
    logging_steps: int = 10
    eval_steps: int = 50
    output_dir: str = "fine_tuned_models"
    fp16: bool = True
    memory_budget_gb: float = 4.0  # Memory budget in GB
    max_seq_length: int = 1024
    max_files_in_memory: int = 1000
    min_quality_threshold: float = 0.7
    enable_early_stopping: bool = True
    patience: int = 3  # For early stopping


class CodeDataset(Dataset):
    """Dataset for code examples"""
    
    def __init__(self, 
                tokenizer: PreTrainedTokenizer, 
                code_examples: List[Dict[str, Any]], 
                max_length: int = 1024):
        """
        Initialize the dataset
        
        Args:
            tokenizer: The tokenizer to use
            code_examples: List of code examples (dict with at least 'content' and 'language' keys)
            max_length: Maximum sequence length
        """
        self.tokenizer = tokenizer
        self.examples = code_examples
        self.max_length = max_length
    
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx) -> Dict[str, torch.Tensor]:
        example = self.examples[idx]
        
        # Add language tag if available
        if 'language' in example and example['language']:
            prompt = f"## {example['language']}\n{example['content']}"
        else:
            prompt = example['content']
        
        # Tokenize input
        tokenized = self.tokenizer(
            prompt,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        
        # Remove batch dimension
        return {k: v.squeeze(0) for k, v in tokenized.items()}


class SelfLearningSystem:
    """Continual learning system for DeepSoul"""
    
    def __init__(self, 
                model: PreTrainedModel,
                tokenizer: PreTrainedTokenizer,
                config: LearningConfig = None):
        """
        Initialize the learning system
        
        Args:
            model: The model to fine-tune
            tokenizer: The tokenizer to use
            config: Learning configuration
        """
        self.model = model
        self.tokenizer = tokenizer
        self.config = config or LearningConfig()
        self.training_history = []
        self.validation_metrics = []
        self.device = next(model.parameters()).device
        
        # Create output directory
        os.makedirs(self.config.output_dir, exist_ok=True)
    
    def prepare_training_args(self, output_subdir: str) -> TrainingArguments:
        """Prepare training arguments"""
        return TrainingArguments(
            output_dir=os.path.join(self.config.output_dir, output_subdir),
            max_steps=self.config.max_steps,
            per_device_train_batch_size=self.config.batch_size,
            per_device_eval_batch_size=self.config.batch_size,
            learning_rate=self.config.learning_rate,
            warmup_steps=self.config.warmup_steps,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            save_steps=self.config.save_steps,
            logging_steps=self.config.logging_steps,
            evaluation_strategy="steps" if self.config.eval_steps > 0 else "no",
            eval_steps=self.config.eval_steps if self.config.eval_steps > 0 else None,
            load_best_model_at_end=self.config.enable_early_stopping,
            fp16=self.config.fp16 and torch.cuda.is_available(),
        )
    
    def fine_tune(self, 
                 train_examples: List[Dict[str, Any]], 
                 eval_examples: Optional[List[Dict[str, Any]]] = None,
                 task_name: str = None) -> Dict[str, Any]:
        """
        Fine-tune the model on code examples
        
        Args:
            train_examples: List of training examples
            eval_examples: List of evaluation examples (optional)
            task_name: Name of the task (used for output directory)
            
        Returns:
            Dictionary of training metrics
        """
        if len(train_examples) == 0:
            logger.warning("No training examples provided. Skipping fine-tuning.")
            return {"status": "failed", "error": "No training examples"}
        
        # Generate task name if not provided
        if task_name is None:
            task_name = f"task_{int(time.time())}"
        
        logger.info(f"Starting fine-tuning for task: {task_name}")
        logger.info(f"Number of training examples: {len(train_examples)}")
        
        # Create datasets
        train_dataset = CodeDataset(
            self.tokenizer,
            train_examples,
            max_length=self.config.max_seq_length
        )
        
        eval_dataset = None
        if eval_examples and len(eval_examples) > 0:
            logger.info(f"Number of evaluation examples: {len(eval_examples)}")
            eval_dataset = CodeDataset(
                self.tokenizer,
                eval_examples,
                max_length=self.config.max_seq_length
            )
        
        # Prepare data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False  # We're doing causal language modeling, not masked
        )
        
        # Prepare training arguments
        training_args = self.prepare_training_args(task_name)
        
        # Create trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator,
        )
        
        # Train the model
        try:
            logger.info(f"Starting training for {self.config.max_steps} steps")
            train_result = trainer.train()
            
            # Save the fine-tuned model
            trainer.save_model()
            self.tokenizer.save_pretrained(os.path.join(self.config.output_dir, task_name))
            
            # Log training metrics
            metrics = train_result.metrics
            metrics["task"] = task_name
            metrics["timestamp"] = datetime.now().isoformat()
            metrics["num_examples"] = len(train_examples)
            
            # Save metrics
            with open(os.path.join(self.config.output_dir, task_name, "metrics.json"), "w") as f:
                json.dump(metrics, f, indent=2)
                
            self.training_history.append(metrics)
            
            logger.info(f"Training completed. Model saved to {os.path.join(self.config.output_dir, task_name)}")
            logger.info(f"Training loss: {metrics.get('train_loss', 'N/A')}")
            
            return {"status": "success", "metrics": metrics}
            
        except Exception as e:
            logger.error(f"Error during fine-tuning: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def evaluate_model(self, eval_examples: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Evaluate the model on a set of examples
        
        Args:
            eval_examples: List of evaluation examples
            
        Returns:
            Dictionary of evaluation metrics
        """
        if len(eval_examples) == 0:
            logger.warning("No evaluation examples provided. Skipping evaluation.")
            return {"status": "failed", "error": "No evaluation examples"}
        
        logger.info(f"Evaluating model on {len(eval_examples)} examples")
        
        # Create dataset
        eval_dataset = CodeDataset(
            self.tokenizer,
            eval_examples,
            max_length=self.config.max_seq_length
        )
        
        # Create data loader
        eval_loader = DataLoader(
            eval_dataset,
            batch_size=self.config.batch_size,
            collate_fn=DataCollatorForLanguageModeling(
                tokenizer=self.tokenizer,
                mlm=False
            )
        )
        
        # Evaluate
        self.model.eval()
        total_loss = 0.0
        num_batches = 0
        
        with torch.no_grad():
            for batch in tqdm(eval_loader, desc="Evaluating"):
                # Move batch to device
                batch = {k: v.to(self.device) for k, v in batch.items()}
                
                # Forward pass
                outputs = self.model(**batch)
                loss = outputs.loss
                
                total_loss += loss.item()
                num_batches += 1
        
        # Calculate average loss
        avg_loss = total_loss / max(1, num_batches)
        perplexity = torch.exp(torch.tensor(avg_loss)).item()
        
        metrics = {
            "eval_loss": avg_loss,
            "eval_perplexity": perplexity,
            "timestamp": datetime.now().isoformat()
        }
        
        self.validation_metrics.append(metrics)
        
        logger.info(f"Evaluation complete. Loss: {avg_loss:.4f}, Perplexity: {perplexity:.4f}")
        
        return metrics
    
    def incremental_learning(self, 
                            examples: List[Dict[str, Any]], 
                            batch_size: int = 100,
                            eval_ratio: float = 0.1) -> List[Dict[str, Any]]:
        """
        Implement incremental learning on batches of examples
        
        Args:
            examples: List of examples to learn from
            batch_size: Number of examples in each batch
            eval_ratio: Ratio of examples to use for evaluation
            
        Returns:
            List of training metrics for each batch
        """
        if len(examples) == 0:
            logger.warning("No examples provided. Skipping incremental learning.")
            return []
        
        logger.info(f"Starting incremental learning on {len(examples)} examples")
        
        # Shuffle examples
        np.random.shuffle(examples)
        
        # Split into batches
        batches = [examples[i:i+batch_size] for i in range(0, len(examples), batch_size)]
        
        metrics_list = []
        
        # Train on each batch
        for i, batch in enumerate(batches):
            logger.info(f"Processing batch {i+1}/{len(batches)} with {len(batch)} examples")
            
            # Split batch into train and eval
            eval_size = max(1, int(len(batch) * eval_ratio))
            eval_examples = batch[:eval_size]
            train_examples = batch[eval_size:]
            
            # Fine-tune on this batch
            task_name = f"incremental_batch_{i+1}"
            metrics = self.fine_tune(train_examples, eval_examples, task_name)
            metrics_list.append(metrics)
            
            # Evaluate overall progress
            if i % 5 == 0 and i > 0:
                all_eval = [ex for b in batches[:i] for ex in b[:int(len(b) * eval_ratio)]]
                logger.info(f"Comprehensive evaluation on {len(all_eval)} examples")
                eval_metrics = self.evaluate_model(all_eval)
                logger.info(f"Comprehensive evaluation metrics: {eval_metrics}")
        
        logger.info(f"Incremental learning complete. Processed {len(batches)} batches.")
        
        return metrics_list
    
    def adaptive_knowledge_integration(self, 
                                     new_examples: List[Dict[str, Any]],
                                     core_examples: List[Dict[str, Any]],
                                     integration_threshold: float = 0.8) -> Dict[str, Any]:
        """
        Adaptively integrate new knowledge while preserving core capabilities
        
        Args:
            new_examples: New examples to integrate
            core_examples: Core examples to preserve capabilities
            integration_threshold: Threshold for accepting integration
            
        Returns:
            Integration metrics
        """
        logger.info(f"Starting adaptive knowledge integration with {len(new_examples)} new examples")
        
        # First, evaluate model on core examples
        initial_metrics = self.evaluate_model(core_examples)
        initial_loss = initial_metrics.get("eval_loss", float('inf'))
        
        # Fine-tune on new examples
        fine_tune_metrics = self.fine_tune(
            new_examples, 
            eval_examples=core_examples,
            task_name=f"integration_{int(time.time())}"
        )
        
        # Re-evaluate on core examples
        post_metrics = self.evaluate_model(core_examples)
        post_loss = post_metrics.get("eval_loss", float('inf'))
        
        # Check if integration was successful
        is_successful = post_loss <= initial_loss * integration_threshold
        
        integration_metrics = {
            "initial_loss": initial_loss,
            "post_integration_loss": post_loss,
            "relative_change": (post_loss - initial_loss) / initial_loss if initial_loss > 0 else 0,
            "is_successful": is_successful,
            "integration_threshold": integration_threshold,
            "num_new_examples": len(new_examples),
            "num_core_examples": len(core_examples),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Knowledge integration {'successful' if is_successful else 'failed'}")
        logger.info(f"Initial loss: {initial_loss:.4f}, Post-integration loss: {post_loss:.4f}")
        
        # If integration failed, we could revert to previous model state
        # (Implementation depends on how you're managing model checkpoints)
        
        return integration_metrics
    
    def generate_training_examples(self, 
                                 seed_examples: List[Dict[str, Any]], 
                                 num_examples: int = 10) -> List[Dict[str, Any]]:
        """
        Generate synthetic training examples based on seed examples
        
        Args:
            seed_examples: Seed examples to generate from
            num_examples: Number of examples to generate
            
        Returns:
            List of generated examples
        """
        logger.info(f"Generating {num_examples} synthetic examples from {len(seed_examples)} seeds")
        
        generated_examples = []
        
        for _ in range(num_examples):
            # Randomly select a seed example
            seed = np.random.choice(seed_examples)
            
            # Prepare the prompt for generation
            language = seed.get('language', 'python')
            content = seed.get('content', '')
            
            # Create prompt based on the first few lines of the seed example
            lines = content.split('\n')
            prompt_lines = lines[:min(5, len(lines))]
            prompt = f"## {language}\n" + '\n'.join(prompt_lines)
            
            # Generate completion
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_new_tokens=self.config.max_seq_length,
                    do_sample=True,
                    top_p=0.95,
                    temperature=0.8,
                    num_return_sequences=1
                )
            
            # Decode the generated text
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Remove the prompt from the generated text
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):]
            
            # Create example
            example = {
                'content': prompt + generated_text,
                'language': language,
                'source': 'synthetic',
                'timestamp': datetime.now().isoformat()
            }
            
            generated_examples.append(example)
        
        logger.info(f"Generated {len(generated_examples)} synthetic examples")
        
        return generated_examples
    
    def expert_programming_tasks(self) -> List[Dict[str, str]]:
        """Generate a set of expert programming tasks for evaluation"""
        tasks = [
            {
                "task": "Implement a red-black tree in Python",
                "language": "python",
                "difficulty": "hard",
                "tags": ["data_structure", "tree", "balanced"]
            },
            {
                "task": "Create a simple HTTP server with routing in JavaScript",
                "language": "javascript",
                "difficulty": "medium",
                "tags": ["network", "server", "web"]
            },
            {
                "task": "Implement a concurrent worker pool in Go",
                "language": "go",
                "difficulty": "medium",
                "tags": ["concurrency", "parallelism", "worker"]
            },
            {
                "task": "Design a SQL query optimizer",
                "language": "sql",
                "difficulty": "hard",
                "tags": ["database", "optimization", "query"]
            },
            {
                "task": "Implement a simple neural network from scratch",
                "language": "python",
                "difficulty": "medium",
                "tags": ["machine_learning", "neural_network"]
            }
        ]
        
        return tasks
    
    def save_learning_state(self, path: str) -> bool:
        """
        Save the learning system state
        
        Args:
            path: Path to save the state
            
        Returns:
            True if successful, False otherwise
        """
        try:
            state = {
                "training_history": self.training_history,
                "validation_metrics": self.validation_metrics,
                "config": {k: v for k, v in self.config.__dict__.items() if not k.startswith("_")},
                "timestamp": datetime.now().isoformat()
            }
            
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                json.dump(state, f, indent=2)
            
            logger.info(f"Learning state saved to {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving learning state: {str(e)}")
            return False
    
    def load_learning_state(self, path: str) -> bool:
        """
        Load the learning system state
        
        Args:
            path: Path to load the state from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(path):
                logger.warning(f"Learning state file not found: {path}")
                return False
            
            with open(path, "r") as f:
                state = json.load(f)
            
            self.training_history = state.get("training_history", [])
            self.validation_metrics = state.get("validation_metrics", [])
            
            # Update config if present
            if "config" in state:
                for k, v in state["config"].items():
                    if hasattr(self.config, k):
                        setattr(self.config, k, v)
            
            logger.info(f"Learning state loaded from {path}")
            logger.info(f"Loaded {len(self.training_history)} training history entries")
            logger.info(f"Loaded {len(self.validation_metrics)} validation metrics entries")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading learning state: {str(e)}")
            return False


class CurriculumLearningManager:
    """Manager for curriculum-based learning process"""
    
    def __init__(self, learning_system: SelfLearningSystem):
        """Initialize with a learning system"""
        self.learning_system = learning_system
        self.curriculum_stages = []
        self.current_stage = 0
        self.stage_metrics = []
    
    def add_curriculum_stage(self, 
                           name: str, 
                           examples: List[Dict[str, Any]], 
                           difficulty: float,
                           description: str = None) -> None:
        """Add a curriculum stage"""
        stage = {
            "name": name,
            "examples": examples,
            "difficulty": difficulty,
            "description": description,
            "completed": False,
            "metrics": None,
            "timestamp": None
        }
        self.curriculum_stages.append(stage)
        self.curriculum_stages.sort(key=lambda s: s["difficulty"])  # Sort by difficulty
    
    def advance_curriculum(self) -> Dict[str, Any]:
        """
        Advance to the next curriculum stage
        
        Returns:
            Dictionary with stage results
        """
        if self.current_stage >= len(self.curriculum_stages):
            logger.info("Curriculum completed. No more stages.")
            return {"status": "completed"}
        
        # Get current stage
        stage = self.curriculum_stages[self.current_stage]
        logger.info(f"Starting curriculum stage {self.current_stage+1}/{len(self.curriculum_stages)}: {stage['name']}")
        
        # Split examples for evaluation
        examples = stage["examples"]
        np.random.shuffle(examples)
        
        eval_size = max(1, int(len(examples) * 0.1))
        eval_examples = examples[:eval_size]
        train_examples = examples[eval_size:]
        
        # Fine-tune on this stage
        metrics = self.learning_system.fine_tune(
            train_examples, 
            eval_examples, 
            task_name=f"curriculum_{stage['name']}"
        )
        
        # Update stage status
        stage["completed"] = metrics["status"] == "success"
        stage["metrics"] = metrics
        stage["timestamp"] = datetime.now().isoformat()
        
        self.stage_metrics.append({
            "stage": self.current_stage,
            "name": stage["name"],
            "metrics": metrics,
            "timestamp": stage["timestamp"]
        })
        
        # Advance to next stage
        self.current_stage += 1
        
        return {
            "status": "advanced",
            "stage_name": stage["name"],
            "stage_index": self.current_stage - 1,
            "completed": stage["completed"],
            "metrics": metrics
        }
    
    def run_full_curriculum(self) -> Dict[str, Any]:
        """
        Run the entire curriculum from the current stage
        
        Returns:
            Dictionary with curriculum results
        """
        results = []
        
        while self.current_stage < len(self.curriculum_stages):
            result = self.advance_curriculum()
            results.append(result)
            
            if result["status"] != "advanced" or not result["completed"]:
                logger.warning(f"Curriculum stopped at stage {self.current_stage}/{len(self.curriculum_stages)}")
                break
        
        return {
            "status": "completed" if self.current_stage >= len(self.curriculum_stages) else "partial",
            "stages_completed": self.current_stage,
            "total_stages": len(self.curriculum_stages),
            "results": results
        }


def create_programming_curriculum() -> List[Dict[str, Any]]:
    """Create a programming curriculum with increasing difficulty"""
    curriculum = [
        {
            "name": "basic_syntax",
            "description": "Basic syntax and simple functions",
            "difficulty": 1.0,
            "examples": generate_basic_syntax_examples()
        },
        {
            "name": "data_structures",
            "description": "Common data structures (lists, dicts, etc.)",
            "difficulty": 2.0,
            "examples": generate_data_structure_examples()
        },
        {
            "name": "algorithms",
            "description": "Basic algorithms (sorting, searching)",
            "difficulty": 3.0,
            "examples": generate_algorithm_examples()
        },
        {
            "name": "oop",
            "description": "Object-oriented programming",
            "difficulty": 4.0,
            "examples": generate_oop_examples()
        },
        {
            "name": "advanced",
            "description": "Advanced topics (concurrency, optimization)",
            "difficulty": 5.0,
            "examples": generate_advanced_examples()
        }
    ]
    
    return curriculum


def generate_basic_syntax_examples() -> List[Dict[str, Any]]:
    """Generate examples for basic syntax"""
    # This is a placeholder - in a real implementation, you would have actual code examples
    return [
        {"content": "def add(a, b):\n    return a + b", "language": "python"},
        {"content": "for i in range(10):\n    print(i)", "language": "python"},
        {"content": "if x > 0:\n    print('positive')\nelse:\n    print('negative')", "language": "python"}
    ]


def generate_data_structure_examples() -> List[Dict[str, Any]]:
    """Generate examples for data structures"""
    # Placeholder
    return [
        {"content": "my_list = [1, 2, 3, 4, 5]\nmy_list.append(6)\nprint(my_list)", "language": "python"},
        {"content": "my_dict = {'name': 'Alice', 'age': 30}\nprint(my_dict['name'])", "language": "python"}
    ]


def generate_algorithm_examples() -> List[Dict[str, Any]]:
    """Generate examples for algorithms"""
    # Placeholder
    return [
        {
            "content": "def bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(0, n-i-1):\n            if arr[j] > arr[j+1]:\n                arr[j], arr[j+1] = arr[j+1], arr[j]\n    return arr",
            "language": "python"
        }
    ]


def generate_oop_examples() -> List[Dict[str, Any]]:
    """Generate examples for OOP"""
    # Placeholder
    return [
        {
            "content": "class Person:\n    def __init__(self, name, age):\n        self.name = name\n        self.age = age\n        \n    def greet(self):\n        return f'Hello, my name is {self.name}'",
            "language": "python"
        }
    ]


def generate_advanced_examples() -> List[Dict[str, Any]]:
    """Generate examples for advanced topics"""
    # Placeholder
    return [
        {
            "content": "import threading\n\ndef worker(num):\n    print(f'Worker {num} started')\n    \nthreads = []\nfor i in range(5):\n    t = threading.Thread(target=worker, args=(i,))\n    threads.append(t)\n    t.start()\n    \nfor t in threads:\n    t.join()",
            "language": "python"
        }
    ]


# Example usage
def demo():
    """Demo of the learning system"""
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    
    print("Loading model and tokenizer...")
    
    # Load a small model for demonstration
    model_name = "deepseek-ai/deepseek-coder-1.3b-instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True)
    
    # Create learning config
    config = LearningConfig(
        max_steps=5,  # Small number for demo
        batch_size=2,
        learning_rate=5e-5,
        output_dir="demo_fine_tuned"
    )
    
    # Create learning system
    learning_system = SelfLearningSystem(model, tokenizer, config)
    
    # Create some examples
    examples = generate_basic_syntax_examples() + generate_data_structure_examples()
    
    print(f"Created {len(examples)} examples for training")
    
    # Split for training and evaluation
    train_examples = examples[:3]
    eval_examples = examples[3:]
    
    print("Fine-tuning model on examples...")
    metrics = learning_system.fine_tune(train_examples, eval_examples, task_name="demo")
    
    print(f"Fine-tuning complete with status: {metrics['status']}")
    
    # Create curriculum
    print("Creating curriculum learning manager...")
    curriculum_manager = CurriculumLearningManager(learning_system)
    
    # Add some curriculum stages
    curriculum_manager.add_curriculum_stage(
        "basics",
        generate_basic_syntax_examples(),
        difficulty=1.0,
        description="Basic syntax examples"
    )
    
    curriculum_manager.add_curriculum_stage(
        "data_structures",
        generate_data_structure_examples(),
        difficulty=2.0,
        description="Data structure examples"
    )
    
    print("Advancing through curriculum...")
    result = curriculum_manager.advance_curriculum()
    
    print(f"Curriculum stage complete: {result['stage_name']}")
    
    # Save learning state
    learning_system.save_learning_state("demo_learning_state.json")
    
    print("Learning system demo complete!")


if __name__ == "__main__":
    demo()
