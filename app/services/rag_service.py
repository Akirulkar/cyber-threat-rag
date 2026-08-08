import time
from typing import Any, Dict, List, Optional

from app.core.exceptions import ModelInferenceError, RAGPipelineException
from app.core.logger import logger
from app.pipeline.rag_pipeline import RAGPipeline
from app.pipeline.retrieve import RetrievalPipeline
from app.rag.llm import LLMEngine
from app.retrieval.dense import DenseRetriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.reranker import CrossEncoderReranker
from app.retrieval.sparse import SparseRetriever
from app.schemas.request import QueryRequest
from app.schemas.response import QueryResponse


class RAGService:
    """Service layer connecting FastAPI API endpoints with the RAG Pipeline."""

    def __init__(self, rag_pipeline: Optional[RAGPipeline] = None):
        self.pipeline = rag_pipeline

    def _ensure_pipeline(self) -> RAGPipeline:
        """Lazy loader to instantiate all Phase 3 & Phase 4 components if not injected."""
        if self.pipeline is None:
            try:
                logger.info("Initializing Phase 4 RAG Pipeline for API Service...")

                # 1. Initialize Phase 3 Retrievers
                dense = DenseRetriever(vectorstore_dir="vectorstore")
                sparse = SparseRetriever(vectorstore_dir="vectorstore")
                hybrid = HybridRetriever(dense, sparse)
                reranker = CrossEncoderReranker(model_name="BAAI/bge-reranker-base")
                retrieval_pipeline = RetrievalPipeline(hybrid, reranker)

                # 2. Initialize Phase 4 LLM Engine
                llm_engine = LLMEngine(
                    provider="nvidia",
                    model_name="nvidia/nemotron-3-nano-30b-a3b",
                    temperature=0.2,
                    top_p=0.95,
                    max_tokens=4096,
                    reasoning_budget=4096,
                )

                # 3. Construct Full RAG Pipeline
                self.pipeline = RAGPipeline(
                    retrieval_pipeline=retrieval_pipeline,
                    llm_engine=llm_engine,
                )
                logger.info("Phase 4 RAG Pipeline successfully loaded into memory.")
            except Exception as e:
                logger.error(
                    f"Failed to initialize RAG Pipeline: {str(e)}", exc_info=True
                )
                raise RAGPipelineException(
                    f"RAG Service initialization error: {str(e)}"
                )

        return self.pipeline

    def query(
        self,
        question: str,
        top_n: int = 5,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Synchronous query method used during testing and direct service invocation."""
        pipeline = self._ensure_pipeline()
        return pipeline.answer(
            question=question, top_n=top_n, chat_history=chat_history
        )

    async def execute_query(self, request: QueryRequest) -> QueryResponse:
        """Async interface for FastAPI route handlers with chat history support."""
        try:
            # Convert Pydantic Message models to dictionary format
            history_dicts = (
                [msg.model_dump() for msg in request.chat_history]
                if request.chat_history
                else []
            )

            # Executes pipeline with chat history
            result = self.query(
                question=request.query,
                top_n=request.top_k,
                chat_history=history_dicts,
            )

            answer_text = result.get("answer", "")
            raw_sources = result.get("sources", [])
            metrics = result.get("metrics", {})

            # Format source strings cleanly if items in sources are dictionaries
            formatted_sources = []
            for src in raw_sources:
                if isinstance(src, dict):
                    doc_id = src.get("document_id", "Doc")
                    source_name = src.get("source", "N/A")
                    formatted_sources.append(f"[{source_name}] {doc_id}")
                else:
                    formatted_sources.append(str(src))

            return QueryResponse(
                query=result.get("question", request.query),
                answer=answer_text,
                sources=formatted_sources,
                retrieved_documents=len(raw_sources),
                latency_ms=metrics.get("total_latency_ms", 0.0),
            )

        except RAGPipelineException:
            raise
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}", exc_info=True)
            raise ModelInferenceError(f"RAG Execution failed: {str(e)}")


# Default singleton instance for FastAPI endpoints
rag_service = RAGService()
