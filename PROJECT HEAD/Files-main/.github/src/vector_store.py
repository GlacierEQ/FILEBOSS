import chromadb
from chromadb.config import Settings
import asyncio
from typing import List, Dict, Optional
import json
from pathlib import Path

class VectorStore:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None

    async def initialize(self):
        """Initialize ChromaDB"""
        self.client = chromadb.Client(Settings(
            persist_directory=self.persist_directory,
            chroma_db_impl="duckdb+parquet"
        ))

        self.collection = self.client.get_or_create_collection(
            name="codexflo_documents",
            metadata={"description": "Legal documents and case files"}
        )

    async def store_file_embedding(self, file_path: Path, metadata: Dict):
        """Store file content and metadata as embeddings"""
        try:
            # Create document ID
            doc_id = str(file_path).replace("/", "_").replace("\\", "_")

            # Prepare content for embedding
            content = metadata.get("content_preview", "")

            # Store in ChromaDB
            self.collection.add(
                documents=[content],
                metadatas=[{
                    "file_path": str(file_path),
                    "document_type": metadata.get("document_type", "unknown"),
                    "case_relevance": metadata.get("case_relevance", 0),
                    "tags": json.dumps(metadata.get("tags", [])),
                    "processed_date": metadata.get("processed_date", ""),
                    "urgency_level": metadata.get("urgency_level", "low")
                }],
                ids=[doc_id]
