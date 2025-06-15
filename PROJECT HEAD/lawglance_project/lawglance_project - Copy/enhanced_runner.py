"""
Enhanced runner script for Lawglance with improved components.
"""
import os
import sys
import logging
from pathlib import Path

# Add project path to Python path for imports
project_path = Path(__file__).parent
if str(project_path) not in sys.path:
    sys.path.append(str(project_path))

# Import improved components
from config import Config
from document_cache import DocumentCache
from document_processor import DocumentProcessor
from lawglance_integration import LawglanceIntegration
from performance_utils import timing, performance_monitor

def setup_lawglance():
    """Set up Lawglance with enhanced components.
    
    Returns:
        Initialized Lawglance instance
    """
    # Load configuration
    config = Config("lawglance_config.json")
    
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, config.get("logging", "level")),
        format=config.get("logging", "format"),
        filename=config.get("logging", "file")
    )
    
    logger = logging.getLogger("lawglance.setup")
    logger.info("Setting up Lawglance with enhanced components")
    
    # Set Hugging Face token from config
    huggingface_token = config.get("api_keys", "huggingface_token")
    os.environ["HUGGINGFACE_API_TOKEN"] = huggingface_token
    
    # Initialize transformers and langchain
    try:
        from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
        from langchain.llms import HuggingFaceHub
        from langchain.embeddings import HuggingFaceEmbeddings
        from langchain.vectorstores import FAISS
        
        # Import Lawglance
        from lawglance_main import Lawglance
        
        # Initialize LLM
        llm = HuggingFaceHub(
            repo_id=config.get("models", "llm"),
            model_kwargs={"temperature": 0.1, "max_length": 512},
            huggingfacehub_api_token=huggingface_token
        )
        
        # Initialize embeddings
        embeddings_model_name = config.get("models", "embeddings")
        embeddings = HuggingFaceEmbeddings(
            model_name=embeddings_model_name,
            model_kwargs={"device": "cpu"}
        )
        
        # Create vector store with sample data
        logger.info("Creating vector store")
        texts = [
            "A contract is a legally binding agreement between two or more parties.",
            "Evidence in legal proceedings must be relevant and admissible.",
            "Jurisdiction refers to the authority of a court to hear and decide a case.",
            "Damages are monetary compensation awarded to a person who has suffered loss."
        ]
        vector_store = FAISS.from_texts(texts, embeddings)
        
        # Initialize basic Lawglance
        logger.info("Initializing Lawglance")
        lawglance = Lawglance(llm, embeddings, vector_store)
        
        # Enhance with improved components
        integration = LawglanceIntegration("lawglance_config.json")
        lawglance = integration.setup_lawglance(lawglance)
        
        logger.info("Lawglance setup complete")
        return lawglance
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        print(f"Error importing required libraries: {e}")
        print("Please install the required dependencies.")
        return None
    except Exception as e:
        logger.error(f"Setup error: {e}")
        print(f"Error setting up Lawglance: {e}")
        return None

@timing
def process_query(lawglance, query):
    """Process a query with timing measurement.
    
    Args:
        lawglance: Lawglance instance
        query: Query string
        
    Returns:
        Response from Lawglance
    """
    return lawglance.conversational(query)

def run_interactive_mode():
    """Run the system in interactive mode."""
    print("Setting up Lawglance...")
    lawglance = setup_lawglance()
    
    if not lawglance:
        print("Failed to initialize Lawglance.")
        return
    
    print("\n" + "=" * 60)
    print("Enhanced Lawglance Interactive Mode")
    print("=" * 60)
    print("Type 'exit' or 'quit' to exit.")
    print("Type 'stats' to show performance stats.")
    print("Type 'help' for example commands.")
    print("=" * 60 + "\n")
    
    def print_help():
        print("\nExample commands:")
        print("- What is a legal contract?")
        print("- process document [path/to/file] analyze")
        print("- compare documents [path/to/file1] and [path/to/file2]")
        print("- extract entities from [path/to/file]")
        print("- extract arguments from [path/to/file]")
    
    while True:
        query = input("\nQuery: ").strip()
        
        if query.lower() in ["exit", "quit"]:
            break
        elif query.lower() == "stats":
            performance_monitor.print_report()
        elif query.lower() == "help":
            print_help()
        elif query:
            try:
                start_time = time.time()
                response = process_query(lawglance, query)
                end_time = time.time()
                
                print("\nResponse:")
                print("-" * 60)
                print(response)
                print("-" * 60)
                print(f"[Processed in {end_time - start_time:.2f}s]")
            except Exception as e:
                print(f"Error processing query: {e}")
    
    print("\nExiting Lawglance. Thank you for using our system!")

if __name__ == "__main__":
    # Add local dependencies path to Python path
    sys.path.insert(0, str(project_path))
    
    try:
        import time
        run_interactive_mode()
    except KeyboardInterrupt:
        print("\nExiting Lawglance.")
    except Exception as e:
        print(f"Unexpected error: {e}")
