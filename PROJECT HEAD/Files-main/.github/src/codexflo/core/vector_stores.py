import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import json
import pickle
from pathlib import Path
import faiss
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from abc import ABC, abstractmethod

class VectorStoreInterface(ABC):
    """Abstract interface for vector storage systems"""

    @abstractmethod
    def add_document(self, doc_id: str, embedding: np.ndarray, metadata: Dict) -> None:
        pass

    @abstractmethod
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[str, float, Dict]]:
        pass

    @abstractmethod
    def update_document(self, doc_id: str, embedding: np.ndarray, metadata: Dict) -> None:
        pass

    @abstractmethod
    def delete_document(self, doc_id: str) -> None:
        pass

    @abstractmethod
    def find_similar(self, doc_id: str, k: int = 5) -> List[Tuple[str, float, Dict]]:
        pass

class ChromaStore(VectorStoreInterface):
    """ChromaDB vector store implementation"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        persist_directory = config.get('persist_directory', './chroma_db')

        # Initialize ChromaDB client
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))

        # Get or create collection
        collection_name = config.get('collection_name', 'codexflo_documents')
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        # Initialize embedding model for queries
        model_name = config.get('embedding_model', 'all-MiniLM-L6-v2')
        self.embedding_model = SentenceTransformer(model_name)

    def add_document(self, doc_id: str, embedding: np.ndarray, metadata: Dict) -> None:
        """Add document to ChromaDB"""
        self.collection.add(
            embeddings=[embedding.tolist()],
            documents=[metadata.get('summary', '')],
            metadatas=[metadata],
            ids=[doc_id]
        )

    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[str, float, Dict]]:
        """Search for similar documents"""
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=k,
            include=['metadatas', 'distances']
        )

        output = []
        if results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                distance = results['distances'][0][i]
                metadata = results['metadatas'][0][i]
                similarity = 1 - distance  # Convert distance to similarity
                output.append((doc_id, similarity, metadata))

        return output

    def update_document(self, doc_id: str, embedding: np.ndarray, metadata: Dict) -> None:
        """Update existing document"""
        # ChromaDB handles updates as upserts
        self.collection.update(
            embeddings=[embedding.tolist()],
            documents=[metadata.get('summary', '')],
            metadatas=[metadata],
            ids=[doc_id]
        )

    def delete_document(self, doc_id: str) -> None:
        """Delete document from store"""
        self.collection.delete(ids=[doc_id])

    def find_similar(self, doc_id: str, k: int = 5) -> List[Tuple[str, float, Dict]]:
        """Find documents similar to a given document"""
        # Get the document's embedding
        result = self.collection.get(
            ids=[doc_id],
            include=['embeddings', 'metadatas']
        )

        if not result['ids']:
            return []

        embedding = np.array(result['embeddings'][0])

        # Search for similar documents (excluding the source)
        similar = self.search(embedding, k + 1)
        return [item for item in similar if item[0] != doc_id][:k]

    def semantic_cluster(self, min_similarity: float = 0.7) -> Dict[str, List[str]]:
        """Cluster documents based on semantic similarity"""
        all_data = self.collection.get(include=['embeddings', 'metadatas'])

        if not all_data['ids']:
            return {}

        embeddings = np.array(all_data['embeddings'])
        doc_ids = all_data['ids']

        # Compute similarity matrix
        similarity_matrix = np.dot(embeddings, embeddings.T)

        # Find clusters
        clusters = {}
        visited = set()

        for i, doc_id in enumerate(doc_ids):
            if doc_id in visited:
                continue

            cluster = [doc_id]
            visited.add(doc_id)

            # Find all documents similar to this one
            similarities = similarity_matrix[i]
            similar_indices = np.where(similarities > min_similarity)[0]

            for idx in similar_indices:
                if idx != i and doc_ids[idx] not in visited:
                    cluster.append(doc_ids[idx])
                    visited.add(doc_ids[idx])

            if len(cluster) > 1:
                cluster_name = f"cluster_{len(clusters)}"
                clusters[cluster_name] = cluster

        return clusters

class SimpleVectorStore(VectorStoreInterface):
    """Simple FAISS-based vector store for local deployment"""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.id_to_idx = {}
        self.idx_to_id = {}
        self.metadata_store = {}
        self.next_idx = 0
        self.persist_path = Path('./simple_vector_store')
        self.persist_path.mkdir(exist_ok=True)

        # Load existing index if available
        self._load()

    def add_document(self, doc_id: str, embedding: np.ndarray, metadata: Dict) -> None:
        """Add document to FAISS index"""
        if doc_id in self.id_to_idx:
            # Update existing
            self.update_document(doc_id, embedding, metadata)
            return

        # Add new document
        self.index.add(embedding.reshape(1, -1))
        self.id_to_idx[doc_id] = self.next_idx
        self.idx_to_id[self.next_idx] = doc_id
        self.metadata_store[doc_id] = metadata
        self.next_idx += 1

        # Persist changes
        self._save()

    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[str, float, Dict]]:
        """Search for similar documents"""
        if self.index.ntotal == 0:
            return []

        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_embedding.reshape(1, -1), k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx in self.idx_to_id:
                doc_id = self.idx_to_id[idx]
                similarity = 1 / (1 + dist)  # Convert distance to similarity
                metadata = self.metadata_store.get(doc_id, {})
                results.append((doc_id, similarity, metadata))

        return results

    def update_document(self, doc_id: str, embedding: np.ndarray, metadata: Dict) -> None:
        """Update existing document"""
        if doc_id not in self.id_to_idx:
            self.add_document(doc_id, embedding, metadata)
            return

        # FAISS doesn't support in-place updates, so we rebuild
        # This is fine for smaller datasets
        old_idx = self.id_to_idx[doc_id]

        # Create new index
        new_index = faiss.IndexFlatL2(self.dimension)

        # Copy all embeddings except the one being updated
        for i in range(self.index.ntotal):
            if i != old_idx:
                vec = self.index.reconstruct(i)
                new_index.add(vec.reshape(1, -1))

        # Add updated embedding
        new_index.add(embedding.reshape(1, -1))

        # Update metadata
        self.metadata_store[doc_id] = metadata

        # Replace index
        self.index = new_index

        # Rebuild mappings
        self._rebuild_mappings()
        self._save()

    def delete_document(self, doc_id: str) -> None:
        """Delete document from store"""
        if doc_id not in self.id_to_idx:
            return

        old_idx = self.id_to_idx[doc_id]

        # Create new index without the deleted document
        new_index = faiss.IndexFlatL2(self.dimension)

        for i in range(self.index.ntotal):
            if i != old_idx:
                vec = self.index.reconstruct(i)
                new_index.add(vec.reshape(1, -1))

        # Update data structures
        del self.id_to_idx[doc_id]
        del self.metadata_store[doc_id]

        # Replace index
        self.index = new_index

        # Rebuild mappings
        self._rebuild_mappings()
        self._save()

    def find_similar(self, doc_id: str, k: int = 5) -> List[Tuple[str, float, Dict]]:
        """Find documents similar to a given document"""
        if doc_id not in self.id_to_idx:
            return []

        idx = self.id_to_idx[doc_id]
        embedding = self.index.reconstruct(idx)

        # Search for k+1 to exclude the source document
        results = self.search(embedding, k + 1)
        return [r for r in results if r[0] != doc_id][:k]

    def _rebuild_mappings(self):
        """Rebuild ID to index mappings after index modification"""
        self.id_to_idx.clear()
        self.idx_to_id.clear()

        idx = 0
        for doc_id in list(self.metadata_store.keys()):
            if doc_id in self.metadata_store:  # Still exists
                self.id_to_idx[doc_id] = idx
                self.idx_to_id[idx] = doc_id
                idx += 1

        self.next_idx = idx

    def _save(self):
        """Persist index and metadata to disk"""
        # Save FAISS index
        faiss.write_index(self.index, str(self.persist_path / 'index.faiss'))

        # Save metadata
        with open(self.persist_path / 'metadata.pkl', 'wb') as f:
            pickle.dump({
                'id_to_idx': self.id_to_idx,
                'idx_to_id': self.idx_to_id,
                'metadata_store': self.metadata_store,
                'next_idx': self.next_idx
            }, f)

    def _load(self):
        """Load index and metadata from disk"""
        index_path = self.persist_path / 'index.faiss'
        metadata_path = self.persist_path / 'metadata.pkl'

        if index_path.exists() and metadata_path.exists():
            # Load FAISS index
            self.index = faiss.read_index(str(index_path))

            # Load metadata
            with open(metadata_path, 'rb') as f:
                data = pickle.load(f)
                self.id_to_idx = data['id_to_idx']
                self.idx_to_id = data['idx_to_id']
                self.metadata_store = data['metadata_store']
                self.next_idx = data['next_idx']

class HybridVectorStore(VectorStoreInterface):
    """Hybrid store combining ChromaDB for persistence and FAISS for speed"""

    def __init__(self, config: Dict[str, Any]):
        self.chroma_store = ChromaStore(config)
        self.faiss_cache = SimpleVectorStore(config.get('dimension', 384))
        self.cache_size = config.get('cache_size', 10000)

    def add_document(self, doc_id: str, embedding: np.ndarray, metadata: Dict) -> None:
        """Add to both stores"""
        self.chroma_store.add_document(doc_id, embedding, metadata)

        # Add to cache if under limit
        if self.faiss_cache.index.ntotal < self.cache_size:
            self.faiss_cache.add_document(doc_id, embedding, metadata)

    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[str, float, Dict]]:
        """Search using FAISS cache first, fallback to Chroma"""
        if self.faiss_cache.index.ntotal > 0:
            return self.faiss_cache.search(query_embedding, k)
        return self.chroma_store.search(query_embedding, k)

    def update_document(self, doc_id: str, embedding: np.ndarray, metadata: Dict) -> None:
        """Update in both stores"""
        self.chroma_store.update_document(doc_id, embedding, metadata)
        if doc_id in self.faiss_cache.id_to_idx:
            self.faiss_cache.update_document(doc_id, embedding, metadata)

    def delete_document(self, doc_id: str) -> None:
        """Delete from both stores"""
        self.chroma_store.delete_document(doc_id)
        self.faiss_cache.delete_document(doc_id)

    def find_similar(self, doc_id: str, k: int = 5) -> List[Tuple[str, float, Dict]]:
        """Find similar using appropriate store"""
        if doc_id in self.faiss_cache.id_to_idx:
            return self.faiss_cache.find_similar(doc_id, k)
        return self.chroma_store.find_similar(doc_id, k)
