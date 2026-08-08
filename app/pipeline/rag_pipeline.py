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
    """End-to-End RAG Pipeline with direct meta-query bypass and empty-history guard."""

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

        is_simplification = QueryProcessor.is_meta_or_formatting_request(question)

        # 1. Handle Simplification Requests
        if is_simplification:
            # Case A: User cleared chat or history is empty -> Return clean message without vector search
            if not chat_history:
                logger.info(
                    "Simplification requested with empty chat history. Returning prompt guidance."
                )
                metrics["skip_retrieval"] = True
                metrics["total_latency_ms"] = round((time.time() - t0) * 1000, 2)
                return {
                    "question": question,
                    "answer": "There is no previous conversation or vulnerability topic in our active chat session to simplify. Please ask a specific question first (for example: *'What is CVE-2024-3094?'*).",
                    "sources": [],
                    "metrics": metrics,
                }

            # Case B: History exists -> Simplify previous assistant response without vector retrieval
            logger.info("Simplification query detected: Bypassing vector retrieval.")

            first_user_query = ""
            target_assistant_msg = ""

            # Iterate backwards to get the latest completed turn
            for msg in reversed(chat_history):
                if msg.get("role") == "assistant" and not target_assistant_msg:
                    target_assistant_msg = msg.get("content", "")
                elif (
                    msg.get("role") == "user"
                    and not first_user_query
                    and target_assistant_msg
                ):
                    first_user_query = msg.get("content", "")
                    break

            prompt = [
                {
                    "role": "system",
                    "content": (
                        "You are a cybersecurity expert. The user wants a simplified, plain-language explanation "
                        "of a specific vulnerability discussed earlier in the conversation. "
                        "Explain what the issue is, how it works, and why it matters in clear, non-technical terms. "
                        "Rely ONLY on the provided context below. Do NOT introduce new CVEs or unmentioned software."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Original Topic/Question: {first_user_query}\n\n"
                        f"Detailed Technical Content:\n{target_assistant_msg}\n\n"
                        f"User Request: {question}\n\n"
                        "Simplified Plain-English Explanation:"
                    ),
                },
            ]

            t_llm = time.time()
            answer_text = self.llm.generate(prompt)
            metrics["llm_generation_ms"] = round((time.time() - t_llm) * 1000, 2)
            metrics["total_latency_ms"] = round((time.time() - t0) * 1000, 2)
            metrics["skip_retrieval"] = True

            return {
                "question": question,
                "answer": answer_text,
                "sources": ["Previous Conversation Summary"],
                "metrics": metrics,
            }

        # 2. Standard Hybrid Retrieval & Reranking
        search_query, _ = QueryProcessor.rewrite_query_with_history(
            raw_query=question,
            chat_history=chat_history,
            llm_engine=self.llm,
        )
        metrics["processed_query"] = search_query

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

        context_str, sources = self.context_builder.build_context(reranked_results)

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
