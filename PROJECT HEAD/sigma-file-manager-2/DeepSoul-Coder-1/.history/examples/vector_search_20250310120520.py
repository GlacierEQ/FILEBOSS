"""
DeepSeek-Coder Vector Database Integration Example
This example demonstrates how to index code snippets in a vector database
and perform semantic code search.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import torch
from transformers import AutoTokenizer, AutoModel
from tqdm import tqdm

# Elasticsearch imports
try:
    from elasticsearch import Elasticsearch
    from elasticsearch.helpers import bulk
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False

# FAISS imports
try:
    import faiss
    import numpy as np
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


class CodeEmbeddingModel:
    """Code embedding model using DeepSeek-Coder."""
    
    def __init__(self, model_name: str = "deepseek-ai/deepseek-coder-6.7b-base"):
        """Initialize the embedding model."""
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")
        
        # Load tokenizer
        print(f"Loading tokenizer from {model_name}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Load model - only load the embedding layer to save memory
        print(f"Loading model from {model_name}...")
        self.model = AutoModel.from_pretrained(
            model_name,
            trust_remote_code=True,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )
        
        # Move model to device and set to evaluation mode
        self.model.to(self.device)
        self.model.eval()
    
    def encode(self, texts: List[str], batch_size: int = 8) -> torch.Tensor:
        """Encode text to embeddings."""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # Tokenize
            inputs = self.tokenizer(
                batch_texts, 
                return_tensors="pt", 
                padding=True, 
                truncation=True,
                max_length=512
            ).to(self.device)
            
            with torch.no_grad():
                # Get the embeddings from the model
                outputs = self.model(**inputs, output_hidden_states=True)
                
                # Use the [CLS] token embedding from the last hidden state
                batch_embeddings = outputs.hidden_states[-1][:, 0, :]
                embeddings.append(batch_embeddings.cpu())
        
        return torch.cat(embeddings)


class ElasticsearchCodeStore:
    """Code storage and retrieval using Elasticsearch."""
    
    def __init__(self, host: str = "localhost", port: int = 9200, index_name: str = "code-snippets"):
        """Initialize the Elasticsearch client."""
        if not ELASTICSEARCH_AVAILABLE:
            raise ImportError("Elasticsearch not available. Install with: pip install elasticsearch")
        
        self.es = Elasticsearch([f"http://{host}:{port}"])
        self.index_name = index_name
        self._create_index_if_not_exists()
    
    def _create_index_if_not_exists(self):
        """Create the index with appropriate settings if it doesn't exist."""
        if not self.es.indices.exists(index=self.index_name):
            # Create index with the appropriate mapping
            self.es.indices.create(
                index=self.index_name,
                body={
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0
                    },
                    "mappings": {
                        "properties": {
                            "code": {"type": "text"},
                            "language": {"type": "keyword"},
                            "filename": {"type": "keyword"},
                            "embedding": {
                                "type": "dense_vector",
                                "dims": 4096,  # DeepSeek-Coder embedding dimension
                                "similarity": "cosine"
                            },
                            "created_at": {"type": "date"}
                        }
                    }
                }
            )
            print(f"Created index: {self.index_name}")
    
    def index_code(self, code_snippets: List[Dict[str, Any]], embeddings: torch.Tensor):
        """Index code snippets with their embeddings."""
        actions = []
        
        for i, snippet in enumerate(code_snippets):
            # Convert embedding tensor to list
            embedding_list = embeddings[i].tolist()
            
            action = {
                "_index": self.index_name,
                "_id": snippet.get("id", str(i)),
                "_source": {
                    "code": snippet["code"],
                    "language": snippet.get("language", "unknown"),
                    "filename": snippet.get("filename", ""),
                    "embedding": embedding_list,
                    "created_at": snippet.get("created_at", time.strftime("%Y-%m-%dT%H:%M:%S"))
                }
            }
            actions.append(action)
        
        # Bulk index the code snippets
        success, failed = bulk(self.es, actions, refresh=True)
        print(f"Indexed {success} documents, {len(failed)} failed")
    
    def search(self, query_embedding: torch.Tensor, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar code snippets."""
        # Convert query embedding tensor to list
        query_embedding_list = query_embedding.squeeze().tolist()
        
        # Perform k-nearest neighbors search
        response = self.es.search(
            index=self.index_name,
            body={
                "size": top_k,
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                            "params": {"query_vector": query_embedding_list}
                        }
                    }
                }
            }
        )
        
        # Extract results
        results = []
        for hit in response["hits"]["hits"]:
            score = hit["_score"]
            source = hit["_source"]
            results.append({
                "id": hit["_id"],
                "code": source["code"],
                "language": source["language"],
                "filename": source["filename"],
                "similarity": (score - 1.0),  # Convert back from [0,2] to [-1,1]
                "created_at": source["created_at"]
            })
        
        return results


class FaissCodeStore:
    """In-memory code storage and retrieval using FAISS."""
    
    def __init__(self, dimension: int = 4096):
        """Initialize the FAISS index."""
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS not available. Install with: pip install faiss-cpu or faiss-gpu")
        
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)  # Inner product index for cosine similarity
        self.code_snippets = []
    
    def index_code(self, code_snippets: List[Dict[str, Any]], embeddings: torch.Tensor):
        """Index code snippets with their embeddings."""
        # Normalize the embeddings for cosine similarity
        embeddings_np = embeddings.numpy()
        faiss.normalize_L2(embeddings_np)
        
        # Add embeddings to the index
        self.index.add(embeddings_np)
        
        # Store code snippets
        self.code_snippets.extend(code_snippets)
        
        print(f"Indexed {len(code_snippets)} code snippets")
    
    def save(self, filepath: str):
        """Save the index and code snippets."""
        # Save FAISS index
        faiss.write_index(self.index, f"{filepath}.index")
        
        # Save code snippets
        with open(f"{filepath}.json", "w") as f:
            json.dump(self.code_snippets, f)
        
        print(f"Saved index and code snippets to {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> "FaissCodeStore":
        """Load the index and code snippets."""
        store = cls()
        
        # Load FAISS index
        store.index = faiss.read_index(f"{filepath}.index")
        
        # Load code snippets
        with open(f"{filepath}.json", "r") as f:
            store.code_snippets = json.load(f)
        
        print(f"Loaded index with {len(store.code_snippets)} code snippets from {filepath}")
        return store
    
    def search(self, query_embedding: torch.Tensor, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar code snippets."""
        # Convert query embedding to numpy and normalize
        query_np = query_embedding.numpy().reshape(1, self.dimension)
        faiss.normalize_L2(query_np)
        
        # Search the index
        distances, indices = self.index.search(query_np, top_k)
        
        # Extract results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.code_snippets) and idx >= 0:
                snippet = self.code_snippets[idx].copy()
                snippet["similarity"] = float(distances[0][i])
                results.append(snippet)
        
        return results


def process_codebase(repo_path: str, extensions: List[str] = None) -> List[Dict[str, Any]]:
    """Process a codebase to extract code snippets."""
    if extensions is None:
        extensions = [".py", ".js", ".java", ".cpp", ".c", ".h", ".cs", ".go", ".rb", ".php"]
    
    code_snippets = []
    repo_path = Path(repo_path)
    
    # Map file extensions to languages
    ext_to_lang = {
        ".py": "python", ".js": "javascript", ".java": "java",
        ".cpp": "cpp", ".c": "c", ".h": "cpp", ".cs": "csharp",
        ".go": "go", ".rb": "ruby", ".php": "php"
    }
    
    # Find all code files recursively
    all_files = []
    for ext in extensions:
        all_files.extend(repo_path.glob(f"**/*{ext}"))
    
    print(f"Found {len(all_files)} files with specified extensions")
    
    for file_path in tqdm(all_files):
        try:
            # Skip files in hidden directories
            if any(part.startswith(".") for part in file_path.parts):
                continue
            
            # Read the file content
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            
            # Get the file extension and corresponding language
            ext = file_path.suffix
            language = ext_to_lang.get(ext, "unknown")
            
            # Get the relative path from the repo root
            rel_path = str(file_path.relative_to(repo_path))
            
            # Add the snippet to the list
            snippet = {
                "id": rel_path,
                "code": content,
                "language": language,
                "filename": rel_path,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
            code_snippets.append(snippet)
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    return code_snippets


def create_file_chunks(code_snippets: List[Dict[str, Any]], max_length: int = 500) -> List[Dict[str, Any]]:
    """Split large files into chunks."""
    chunked_snippets = []
    
    for snippet in code_snippets:
        code = snippet["code"]
        lines = code.splitlines()
        
        # If the file is small enough, keep it as is
        if len(lines) <= max_length:
            chunked_snippets.append(snippet)
            continue
        
        # Otherwise, split it into chunks
        for i in range(0, len(lines), max_length):
            chunk_lines = lines[i:i + max_length]
            chunk_code = "\n".join(chunk_lines)
            
            # Create a new snippet for the chunk
            chunk_snippet = snippet.copy()
            chunk_snippet["id"] = f"{snippet['id']}#chunk{i//max_length + 1}"
            chunk_snippet["code"] = chunk_code
            
            chunked_snippets.append(chunk_snippet)
    
    return chunked_snippets


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="DeepSeek-Coder Vector Database Integration")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Index command
    index_parser = subparsers.add_parser("index", help="Index code from a repository")
    index_parser.add_argument("repo_path", help="Path to the code repository")
    index_parser.add_argument("--extensions", nargs="+", default=[".py", ".js", ".java", ".cpp"],
                            help="File extensions to include")
    index_parser.add_argument("--chunk-size", type=int, default=500,
                            help="Maximum number of lines per code chunk")
    index_parser.add_argument("--model", default="deepseek-ai/deepseek-coder-6.7b-base",
                            help="Model to use for embeddings")
    index_parser.add_argument("--storage", choices=["elasticsearch", "faiss"], default="faiss",
                            help="Storage backend")
    index_parser.add_argument("--es-host", default="localhost", help="Elasticsearch host")
    index_parser.add_argument("--es-port", type=int, default=9200, help="Elasticsearch port")
    index_parser.add_argument("--es-index", default="code-snippets", help="Elasticsearch index name")
    index_parser.add_argument("--output", default="code_store", help="Output path for FAISS index")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for similar code")
    search_parser.add_argument("query", help="Query string or file path")
    search_parser.add_argument("--is-file", action="store_true", help="If the query is a file path")
    search_parser.add_argument("--model", default="deepseek-ai/deepseek-coder-6.7b-base",
                             help="Model to use for embeddings")
    search_parser.add_argument("--top-k", type=int, default=5, help="Number of results to return")
    search_parser.add_argument("--storage", choices=["elasticsearch", "faiss"], default="faiss",
                             help="Storage backend")
    search_parser.add_argument("--es-host", default="localhost", help="Elasticsearch host")
    search_parser.add_argument("--es-port", type=int, default=9200, help="Elasticsearch port")
    search_parser.add_argument("--es-index", default="code-snippets", help="Elasticsearch index name")
    search_parser.add_argument("--index-path", default="code_store", help="Path to FAISS index")
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command == "index":
        # Process repository
        print(f"Processing repository: {args.repo_path}")
        code_snippets = process_codebase(args.repo_path, args.extensions)
        print(f"Extracted {len(code_snippets)} code snippets")
        
        # Chunk large files
        if args.chunk_size > 0:
            code_snippets = create_file_chunks(code_snippets, args.chunk_size)
            print(f"After chunking: {len(code_snippets)} code snippets")
        
        # Initialize embedding model
        model = CodeEmbeddingModel(args.model)
        
        # Generate embeddings
        print("Generating embeddings...")
        code_texts = [snippet["code"] for snippet in code_snippets]
        embeddings = model.encode(code_texts)
        print(f"Generated embeddings with shape: {embeddings.shape}")
        
        # Store embeddings
        if args.storage == "elasticsearch":
            print(f"Storing embeddings in Elasticsearch index: {args.es_index}")
            store = ElasticsearchCodeStore(
                host=args.es_host,
                port=args.es_port,
                index_name=args.es_index
            )
            store.index_code(code_snippets, embeddings)
        else:
            print(f"Storing embeddings in FAISS index: {args.output}")
            store = FaissCodeStore(dimension=embeddings.size(1))
            store.index_code(code_snippets, embeddings)
            store.save(args.output)
            
        print("Indexing completed successfully")
        
    elif args.command == "search":
        # Get query
        if args.is_file:
            with open(args.query, "r", encoding="utf-8") as f:
                query_text = f.read()
            print(f"Loaded query from file: {args.query}")
        else:
            query_text = args.query
        print(f"Query: {query_text[:100]}...")
        
        # Initialize embedding model
        model = CodeEmbeddingModel(args.model)
        
        # Generate query embedding
        print("Generating query embedding...")
        query_embedding = model.encode([query_text])
        
        # Search
        if args.storage == "elasticsearch":
            print(f"Searching in Elasticsearch index: {args.es_index}")
            store = ElasticsearchCodeStore(
                host=args.es_host,
                port=args.es_port,
                index_name=args.es_index
            )
            results = store.search(query_embedding, args.top_k)
        else:
            print(f"Searching in FAISS index: {args.index_path}")
            store = FaissCodeStore.load(args.index_path)
            results = store.search(query_embedding, args.top_k)
        
        # Print results
        print(f"\nFound {len(results)} results:")
        for i, result in enumerate(results):
            print(f"\n{i+1}. {result['filename']} (similarity: {result['similarity']:.4f})")
            print(f"Language: {result['language']}")
            print("-" * 40)
            # Print snippet of the code
            code_lines = result['code'].splitlines()
            print("\n".join(code_lines[:10]))
            if len(code_lines) > 10:
                print("...")
            print("-" * 40)
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
