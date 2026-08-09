# app/retrieval/sparse.py
import pickle
import re
from pathlib import Path
from typing import List, Tuple
from rank_bm25 import BM25Okapi

from app.core.logger import logger
from app.models.chunk import Chunk
from app.vectorstore_scripts.sqlite_store import SQLiteMetadataStore


class SparseRetriever:
    """Sparse keyword retrieval using rank-bm25."""

    def __init__(self, vectorstore_dir: str = "vectorstore"):
        bm25_path = Path(vectorstore_dir) / "bm25.pkl"
        db_path = Path(vectorstore_dir) / "metadata.db"

        if not bm25_path.exists():
            raise FileNotFoundError(
                f"BM25 index not found at '{bm25_path}'. Run build_bm25_index.py first!"
            )

        logger.info("Loading BM25 index into memory...")
        with open(bm25_path, "rb") as f:
            data = pickle.load(f)
            self.faiss_ids = data["faiss_ids"]
            self.bm25: BM25Okapi = data["bm25"]

        self.db_store = SQLiteMetadataStore(db_path=str(db_path))

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        cve_pattern = r"CVE-\d{4}-\d{4,7}"
        cves = [c.upper() for c in re.findall(cve_pattern, text, flags=re.IGNORECASE)]
        text_sans_cves = re.sub(cve_pattern, "", text, flags=re.IGNORECASE)
        words = re.findall(r"\w+", text_sans_cves.lower())
        return cves + words

    def retrieve(self, query: str, top_k: int = 20) -> List[Tuple[Chunk, float]]:
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)

        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[
            :top_k
        ]

        selected_faiss_ids = [
            self.faiss_ids[idx] for idx in top_indices if scores[idx] > 0
        ]
        selected_scores = [scores[idx] for idx in top_indices if scores[idx] > 0]

        chunks_map = self.db_store.get_chunks_by_faiss_ids(selected_faiss_ids)

        results: List[Tuple[Chunk, float]] = []
        for fid, score in zip(selected_faiss_ids, selected_scores):
            if fid in chunks_map:
                results.append((chunks_map[fid], float(score)))

        return results
