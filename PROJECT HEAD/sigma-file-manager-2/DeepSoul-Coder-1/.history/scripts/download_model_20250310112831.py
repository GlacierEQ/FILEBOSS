"""
Script to download model weights during Docker initialization
"""
import os
import argparse
import logging
from pathlib import Path
from huggingface_hub import snapshot_download
import torch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("DeepSoul-ModelDownloader")

# Model repository mappings - update with actual model repos
MODEL_REPOS = {
    "base": "deepseek-ai/deepseek-coder-6.7b-base",
    "large": "deepseek-ai/deepseek-coder-33b-instruct",
}

def download_model(model_size: str) -> Path:
    """
    Download model weights from Hugging Face Hub
    
    Args:
        model_size: Size of model to download (base or large)
        
    Returns:
        Path to downloaded model
    """
    if model_size not in MODEL_REPOS:
        raise ValueError(f"Unknown model size: {model_size}. Available options: {list(MODEL_REPOS.keys())}")
    
    repo_id = MODEL_REPOS[model_size]
    logger.info(f"Downloading model {repo_id}")
    
    # Get model directory
    model_dir = os.environ.get("MODEL_PATH", "./models")
    os.makedirs(model_dir, exist_ok=True)
    
    # Download the model
    try:
        model_path = snapshot_download(
            repo_id=repo_id,
            cache_dir=os.path.join(model_dir, model_size),
            local_dir=os.path.join(model_dir, model_size),
            local_dir_use_symlinks=False
        )
        
        logger.info(f"Model downloaded to {model_path}")
        return Path(model_path)
        
    except Exception as e:
        logger.error(f"Error downloading model: {str(e)}")
        raise

def check_gpu():
    """Check GPU availability and print information"""
    if torch.cuda.is_available():
        gpu_count = torch.cuda.device_count()
        logger.info(f"Found {gpu_count} GPU(s):")
        for i in range(gpu_count):
            logger.info(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
        logger.info(f"Current device: {torch.cuda.current_device()}")
    else:
        logger.warning("No GPU available - model will run on CPU only")

def main():
    parser = argparse.ArgumentParser(description="Download model weights")
    parser.add_argument("--model", choices=["base", "large"], default="base", help="Model size to download")
    args = parser.parse_args()
    
    check_gpu()
    download_model(args.model)
    
    # Create a flag file to indicate model has been downloaded
    with open(os.path.join(os.environ.get("DATA_DIR", "./data"), ".models_initialized"), "w") as f:
        f.write(f"Model initialized: {args.model}")
    
if __name__ == "__main__":
    main()
