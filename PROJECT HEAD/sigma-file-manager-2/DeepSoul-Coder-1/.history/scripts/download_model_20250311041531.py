#!/usr/bin/env python3
"""
Download script for DeepSeek-Coder model weights.

This script downloads model weights from Hugging Face or a custom source
and prepares them for use with the DeepSeek-Coder API server.
"""

import os
import sys
import argparse
import logging
import time
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("model-downloader")

# Model versions and their Hugging Face repos
MODEL_REPOS = {
    "base": "deepseek-ai/deepseek-coder-6.7b-base",
    "instruct": "deepseek-ai/deepseek-coder-6.7b-instruct",
    "large-base": "deepseek-ai/deepseek-coder-33b-base",
    "large-instruct": "deepseek-ai/deepseek-coder-33b-instruct",
}

class ModelDownloader:
    """Downloader for DeepSeek-Coder models."""
    
    def __init__(self, output_dir: str = "models", use_hf_transfer: bool = True):
        """
        Initialize the model downloader.
        
        Args:
            output_dir: Directory to save models
            use_hf_transfer: Use huggingface-cli for faster downloads if available
        """
        self.output_dir = output_dir
        self.use_hf_transfer = use_hf_transfer
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
    def check_huggingface_cli(self) -> bool:
        """
        Check if huggingface-cli is available.
        
        Returns:
            True if huggingface-cli is available
        """
        try:
            subprocess.check_call(
                ["huggingface-cli", "--help"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def download_with_hf_transfer(self, model_id: str, output_path: str) -> bool:
        """
        Download a model using huggingface-cli.
        
        Args:
            model_id: Hugging Face model ID
            output_path: Output directory path
        
        Returns:
            True if download was successful
        """
        try:
            cmd = ["huggingface-cli", "download", "--resume-download", 
                   model_id, "--local-dir", output_path]
            logger.info(f"Running: {' '.join(cmd)}")
            subprocess.check_call(cmd)
            return True
        except subprocess.SubprocessError as e:
            logger.error(f"Error downloading with huggingface-cli: {e}")
            return False
    
    def download_with_transformers(self, model_id: str, output_path: str) -> bool:
        """
        Download a model using transformers library.
        
        Args:
            model_id: Hugging Face model ID
            output_path: Output directory path
        
        Returns:
            True if download was successful
        """
        try:
            # Import libraries here to keep the script usable without them initially
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            logger.info(f"Downloading tokenizer for {model_id}...")
            tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
            tokenizer.save_pretrained(output_path)
            
            logger.info(f"Downloading model for {model_id}...")
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            model.save_pretrained(output_path)
            
            return True
        except Exception as e:
            logger.error(f"Error downloading with transformers: {e}")
            return False
    
    def download_model(self, model_type: str, custom_repo: Optional[str] = None) -> bool:
        """
        Download a model of the specified type.
        
        Args:
            model_type: Type of model to download (base, instruct, etc.)
            custom_repo: Custom repository URL or path
        
        Returns:
            True if download was successful
        """
        # Get repo ID
        repo_id = custom_repo or MODEL_REPOS.get(model_type)
        
        if not repo_id:
            logger.error(f"Invalid model type: {model_type}")
            logger.info(f"Available model types: {', '.join(MODEL_REPOS.keys())}")
            return False
        
        # Set output path
        output_path = os.path.join(self.output_dir, model_type)
        if os.path.exists(output_path):
            logger.warning(f"Model directory already exists: {output_path}")
            response = input("Continue and overwrite existing files? [y/N]: ")
            if response.lower() != 'y':
                logger.info("Download cancelled by user")
                return False
        else:
            os.makedirs(output_path, exist_ok=True)
        
        # Download the model
        logger.info(f"Downloading model '{repo_id}' to {output_path}")
        start_time = time.time()
        
        # Try huggingface-cli first if available and enabled
        success = False
        if self.use_hf_transfer and self.check_huggingface_cli():
            logger.info("Using huggingface-cli for download (faster)")
            success = self.download_with_hf_transfer(repo_id, output_path)
        
        # Fall back to transformers if needed
        if not success:
            logger.info("Using transformers library for download")
            success = self.download_with_transformers(repo_id, output_path)
        
        elapsed = time.time() - start_time
        
        if success:
            logger.info(f"Model downloaded successfully in {elapsed:.1f} seconds")
            logger.info(f"Model files saved to: {output_path}")
            return True
        else:
            logger.error(f"Failed to download model after {elapsed:.1f} seconds")
            return False
    
    def list_available_models(self) -> List[str]:
        """
        List available model types.
        
        Returns:
            List of available model types
        """
        return list(MODEL_REPOS.keys())
    
    def list_downloaded_models(self) -> List[str]:
        """
        List already downloaded models.
        
        Returns:
            List of downloaded model types
        """
        if not os.path.exists(self.output_dir):
            return []
        
        downloaded = []
        for model_type in MODEL_REPOS.keys():
            model_dir = os.path.join(self.output_dir, model_type)
            if os.path.exists(model_dir):
                # Check for model files
                model_files = list(Path(model_dir).glob("*.safetensors")) + list(Path(model_dir).glob("*.bin"))
                if model_files:
                    downloaded.append(model_type)
        
        return downloaded


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="DeepSeek-Coder Model Downloader")
    parser.add_argument(
        "--model",
        type=str,
        choices=list(MODEL_REPOS.keys()) + ["all"],
        default="base",
        help="Model type to download"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models",
        help="Directory to save models"
    )
    parser.add_argument(
        "--custom-repo",
        type=str,
        help="Custom Hugging Face repository ID"
    )
    parser.add_argument(
        "--no-hf-transfer",
        action="store_true",
        help="Disable huggingface-cli for downloads"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available and downloaded models"
    )
    
    args = parser.parse_args()
    
    downloader = ModelDownloader(
        output_dir=args.output_dir,
        use_hf_transfer=not args.no_hf_transfer
    )
    
    if args.list:
        available = downloader.list_available_models()
        downloaded = downloader.list_downloaded_models()
        
        print("\nAvailable models:")
        for model in available:
            status = " [DOWNLOADED]" if model in downloaded else ""
            print(f"  - {model}{status}")
        print(f"\nOutput directory: {args.output_dir}")
        return 0
    
    if args.model == "all":
        success = True
        for model_type in MODEL_REPOS.keys():
            model_success = downloader.download_model(model_type)
            success = success and model_success
        return 0 if success else 1
    else:
        success = downloader.download_model(args.model, args.custom_repo)
        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
