"""Runner script for the Lawglance system.
This script:
1. Ensures the Hugging Face token is set
2. Sets up the required environment
3. Initializes and runs the Lawglance system
"""
import os
import sys
import json
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lawglance.runner")

# Add the project path to Python path
project_path = Path(__file__).parent.parent
if str(project_path) not in sys.path:
    sys.path.append(str(project_path))

# Constants
CONFIG_DIR = Path.home() / ".lawglance"
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN", "YOUR_DEFAULT_TOKEN")

def setup_environment():
    """Set up the environment for running Lawglance."""
    logger.info("Setting up environment...")
    
    # Load token from config file if available
    token = DEFAULT_TOKEN
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding='utf-8') as f:
                config = json.load(f)
                token = config.get("huggingface_token", DEFAULT_TOKEN)
        except json.JSONDecodeError as e:
            logger.warning(f"Could not read config file. Using default token. Error: {e}")
    
    # Set token in environment
    os.environ["HUGGINGFACE_API_TOKEN"] = token
    logger.info(f"Using Hugging Face token: {token[:5]}...{token[-5:]}")
    
    return True

def run_lawglance():
    """Initialize and run the Lawglance system."""
    try:
        from langchain.llms import HuggingFaceHub
        from langchain.embeddings import HuggingFaceEmbeddings
        from langchain.vectorstores import FAISS
        
        # Import our main module
        from lawglance_main import Lawglance
        
        logger.info("Initializing Lawglance system...")
        
        # Initialize LLM
        llm = HuggingFaceHub(
            repo_id="google/flan-t5-base",  # Start with a smaller model for testing
            model_kwargs={"temperature": 0.1, "max_length": 512},
            huggingfacehub_api_token=os.environ["HUGGINGFACE_API_TOKEN"]
        )
        
        # Initialize embeddings
        embeddings = HuggingFaceEmbeddings(
            model_kwargs={"token": os.environ["HUGGINGFACE_API_TOKEN"]}
        )
        
        # Create a simple vector store for testing
        logger.info("Creating test vector store...")
        texts = [
            "A contract is a legally binding agreement between two or more parties.",
            "Legal documents often contain specific terms and conditions.",
            "Law is a system of rules created and enforced through social or governmental institutions."
        ]
        vector_store = FAISS.from_texts(texts, embeddings)
        
        # Initialize Lawglance
        lawglance = Lawglance(llm, embeddings, vector_store)
        logger.info("Lawglance initialized successfully!")
        
        # Interactive mode
        logger.info("\n" + "=" * 60)
        logger.info("Lawglance Interactive Mode")
        logger.info("=" * 60)
        logger.info("Type 'exit' to quit.")
        logger.info("Example commands:")
        logger.info("- What is a legal contract?")
        logger.info("- process document [file_path] analyze")
        logger.info("- compare documents [file_path1] and [file_path2]")
        logger.info("=" * 60 + "\n")
        
        while True:
            query = input("Query: ").strip()
            if query.lower() in ["exit", "quit", "q"]:
                break
                
            try:
                response = lawglance.conversational(query)
                logger.info("\nResponse:")
                logger.info("-" * 60)
                logger.info(response)
                logger.info("-" * 60 + "\n")
            except Exception as e:
                logger.error(f"\nError: {e}")
        
        logger.info("Exiting Lawglance. Thank you for using our system!")
        return True
        
    except ImportError as e:
        logger.error(f"Error: Required module not found: {e}")
        logger.info("Please run setup_huggingface.py first to install all dependencies.")
        return False
    except Exception as e:
        logger.error(f"Error running Lawglance: {e}")
        return False

if __name__ == "__main__":
    if setup_environment():
        run_lawglance()
