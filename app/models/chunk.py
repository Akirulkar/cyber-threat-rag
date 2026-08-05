from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """Metadata attached to each chunk for filtering & context revival."""

    chunk_id: str
    document_id: str
    source: str
    document_type: str
    title: str
    url: str
    severity: str
    vendor: Optional[str] = None
    product: Optional[str] = None
    chunk_index: int
    total_chunks: int


class Chunk(BaseModel):
    """The atomic searchable unit in the RAG system."""

    chunk_id: str
    document_id: str
    text: str
    metadata: ChunkMetadata
    embedding: Optional[List[float]] = None
