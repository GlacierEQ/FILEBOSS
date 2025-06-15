#!/usr/bin/env python3
"""
Script to optimize DeepSeek-Coder model for faster inference.
This includes torch.compile, quantization, and performance tuning.
"""

import os
import time
import sys
import argparse
import logging
import torch
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from transformers import AutoTokenizer, AutoModelForCausalLM

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DeepSoul-Optimizer")

class ModelOptimizer:
    """Class to optimize large language models for inference."""
    
    def __init__(self, 
                 model_path: str,
                 output_path: Optional[str] = None,
                 device: str = "auto",
                 precision: str = "fp16"):
        """
        Initialize the model optimizer.
        
        Args:
            model_path: Path to model or model identifier
            output_path: Path to save the optimized model (optional)
            device: Device to run optimization on ("auto", "cpu", "cuda", "cuda:0", etc.)
            precision: Precision to use ("fp32", "fp16", "bf16")
        """
        self.model_path = model_path
        self.output_path = output_path
        self.precision = precision
        
        # Determine the device to use
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        # Set the PyTorch dtype based on precision
        if precision == "fp16":
            self.dtype = torch.float16
        elif precision == "bf16":
            self.dtype = torch.bfloat16
        else:  # fp32
            self.dtype = torch.float32
        
        # Log initialization info
        logger.info(f"Initializing optimizer for model: {model_path}")
        logger.info(f"Using device: {self.device}")
        logger.info(f"Using precision: {precision} ({self.dtype})")
        
        # Initialize tokenizer and model
        self.tokenizer = None
        self.model = None
        
        # Performance metrics
        self.metrics = {}
    
    def load_model(self):
        """Load the model and tokenizer."""
        logger.info("Loading model and tokenizer...")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True)
        
        # Load model with specified precision
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=self.dtype,
            trust_remote_code=True,
            device_map=self.device
        )
        
        logger.info("Model and tokenizer loaded successfully.")
    
    def apply_torch_compile(self, mode: str = "reduce-overhead"):
        """
        Apply torch.compile to the model for faster inference.
        
        Args:
            mode: Compilation mode (default, reduce-overhead, max-autotune)
        """
        if not hasattr(torch, "compile"):
            logger.warning("torch.compile not available. Skipping compilation.")
            return False
        
        try:
            logger.info(f"Applying torch.compile with mode: {mode}...")
            start_time = time.time()
            
            # Save original generate function for comparison
            orig_generate = self.model.generate
            
            # Apply torch.compile
            self.model = torch.compile(self.model, mode=mode)
            
            # Run a test inference to trigger compilation
            input_ids = self.tokenizer("def hello_world():", return_tensors="pt").input_ids
            if self.device != "cpu":
                input_ids = input_ids.to(self.device)
            
            # Generate output to trigger compilation
            _ = self.model.generate(input_ids, max_length=20)
            
            # Measure compilation time
            compile_time = time.time() - start_time
            logger.info(f"Model compiled in {compile_time:.2f} seconds")
            
            # Save metric
            self.metrics["torch_compile"] = {
                "mode": mode,
                "compile_time_seconds": compile_time
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply torch.compile: {str(e)}")
            return False
    
    def optimize_attention(self, flash_attention: bool = True, sdp_attention: bool = True):
        """
        Optimize attention mechanisms for faster inference.
        
        Args:
            flash_attention: Whether to enable Flash Attention if available
            sdp_attention: Whether to enable Scaled Dot Product attention
        """
        try:
            # Check for Flash Attention
            if flash_attention:
                try:
                    from transformers.utils import is_flash_attn_available
                    
                    if is_flash_attn_available():
                        logger.info("Enabling Flash Attention...")
                        os.environ["TRANSFORMERS_ATTENTION_IMPLEMENTATION"] = "flash_attention_2"
                        self.metrics["flash_attention"] = True
                    else:
                        logger.warning("Flash Attention not available. Install with: pip install flash-attn")
                        self.metrics["flash_attention"] = False
                except ImportError:
                    logger.warning("Could not check for Flash Attention.")
                    self.metrics["flash_attention"] = False
            
            # Enable Scaled Dot Product attention
            if sdp_attention:
                logger.info("Enabling PyTorch Scaled Dot Product attention...")
                torch.backends.cuda.enable_math_sdp(True)
                torch.backends.cuda.enable_flash_sdp(True)
                torch.backends.cuda.enable_mem_efficient_sdp(True)
                self.metrics["sdp_attention"] = True
            
            # Log current attention implementation
            attn_impl = os.environ.get("TRANSFORMERS_ATTENTION_IMPLEMENTATION", "default")
            logger.info(f"Current attention implementation: {attn_impl}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to optimize attention: {str(e)}")
            return False
    
    def optimize_memory(self):
        """Optimize memory usage for the model."""
        try:
            # Set PyTorch memory allocator
            if self.device != "cpu" and hasattr(torch.cuda, "memory_stats"):
                logger.info("Optimizing CUDA memory usage...")
                
                # Set CUDA memory allocation config for better large model performance
                torch.cuda.empty_cache()
                os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:128"
                
                # Log current memory usage
                memory_stats = torch.cuda.memory_stats()
                allocated_mem = memory_stats.get("allocated_bytes.all.current", 0) / (1024**3)
                reserved_mem = memory_stats.get("reserved_bytes.all.current", 0) / (1024**3)
                
                logger.info(f"CUDA memory: allocated={allocated_mem:.2f} GB, reserved={reserved_mem:.2f} GB")
                
                self.metrics["memory"] = {
                    "allocated_gb": allocated_mem,
                    "reserved_gb": reserved_mem
                }
            
            return True
                
        except Exception as e:
            logger.error(f"Failed to optimize memory: {str(e)}")
            return False
    
    def benchmark(self, prompt: str = "def fibonacci(n):", num_runs: int = 5):
        """
        Benchmark model inference performance.
        
        Args:
            prompt: The prompt to use for benchmarking
            num_runs: Number of benchmark runs
        """
        logger.info(f"Running benchmark with prompt: '{prompt}'")
        
        try:
            # Ensure model is loaded
            if self.model is None or self.tokenizer is None:
                self.load_model()
            
            # Prepare input
            inputs = self.tokenizer(prompt, return_tensors="pt")
            if self.device != "cpu":
                inputs = inputs.to(self.device)
            
            # Warmup
            logger.info("Warming up...")
            _ = self.model.generate(**inputs, max_length=50)
            
            # Benchmark
            logger.info(f"Running {num_runs} benchmark iterations...")
            latencies = []
            tokens_per_second = []
            
            for i in range(num_runs):
                start_time = time.time()
                outputs = self.model.generate(**inputs, max_length=100)
                end_time = time.time()
                
                # Calculate metrics
                latency = end_time - start_time
                num_tokens = outputs.shape[1] - inputs.input_ids.shape[1]
                tokens_per_sec = num_tokens / latency
                
                latencies.append(latency)
                tokens_per_second.append(tokens_per_sec)
                
                logger.info(f"Run {i+1}: Latency={latency:.4f}s, Tokens/sec={tokens_per_sec:.2f}")
            
            # Calculate statistics
            avg_latency = sum(latencies) / len(latencies)
            avg_tokens_per_sec = sum(tokens_per_second) / len(tokens_per_second)
            
            # Log results
            logger.info(f"Benchmark results:")
            logger.info(f"  Average latency: {avg_latency:.4f} seconds")
            logger.info(f"  Average generation speed: {avg_tokens_per_sec:.2f} tokens/second")
            
            # Save results to metrics
            self.metrics["benchmark"] = {
                "prompt": prompt,
                "num_runs": num_runs,
                "average_latency_seconds": avg_latency,
                "average_tokens_per_second": avg_tokens_per_sec,
                "individual_latencies": latencies
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Benchmark failed: {str(e)}")
            return False
    
    def save_model(self):
        """Save the optimized model if output path is provided."""
        if not self.output_path:
            logger.info("No output path provided. Skipping model save.")
            return False
        
        try:
            # Create output directory
            os.makedirs(self.output_path, exist_ok=True)
            
            # Save model and tokenizer
            logger.info(f"Saving optimized model to {self.output_path}...")
            self.model.save_pretrained(self.output_path)
            self.tokenizer.save_pretrained(self.output_path)
            
            # Save optimization metrics
            metrics_path = os.path.join(self.output_path, "optimization_metrics.json")
            with open(metrics_path, "w") as f:
                json.dump(self.metrics, f, indent=2)
            
            logger.info("Model, tokenizer, and metrics saved successfully.")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save model: {str(e)}")
            return False
    
    def optimize(self, 
                apply_torch_compile: bool = True,
                optimize_attention: bool = True,
                optimize_memory: bool = True,
                run_benchmark: bool = True):
        """
        Run full optimization process.
        
        Args:
            apply_torch_compile: Whether to apply torch.compile
            optimize_attention: Whether to optimize attention mechanisms
            optimize_memory: Whether to optimize memory usage
            run_benchmark: Whether to run benchmarks
        """
        # Record start time
        start_time = time.time()
        
        # Load model
        self.load_model()
        
        # Apply optimizations
        if optimize_memory:
            self.optimize_memory()
        
        if optimize_attention:
            self.optimize_attention()
        
        if apply_torch_compile:
            self.apply_torch_compile()
        
        # Run benchmark
        if run_benchmark:
            self.benchmark()
        
        # Save model if output path provided
        if self.output_path:
            self.save_model()
        
        # Record total optimization time
        total_time = time.time() - start_time
        self.metrics["total_optimization_time_seconds"] = total_time
        logger.info(f"Optimization completed in {total_time:.2f} seconds.")
        
        return self.metrics

def main():
    parser = argparse.ArgumentParser(description="Optimize DeepSeek-Coder models for inference")
    parser.add_argument("--model-path", type=str, required=True, help="Path to the model or model ID")
    parser.add_argument("--output-path", type=str, help="Path to save the optimized model (optional)")
    parser.add_argument("--device", type=str, default="auto", help="Device to run optimization on (auto, cpu, cuda, cuda:0, etc.)")
    parser.add_argument("--precision", type=str, default="fp16", choices=["fp32", "fp16", "bf16"], help="Precision to use")
    parser.add_argument("--no-torch-compile", action="store_true", help="Disable torch.compile optimization")
    parser.add_argument("--no-attention-optim", action="store_true", help="Disable attention optimizations")
    parser.add_argument("--no-memory-optim", action="store_true", help="Disable memory optimizations")
    parser.add_argument("--no-benchmark", action="store_true", help="Skip benchmarking")
    parser.add_argument("--benchmark-prompt", type=str, default="def fibonacci(n):", help="Prompt to use for benchmarking")
    parser.add_argument("--benchmark-runs", type=int, default=5, help="Number of benchmark runs")
    
    args = parser.parse_args()
    
    # Create optimizer
    optimizer = ModelOptimizer(
        model_path=args.model_path,
        output_path=args.output_path,
        device=args.device,
        precision=args.precision
    )
    
    # Run optimization
    metrics = optimizer.optimize(
        apply_torch_compile=not args.no_torch_compile,
        optimize_attention=not args.no_attention_optim,
        optimize_memory=not args.no_memory_optim,
        run_benchmark=not args.no_benchmark
    )
    
    # Print summary
    print("\nOptimization Summary:")
    print("=" * 50)
    if "benchmark" in metrics:
        print(f"Average latency: {metrics['benchmark']['average_latency_seconds']:.4f} seconds")
        print(f"Generation speed: {metrics['benchmark']['average_tokens_per_second']:.2f} tokens/second")
    print(f"Total time: {metrics.get('total_optimization_time_seconds', 0):.2f} seconds")
    print("=" * 50)

if __name__ == "__main__":
    main()
