# app/pipeline/rag_pipeline.py
import time
from typing import Any, Dict, List, Optional

from app.core.logger import logger
from app.pipeline.retrieve import RetrievalPipeline
from app.rag.context_builder import ContextBuilder
from app.rag.llm import LLMEngine
from app.rag.prompt_builder import PromptBuilder
from app.retrieval.query_processor import QueryProcessor


class RAGPipeline:
    """End-to-End RAG Pipeline with conditional retrieval bypass for meta/simplification queries."""

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

    def answer(
        self,
        question: str,
        top_n: int = 5,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        t0 = time.time()
        metrics = {}
        chat_history = chat_history or []

        # 1. Rewrite Query and check if retrieval should be skipped
        search_query, skip_retrieval = QueryProcessor.rewrite_query_with_history(
            raw_query=question,
            chat_history=chat_history,
            llm_engine=self.llm,
        )
        metrics["processed_query"] = search_query
        metrics["skip_retrieval"] = skip_retrieval

        # 2. Skip Retrieval for Simplification / Meta Queries
        if skip_retrieval and chat_history:
            logger.info("Executing direct LLM re-formatting without vector retrieval.")

            # Find the last assistant message in history
            last_assistant_msg = ""
            for msg in reversed(chat_history):
                if msg.get("role") == "assistant":
                    last_assistant_msg = msg.get("content", "")
                    break

            prompt = [
                {
                    "role": "system",
                    "content": (
                        "You are a cybersecurity assistant. The user wants you to explain or simplify "
                        "your previous answer. Rely ONLY on the previous response content. Do NOT invent new details."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Previous Answer:\n{last_assistant_msg}\n\nUser Instruction: {question}\n\nSimplified Explanation:",
                },
            ]

            t_llm = time.time()
            answer_text = self.llm.generate(prompt)
            metrics["llm_generation_ms"] = round((time.time() - t_llm) * 1000, 2)
            metrics["total_latency_ms"] = round((time.time() - t0) * 1000, 2)

            return {
                "question": question,
                "answer": answer_text,
                "sources": ["Previous Conversation Turn"],
                "metrics": metrics,
            }

        # 3. Standard Hybrid Retrieval & Reranking
        retrieval_output = self.retriever.run(raw_query=search_query, top_n=top_n)
        reranked_results = retrieval_output["results"]
        metrics["retrieval_ms"] = retrieval_output["metrics"]["total_latency_ms"]

        if not reranked_results:
            return {
                "question": question,
                "answer": "I could not find sufficient threat intelligence in the database to answer this question.",
                "sources": [],
                "metrics": {"total_latency_ms": round((time.time() - t0) * 1000, 2)},
            }

        # 4. Context Assembly & Source Extraction
        context_str, sources = self.context_builder.build_context(reranked_results)

        # 5. Construct Prompt & LLM Generation
        try:
            formatted_messages = self.prompt_builder.format(
                context=context_str, question=question, chat_history=chat_history
            )
        except TypeError:
            formatted_messages = self.prompt_builder.format(
                context=context_str, question=question
            )

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
