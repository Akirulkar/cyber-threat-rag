# app/retrieval/hybrid.py
import re
from typing import List
from app.models.chunk import Chunk
from app.retrieval.dense import DenseRetriever
from app.retrieval.sparse import SparseRetriever


class HybridRetriever:
    """Combines Dense (FAISS) and Sparse (BM25) search streams with multi-source CVE matching."""

    def __init__(
        self, dense_retriever: DenseRetriever, sparse_retriever: SparseRetriever
    ):
        self.dense = dense_retriever
        self.sparse = sparse_retriever

    def retrieve(
        self, query: str, dense_k: int = 30, sparse_k: int = 30
    ) -> List[Chunk]:
        cve_matches = re.findall(r"(CVE-\d{4}-\d{4,7})", query, flags=re.IGNORECASE)
        exact_cve = cve_matches[0].upper() if cve_matches else None

        dense_results = self.dense.retrieve(query, top_k=dense_k)
        sparse_results = self.sparse.retrieve(query, top_k=sparse_k)

        seen_chunk_ids = set()
        cve_priority_chunks: List[Chunk] = []
        other_chunks: List[Chunk] = []

        for item in dense_results + sparse_results:
            chunk = item[0] if isinstance(item, tuple) else item
            if chunk.chunk_id not in seen_chunk_ids:
                seen_chunk_ids.add(chunk.chunk_id)

                # Check if exact_cve is matched in NVD, CISA (CISA-KEV-CVE-XXXX), or Metadata
                is_cve_match = exact_cve and (
                    exact_cve in chunk.document_id.upper()
                    or exact_cve in chunk.metadata.chunk_id.upper()
                )

                if is_cve_match:
                    cve_priority_chunks.append(chunk)
                else:
                    other_chunks.append(chunk)

        return cve_priority_chunks + other_chunks
