"""Command line interface for LawGlance."""
import os
import sys
import argparse
import logging
from typing import List, Optional
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.lawglance_main import Lawglance
from src.utils.config_manager import ConfigManager
from src.utils.document_loader import DocumentLoader
from src.utils.document_editor import DocumentEditor
from src.utils.document_compare import DocumentCompare
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lawglance.cli")

class LawglanceCLI:
    """Command line interface for LawGlance."""

    def __init__(self):
        """Initialize the CLI."""
        self.config = ConfigManager()
        self.lawglance = None
        self.document_loader = None
        self.document_editor = None
        self.document_compare = None

    def setup(self) -> bool:
        """
        Set up LawGlance and related components.

        Returns:
            True if setup was successful, False otherwise
        """
        load_dotenv()

        try:
            # Get OpenAI API key
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if not openai_api_key:
                logger.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
                raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
                return False

            # Initialize components
            model_name = os.getenv('MODEL_NAME', 'gpt-4o-mini')
            temperature = float(os.getenv('MODEL_TEMPERATURE', '0.9'))
            vector_store_dir = os.getenv('VECTOR_STORE_DIR', 'chroma_db_legal_bot_part1')

            # Create vector store directory if it doesn't exist
            os.makedirs(vector_store_dir, exist_ok=True)

            # Initialize LLM
            llm = ChatOpenAI(model=model_name, temperature=temperature, openai_api_key=openai_api_key)

            # Initialize embeddings
            embeddings = OpenAIEmbeddings()

            # Initialize vector store
            vector_store = Chroma(persist_directory=vector_store_dir, embedding_function=embeddings)

            # Initialize LawGlance
            self.lawglance = Lawglance(llm, embeddings, vector_store)

            # Initialize document loader
            self.document_loader = DocumentLoader(persist_directory=vector_store_dir)

            # Initialize document editor
            self.document_editor = DocumentEditor()

            # Initialize document compare
            self.document_compare = DocumentCompare()

            logger.info("LawGlance CLI setup complete")
            return True

        except Exception as e:
            logger.error(f"Error setting up LawGlance: {e}")
            return False

    def ask(self, question: str) -> str:
        """
        Ask a question to LawGlance.

        Args:
            question: Question to ask

        Returns:
            LawGlance response
        """
        if not self.lawglance:
            if not self.setup():
                logger.error("LawGlance not initialized. Setup failed.")
                return "Error: LawGlance not initialized. Please check the setup."

        try:
            return self.lawglance.conversational(question)
        except Exception as e:
            logger.error(f"Error asking question: {e}")
            return f"Error: {str(e)}"

    def load_documents(self, directory: str) -> str:
        """
        Load documents from a directory.

        Args:
            directory: Directory containing documents to load

        Returns:
            Status message
        """
        if not self.document_loader:
            if not self.setup():
                logger.error("Document loader not initialized. Setup failed.")
                return "Error: Document loader not initialized. Please check the setup."

        try:
            docs = self.document_loader.load_documents(directory)
            processed_docs = self.document_loader.process_documents(docs)
            self.document_loader.add_to_vectorstore(processed_docs)
            return f"Successfully loaded {len(docs)} documents with {len(processed_docs)} chunks."
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            return f"Error loading documents: {str(e)}"

    def edit_document(self, file_path: str, instructions: str) -> str:
        """
        Edit a document based on natural language instructions.

        Args:
            file_path: Path to the document
            instructions: Natural language instructions for editing

        Returns:
            Status message
        """
        if not self.document_editor:
            if not self.setup():
                logger.error("Document editor not initialized. Setup failed.")
                return "Error: Document editor not initialized. Please check the setup."

        try:
            return self.document_editor.edit_document(file_path, instructions)
        except Exception as e:
            logger.error(f"Error editing document: {e}")
            return f"Error editing document: {str(e)}"

    def compare_documents(self, file1: str, file2: str) -> str:
        """
        Compare two documents.

        Args:
            file1: Path to first document
            file2: Path to second document

        Returns:
            Comparison summary
        """
        if not self.document_compare:
            if not self.setup():
                logger.error("Document compare not initialized. Setup failed.")
                return "Error: Document compare not initialized. Please check the setup."

        try:
            result = self.document_compare.compare_files(file1, file2)
            return result.summary
        except Exception as e:
            logger.error(f"Error comparing documents: {e}")
            return f"Error comparing documents: {str(e)}"

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="LawGlance command line interface")

    # Create subparsers
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Ask command
    ask_parser = subparsers.add_parser("ask", help="Ask a question")
    ask_parser.add_argument("question", type=str, help="Question to ask")

    # Load documents command
    load_parser = subparsers.add_parser("load", help="Load documents")
    load_parser.add_argument("directory", type=str, help="Directory containing documents")

    # Edit document command
    edit_parser = subparsers.add_parser("edit", help="Edit a document")
    edit_parser.add_argument("file", type=str, help="File to edit")
    edit_parser.add_argument("instructions", type=str, help="Editing instructions")

    # Compare documents command
    compare_parser = subparsers.add_parser("compare", help="Compare two documents")
    compare_parser.add_argument("file1", type=str, help="First file")
    compare_parser.add_argument("file2", type=str, help="Second file")

    # Parse arguments
    args = parser.parse_args()

    # Create CLI
    cli = LawGlanceCLI()

    # Run command
    if args.command == "ask":
        print(cli.ask(args.question))
    elif args.command == "load":
        print(cli.load_documents(args.directory))
    elif args.command == "edit":
        print(cli.edit_document(args.file, args.instructions))
    elif args.command == "compare":
        print(cli.compare_documents(args.file1, args.file2))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
