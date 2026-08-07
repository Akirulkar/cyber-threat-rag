from typing import List, Union, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from app.models.chunk import Chunk
import torch
from app.core.logger import logger
from app.core.config import settings


class TextEmbedder:
    """Wrapper around SentenceTransformer for generating vector embeddings."""

    def __init__(
        self,
        model_name: str = settings.EMBEDDING_MODEL,
        device: Optional[str] = None,
    ):
        """Initializes the embedding model with automatic GPU/CPU detection.

        Defaults to 'BAAI/bge-base-en-v1.5' (768-dim output).
        """
        self.model_name = model_name
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        logger.info(
            f"Initializing TextEmbedder with model '{model_name}' on device '{self.device}'..."
        )
        self.model = SentenceTransformer(model_name, device=self.device)
        self.embedding_dim = self.model.get_embedding_dimension()

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Embeds a list of raw text strings into a 2D float32 NumPy array."""
        if not texts:
            return np.empty((0, self.embedding_dim), dtype=np.float32)

        # normalize_embeddings=True allows using Inner Product for Cosine Similarity
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return embeddings.astype(np.float32)

    def embed_chunks(self, chunks: List[Chunk], batch_size: int = 128) -> List[Chunk]:
        """Generates embeddings for a list of Chunk models and updates them in-place."""
        if not chunks:
            return chunks

        texts = [chunk.text for chunk in chunks]
        embeddings = self.embed_texts(texts, batch_size=batch_size)

        for chunk, emb in zip(chunks, embeddings):
            chunk.embedding = emb.tolist()

        return chunks

    def embed_query(self, query: str) -> np.ndarray:
        """Embeds a single query string for retrieval search."""
        embedding = self.model.encode(
            query,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return np.expand_dims(embedding.astype(np.float32), axis=0)
