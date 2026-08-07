from typing import Any, Dict
from app.pipeline.retrieve import RetrievalPipeline


class RetrievalService:
    def __init__(self, pipeline: RetrievalPipeline):
        self.pipeline = pipeline

    def search_threat_intel(self, query: str, top_n: int = 5) -> Dict[str, Any]:
        return self.pipeline.run(raw_query=query, top_n=top_n)
