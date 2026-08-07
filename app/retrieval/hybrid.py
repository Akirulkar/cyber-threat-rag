from typing import List
from app.models.chunk import Chunk
from app.retrieval.dense import DenseRetriever
from app.retrieval.sparse import SparseRetriever


class HybridRetriever:
    """Combines Dense (FAISS) and Sparse (BM25) search streams."""

    def __init__(
        self, dense_retriever: DenseRetriever, sparse_retriever: SparseRetriever
    ):
        self.dense = dense_retriever
        self.sparse = sparse_retriever

    def retrieve(
        self, query: str, dense_k: int = 20, sparse_k: int = 20
    ) -> List[Chunk]:
        dense_results = self.dense.retrieve(query, top_k=dense_k)
        sparse_results = self.sparse.retrieve(query, top_k=sparse_k)

        seen_chunk_ids = set()
        deduped_chunks: List[Chunk] = []

        # Merge Dense and Sparse candidates, eliminating duplicates
        for item in dense_results + sparse_results:
            chunk = item[0] if isinstance(item, tuple) else item
            if chunk.chunk_id not in seen_chunk_ids:
                seen_chunk_ids.add(chunk.chunk_id)
                deduped_chunks.append(chunk)

        return deduped_chunks
