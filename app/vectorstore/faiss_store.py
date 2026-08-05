import os
import pickle
from typing import List, Tuple, Dict, Any
import numpy as np
import faiss

from app.models.chunk import Chunk, ChunkMetadata


class FAISSVectorStore:
    """FAISS-backed vector store managing vector index and payload mapping."""

    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        # IndexFlatIP performs inner product search (Cosine Similarity when normalized)
        self.index = faiss.IndexFlatIP(dimension)
        # Store metadata mapping using FAISS internal integer position as key
        self.doc_map: Dict[int, Chunk] = {}

    def add_chunks(self, chunks: List[Chunk]) -> None:
        """Adds a list of embedded Chunk models into the FAISS index."""
        if not chunks:
            return

        embeddings_list = []
        start_idx = len(self.doc_map)

        for i, chunk in enumerate(chunks):
            if chunk.embedding is None:
                raise ValueError(f"Chunk {chunk.chunk_id} missing embedding vector.")

            embeddings_list.append(chunk.embedding)
            self.doc_map[start_idx + i] = chunk

        embeddings_np = np.array(embeddings_list, dtype=np.float32)
        self.index.add(embeddings_np)

    def search(
        self, query_vector: np.ndarray, top_k: int = 5
    ) -> List[Tuple[Chunk, float]]:
        """Searches the vector store for top_k nearest neighbors given a query embedding."""
        if self.index.ntotal == 0:
            return []

        # distances contains cosine similarity scores due to normalized vectors
        distances, indices = self.index.search(query_vector, top_k)

        results: List[Tuple[Chunk, float]] = []
        for idx, score in zip(indices[0], distances[0]):
            if idx != -1 and idx in self.doc_map:
                results.append((self.doc_map[idx], float(score)))

        return results

    def save(self, folder_path: str) -> None:
        """Saves the FAISS index binary and doc_map metadata to disk."""
        os.makedirs(folder_path, exist_ok=True)

        index_path = os.path.join(folder_path, "faiss.index")
        metadata_path = os.path.join(folder_path, "metadata.pkl")

        # Save C++ binary index
        faiss.write_index(self.index, index_path)

        # Save metadata mapping
        with open(metadata_path, "wb") as f:
            pickle.dump(self.doc_map, f)

    @classmethod
    def load(cls, folder_path: str) -> "FAISSVectorStore":
        """Loads a FAISSVectorStore instance from disk."""
        index_path = os.path.join(folder_path, "faiss.index")
        metadata_path = os.path.join(folder_path, "metadata.pkl")

        if not os.path.exists(index_path) or not os.path.exists(metadata_path):
            raise FileNotFoundError(f"FAISS files not found in {folder_path}")

        index = faiss.read_index(index_path)
        with open(metadata_path, "rb") as f:
            doc_map = pickle.load(f)

        store = cls(dimension=index.d)
        store.index = index
        store.doc_map = doc_map
        return store
