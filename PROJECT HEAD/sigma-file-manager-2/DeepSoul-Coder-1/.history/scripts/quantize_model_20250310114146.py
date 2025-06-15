"""
Script for quantizing DeepSeek Coder models to reduce memory footprint
"""
import os
import sys
import argparse
import logging
import torch
from pathlib import Path
from typing import Optional, Dict, Any
from transformers import AutoTokenizer, AutoModelForCausalLM

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("DeepSoul-ModelQuantizer")

def get_model_info(model_path: str) -> Dict[str, Any]:
    """
    Get information about the model, such as size and architecture
    """
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    
    # Get model size estimate without loading weights
    model_info = {}
    try:
        config = AutoModelForCausalLM.config_class.from_pretrained(model_path, trust_remote_code=True)
        model_info["architecture"] = config.architectures[0] if hasattr(config, "architectures") else "Unknown"
        model_info["vocab_size"] = config.vocab_size if hasattr(config, "vocab_size") else 0
        model_info["hidden_size"] = config.hidden_size if hasattr(config, "hidden_size") else 0
        model_info["num_layers"] = config.num_hidden_layers if hasattr(config, "num_hidden_layers") else 0
        model_info["tokenizer_type"] = type(tokenizer).__name__
        
        # Estimate size in GB
        num_params = 0
        if hasattr(config, "num_parameters"):
            num_params = config.num_parameters
        elif hasattr(config, "hidden_size") and hasattr(config, "num_hidden_layers"):
            # Rough estimate based on architecture
            intermediate_size = getattr(config, "intermediate_size", config.hidden_size * 4)
            num_params = (
                12 * config.num_hidden_layers * (config.hidden_size ** 2)  # Self-attention
                + 12 * config.num_hidden_layers * config.hidden_size * intermediate_size  # FF
                + config.vocab_size * config.hidden_size  # Embeddings
            )
        model_info["estimated_params"] = num_params
        model_info["estimated_size_gb"] = num_params * 4 / (1024**3)  # FP32 size
        
        return model_info
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        return {"error": str(e)}

def quantize_model_bitsandbytes(
    model_path: str, 
    output_path: str, 
    quantization_type: str = "4bit"
) -> Optional[str]:
    """
    Quantize a model using bitsandbytes library
    
    Args:
        model_path: Path to the original model
        output_path: Path to save the quantized model
        quantization_type: Type of quantization (4bit or 8bit)
        
    Returns:
        Path to the quantized model if successful, None otherwise
    """
    try:
        os.makedirs(output_path, exist_ok=True)
        
        # Import bitsandbytes
        import bitsandbytes as bnb
        from transformers import BitsAndBytesConfig
        
        # Set quantization config
        if quantization_type == "4bit":
            quant_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
        else:  # 8bit
            quant_config = BitsAndBytesConfig(
                load_in_8bit=True,
            )
        
        # Load and quantize model
        logger.info(f"Loading model from {model_path} with {quantization_type} quantization...")
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            quantization_config=quant_config,
            device_map="auto",
            trust_remote_code=True
        )
        
        # Save quantized model
        logger.info(f"Saving quantized model to {output_path}...")
        model.save_pretrained(output_path)
        tokenizer.save_pretrained(output_path)
        
        logger.info(f"Model quantized successfully to {output_path}")
        return output_path
    except ImportError:
        logger.error("bitsandbytes library not found. Install with 'pip install bitsandbytes'")
        return None
    except Exception as e:
        logger.error(f"Error quantizing model: {str(e)}")
        return None

def quantize_model_gguf(
    model_path: str,
    output_path: str,
    quantization_type: str = "q4_k_m"
) -> Optional[str]:
    """
    Quantize model to GGUF format for use with llama.cpp
    
    Args:
        model_path: Path to the original model
        output_path: Path to save the quantized model
        quantization_type: GGUF quantization type (q4_0, q4_k_m, q5_k_m, q8_0)
        
    Returns:
        Path to the quantized model if successful, None otherwise
    """
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # First convert from HF to GGUF format
        import subprocess
        
        # Check if llama.cpp is available in PATH or in the project directory
        convert_script = "convert-hf-to-gguf.py"
        convert_paths = [
            convert_script,
            os.path.join("llama.cpp", convert_script),
            os.path.join("..", "llama.cpp", convert_script),
            os.path.join(os.path.expanduser("~"), "llama.cpp", convert_script)
        ]
        
        convert_script_path = None
        for path in convert_paths:
            if os.path.exists(path):
                convert_script_path = path
                break
        
        if not convert_script_path:
            logger.error("Could not find convert-hf-to-gguf.py script. Please ensure llama.cpp is installed.")
            return None
        
        # Convert to GGUF
        logger.info(f"Converting {model_path} to GGUF format...")
        gguf_output = f"{output_path}.gguf"
        convert_cmd = [
            sys.executable, convert_script_path,
            model_path,
            "--outfile", gguf_output,
            "--model-name", "deepseekcoder"
        ]
        
        result = subprocess.run(convert_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"GGUF conversion failed: {result.stderr}")
            return None
        
        # Quantize the model
        logger.info(f"Quantizing to {quantization_type} format...")
        quantize_paths = [
            "quantize",
            os.path.join("llama.cpp", "quantize"),
            os.path.join("..", "llama.cpp", "quantize"),
            os.path.join(os.path.expanduser("~"), "llama.cpp", "quantize")
        ]
        
        quantize_path = None
        for path in quantize_paths:
            if os.path.exists(path) or os.path.exists(path + ".exe"):
                quantize_path = path
                break
        
        if not quantize_path:
            logger.error("Could not find quantize executable. Please ensure llama.cpp is installed and compiled.")
            return None
        
        # Run quantization
        quantize_cmd = [
            quantize_path,
            gguf_output,
            output_path,
            quantization_type
        ]
        
        result = subprocess.run(quantize_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Quantization failed: {result.stderr}")
            return None
            
        logger.info(f"Model quantized successfully to {output_path}")
        return output_path
            
    except Exception as e:
        logger.error(f"Error quantizing model to GGUF: {str(e)}")
        return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Quantize DeepSeek Coder models")
    parser.add_argument("--model-path", type=str, required=True, help="Path to the model or model ID on HuggingFace")
    parser.add_argument("--output-path", type=str, required=True, help="Path to save the quantized model")
    parser.add_argument("--method", type=str, choices=["bitsandbytes", "gguf"], default="bitsandbytes", 
                        help="Quantization method to use")
    parser.add_argument("--type", type=str, choices=["4bit", "8bit", "q4_0", "q4_k_m", "q5_k_m", "q8_0"], 
                        default="4bit", help="Quantization type")
    
    args = parser.parse_args()
    
    # Show model info before quantization
    logger.info(f"Analyzing model: {args.model_path}")
    model_info = get_model_info(args.model_path)
    for key, value in model_info.items():
        logger.info(f"  {key}: {value}")
    
    # Choose quantization method
    if args.method == "bitsandbytes":
        if args.type not in ["4bit", "8bit"]:
            logger.error(f"Invalid quantization type for bitsandbytes: {args.type}")
            return
        quantize_model_bitsandbytes(args.model_path, args.output_path, args.type)
    elif args.method == "gguf":
        if args.type not in ["q4_0", "q4_k_m", "q5_k_m", "q8_0"]:
            logger.error(f"Invalid quantization type for GGUF: {args.type}")
            return
        quantize_model_gguf(args.model_path, args.output_path, args.type)
    else:
        logger.error(f"Unsupported quantization method: {args.method}")
        return
    
if __name__ == "__main__":
    main()
