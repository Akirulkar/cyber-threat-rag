from pydantic import BaseModel
from typing import List, Optional


class SourceDocument(BaseModel):
    id: str
    content: str
    source: str
    score: Optional[float] = None


class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[str]
    retrieved_documents: int
    latency_ms: float


class HealthResponse(BaseModel):
    status: str


class StatsResponse(BaseModel):
    documents: int
    chunks: int
    embedding_model: str
    llm: str
