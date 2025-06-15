"""Utility for loading legal documents into the vector store."""
import os
import argparse
import logging
from typing import List, Dict, Any, Optional
from tqdm import tqdm
from langchain_community.document_loaders import (
    TextLoader, 
    PDFMinerLoader, 
    DirectoryLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('document_loader')

class DocumentLoader:
    """Utility class for loading and processing documents for the vector store."""
    
    def __init__(self, persist_directory: str = "chroma_db_legal_bot_part1"):
        """Initialize the document loader with embeddings and vector store."""
        load_dotenv()
        
        self.persist_directory = persist_directory
        self.embeddings = OpenAIEmbeddings()
        
        # Create vector store directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize vector store
        self.vector_store = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", " ", ""]
        )
    
    def load_documents(self, directory_path: str) -> List[Dict[str, Any]]:
        """
        Load documents from a directory.
        
        Args:
            directory_path: Path to directory containing documents
            
        Returns:
            List of document objects
        """
        logger.info(f"Loading documents from {directory_path}")
        
        # Check if directory exists
        if not os.path.exists(directory_path):
            logger.error(f"Directory {directory_path} not found")
            return []
        
        # Set up loaders for different file types
        txt_loader = DirectoryLoader(
            directory_path, 
            glob="**/*.txt",
            loader_cls=TextLoader
        )
        
        pdf_loader = DirectoryLoader(
            directory_path,
            glob="**/*.pdf",
            loader_cls=PDFMinerLoader
        )
        
        # Load documents
        logger.info("Loading text documents...")
        txt_docs = txt_loader.load()
        logger.info(f"Loaded {len(txt_docs)} text documents")
        
        logger.info("Loading PDF documents...")
        pdf_docs = pdf_loader.load()
        logger.info(f"Loaded {len(pdf_docs)} PDF documents")
        
        all_docs = txt_docs + pdf_docs
        logger.info(f"Total: Loaded {len(all_docs)} documents")
        
        return all_docs
    
    def process_documents(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process documents by splitting them into chunks.
        
        Args:
            docs: List of document objects
            
        Returns:
            List of document chunks
        """
        logger.info("Processing documents...")
        if not docs:
            logger.warning("No documents to process")
            return []
        
        # Split documents into chunks
        splits = self.text_splitter.split_documents(docs)
        logger.info(f"Created {len(splits)} document chunks")
        
        return splits
    
    def add_to_vectorstore(self, docs: List[Dict[str, Any]]) -> None:
        """
        Add processed document chunks to the vector store.
        
        Args:
            docs: List of document chunks to add to vector store
        """
        if not docs:
            logger.warning("No document chunks to add to vector store")
            return
            
        logger.info(f"Adding {len(docs)} document chunks to vector store")
        
        # Add documents to vector store with progress bar
        for i in tqdm(range(0, len(docs), 100), desc="Adding documents"):
            end_idx = min(i + 100, len(docs))
            batch = docs[i:end_idx]
            self.vector_store.add_documents(batch)
        
        logger.info("Documents added to vector store successfully")

def main():
    """Main function to run the document loader."""
    parser = argparse.ArgumentParser(
        description="Load legal documents into the vector store"
    )
    parser.add_argument(
        "directory",
        type=str,
        help="Directory containing documents to load"
    )
    parser.add_argument(
        "--persist_dir",
        type=str,
        default="chroma_db_legal_bot_part1",
        help="Directory to persist the vector store"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        loader = DocumentLoader(persist_directory=args.persist_dir)
        docs = loader.load_documents(args.directory)
        processed_docs = loader.process_documents(docs)
        loader.add_to_vectorstore(processed_docs)
        
        logger.info("Document loading complete!")
    except Exception as e:
        logger.error(f"Error loading documents: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
