from typing import List, Tuple
import torch
from sentence_transformers import CrossEncoder

from app.core.logger import logger
from app.models.chunk import Chunk


class CrossEncoderReranker:
    """Reranks candidate chunks using a cross-encoder model."""

    def __init__(self, model_name: str = "BAAI/bge-reranker-base", device: str = None):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        logger.info(
            f"Loading CrossEncoder model '{model_name}' on device '{self.device}'..."
        )
        self.model = CrossEncoder(model_name, device=self.device)

    def rerank(
        self, query: str, chunks: List[Chunk], top_n: int = 5
    ) -> List[Tuple[Chunk, float]]:
        if not chunks:
            return []

        # Form (query, chunk_text) pairs
        pairs = [[query, chunk.text] for chunk in chunks]
        scores = self.model.predict(pairs)

        chunk_score_pairs = list(zip(chunks, [float(s) for s in scores]))

        # Sort descending by reranker score
        reranked = sorted(chunk_score_pairs, key=lambda x: x[1], reverse=True)
        return reranked[:top_n]
