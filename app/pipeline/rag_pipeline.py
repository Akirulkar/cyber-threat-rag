import time
from typing import Any, Dict

from app.core.logger import logger
from app.pipeline.retrieve import RetrievalPipeline
from app.rag.context_builder import ContextBuilder
from app.rag.llm import LLMEngine
from app.rag.prompt_builder import PromptBuilder


class RAGPipeline:
    """End-to-End RAG Pipeline combining retrieval, context preparation, and LLM generation."""

    def __init__(
        self,
        retrieval_pipeline: RetrievalPipeline,
        llm_engine: LLMEngine,
        context_builder: ContextBuilder = None,
        prompt_builder: PromptBuilder = None,
    ):
        self.retriever = retrieval_pipeline
        self.llm = llm_engine
        self.context_builder = context_builder or ContextBuilder()
        self.prompt_builder = prompt_builder or PromptBuilder()

    def answer(self, question: str, top_n: int = 5) -> Dict[str, Any]:
        t0 = time.time()
        metrics = {}

        # 1. Execute Phase 3 Hybrid Retrieval & Reranking
        retrieval_output = self.retriever.run(raw_query=question, top_n=top_n)
        reranked_results = retrieval_output["results"]
        metrics["retrieval_ms"] = retrieval_output["metrics"]["total_latency_ms"]

        # 2. Check for empty retrieval results
        if not reranked_results:
            return {
                "question": question,
                "answer": "I could not find sufficient threat intelligence in the database to answer this question.",
                "sources": [],
                "metrics": {"total_latency_ms": round((time.time() - t0) * 1000, 2)},
            }

        # 3. Build Context String & Extract Sources
        context_str, sources = self.context_builder.build_context(reranked_results)

        # 4. Construct Prompt
        formatted_messages = self.prompt_builder.format(
            context=context_str, question=question
        )

        # 5. LLM Generation
        t_llm = time.time()
        answer_text = self.llm.generate(formatted_messages)
        metrics["llm_generation_ms"] = round((time.time() - t_llm) * 1000, 2)

        metrics["total_latency_ms"] = round((time.time() - t0) * 1000, 2)

        return {
            "question": question,
            "answer": answer_text,
            "sources": sources,
            "metrics": metrics,
        }
