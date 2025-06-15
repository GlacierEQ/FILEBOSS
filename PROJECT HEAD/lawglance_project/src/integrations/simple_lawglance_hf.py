"""Integration for simple Lawglance functionality."""
import os
import json
import logging
from typing import Dict

# Import verify_token from utils.huggingface_setup
from utils.huggingface_setup import verify_token

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lawglance.integration")

def load_config() -> Dict:
    """Load configuration from a JSON file."""
    config_path = os.path.join(os.path.expanduser("~"), ".lawglance", "config.json")
    if not os.path.exists(config_path):
        logger.error("Configuration file not found.")
        return {}
    
    with open(config_path, "r", encoding='utf-8') as f:
        return json.load(f)

def main():
    """Main function to run the integration."""
    logger.info("Starting Lawglance integration...")
    
    # Verify Hugging Face token
    if not verify_token():
        logger.error("Hugging Face token verification failed.")
        return
    
    # Load configuration
    config = load_config()
    if not config:
        logger.error("Failed to load configuration.")
        return
    
    logger.info("Lawglance integration completed successfully.")

if __name__ == "__main__":
    main()
