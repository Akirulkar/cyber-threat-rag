from typing import List, Tuple
import faiss
import numpy as np

from app.core.logger import logger
from app.embedding.embedder import TextEmbedder
from app.models.chunk import Chunk
from app.vectorstore_scripts.sqlite_store import SQLiteMetadataStore


class DenseRetriever:
    """Dense semantic retrieval wrapping FAISS binary index and SQLite metadata store."""

    def __init__(
        self,
        vectorstore_dir: str = "vectorstore",
        model_name: str = "BAAI/bge-base-en-v1.5",
    ):
        self.index_path = f"{vectorstore_dir}/faiss.index"
        self.db_path = f"{vectorstore_dir}/metadata.db"

        logger.info("Loading FAISS index for DenseRetriever...")
        self.faiss_index = faiss.read_index(self.index_path)

        logger.info("Connecting to SQLite store for DenseRetriever...")
        self.db_store = SQLiteMetadataStore(db_path=self.db_path)

        self.embedder = TextEmbedder(model_name=model_name)

    def retrieve(self, query: str, top_k: int = 20) -> List[Tuple[Chunk, float]]:
        query_vector = self.embedder.embed_query(query)
        distances, indices = self.faiss_index.search(
            query_vector.astype(np.float32), top_k
        )

        top_ids = [int(i) for i in indices[0] if i != -1]
        scores = distances[0].tolist()

        chunks_map = self.db_store.get_chunks_by_faiss_ids(top_ids)

        results: List[Tuple[Chunk, float]] = []
        for fid, score in zip(top_ids, scores):
            if fid in chunks_map:
                results.append((chunks_map[fid], float(score)))

        return results
