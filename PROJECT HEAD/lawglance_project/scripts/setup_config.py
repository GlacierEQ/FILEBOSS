o"""Script to setup initial configuration for LawGlance."""
import os
import sys
import json
import shutil
import argparse
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.utils.config_manager import ConfigManager

def setup_config(model: str = "gpt-4o-mini", temp: float = 0.9, 
                vector_dir: str = "chroma_db_legal_bot_part1") -> bool:
    """
    Set up configuration for LawGlance.
    
    Args:
        model: Model name
        temp: Temperature
        vector_dir: Vector store directory
        
    Returns:
        True if setup was successful, False otherwise
    """
    try:
        config = ConfigManager()
        
        # Set up configuration
        config.set("MODEL_NAME", model)
        config.set("MODEL_TEMPERATURE", temp)
        config.set("VECTOR_STORE_DIR", vector_dir)
        
        # Save configuration
        config.save_config()
        
        print(f"Configuration saved to {config.config_path}")
        return True
    except Exception as e:
        print(f"Error setting up configuration: {e}")
        return False

def create_env_file() -> bool:
    """
    Create .env file from template if it doesn't exist.
    
    Returns:
        True if .env file was created or already exists, False otherwise
    """
    env_file = os.path.join(project_root, ".env")
    example_file = os.path.join(project_root, ".env.example")
    
    if os.path.exists(env_file):
        print(f".env file already exists at {env_file}")
        return True
    
    if not os.path.exists(example_file):
        print(f"Error: .env.example file not found at {example_file}")
        return False
    
    try:
        shutil.copy(example_file, env_file)
        print(f"Created .env file at {env_file}")
        print("Please edit the .env file to add your OpenAI API key.")
        return True
    except Exception as e:
        print(f"Error creating .env file: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Setup configuration for LawGlance")
    parser.add_argument("--model", type=str, default="gpt-4o-mini", help="Model name")
    parser.add_argument("--temp", type=float, default=0.9, help="Temperature")
    parser.add_argument("--vector-dir", type=str, default="chroma_db_legal_bot_part1", help="Vector store directory")
    
    args = parser.parse_args()
    
    # Create .env file
    create_env_file()
    
    # Setup configuration
    success = setup_config(args.model, args.temp, args.vector_dir)
    
    if success:
        print("\nConfiguration setup complete!")
        print("To start using LawGlance:")
        print("1. Edit the .env file to add your OpenAI API key")
        print("2. Run the Streamlit app: streamlit run app.py")
        print("3. Or use the CLI: python -m src.cli ask \"Your question here\"")
    else:
        print("Configuration setup failed!")

if __name__ == "__main__":
    main()
