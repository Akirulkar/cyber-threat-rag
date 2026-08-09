# app/pipeline/retrieve.py
import time
from typing import Any, Dict

from app.core.logger import logger
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.query_processor import QueryProcessor
from app.retrieval.reranker import CrossEncoderReranker


class RetrievalPipeline:
    def __init__(
        self, hybrid_retriever: HybridRetriever, reranker: CrossEncoderReranker
    ):
        self.hybrid_retriever = hybrid_retriever
        self.reranker = reranker

    def run(self, raw_query: str, top_n: int = 5) -> Dict[str, Any]:
        metrics = {}
        t0 = time.time()

        # 1. Preprocess Query
        query = QueryProcessor.process(raw_query)

        # 2. Hybrid Search with increased candidate depth (50 each stream)
        t_search = time.time()
        candidates = self.hybrid_retriever.retrieve(query, dense_k=50, sparse_k=50)
        metrics["hybrid_search_ms"] = round((time.time() - t_search) * 1000, 2)
        metrics["candidates_found"] = len(candidates)

        # 3. Cross-Encoder Reranking
        t_rerank = time.time()
        reranked_results = self.reranker.rerank(query, candidates, top_n=top_n)
        metrics["rerank_ms"] = round((time.time() - t_rerank) * 1000, 2)

        metrics["total_latency_ms"] = round((time.time() - t0) * 1000, 2)

        return {
            "processed_query": query,
            "results": reranked_results,
            "metrics": metrics,
        }
