from typing import Any, Dict
from app.pipeline.rag_pipeline import RAGPipeline


class RAGService:
    def __init__(self, rag_pipeline: RAGPipeline):
        self.pipeline = rag_pipeline

    def query(self, question: str, top_n: int = 5) -> Dict[str, Any]:
        return self.pipeline.answer(question=question, top_n=top_n)
