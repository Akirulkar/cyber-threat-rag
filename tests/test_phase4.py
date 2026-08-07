import os
from dotenv import load_dotenv

load_dotenv()

from app.core.logger import logger
from app.pipeline.retrieve import RetrievalPipeline
from app.rag.llm import LLMEngine
from app.pipeline.rag_pipeline import RAGPipeline
from app.retrieval.dense import DenseRetriever
from app.retrieval.sparse import SparseRetriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.reranker import CrossEncoderReranker
from app.services.rag_service import RAGService


def test_rag_system():
    logger.info("Initializing Phase 4 RAG Pipeline with Llama 3.3 70B on NVIDIA NIM...")

    # 1. Phase 3 Retrievers
    dense = DenseRetriever(vectorstore_dir="vectorstore")
    sparse = SparseRetriever(vectorstore_dir="vectorstore")
    hybrid = HybridRetriever(dense, sparse)
    reranker = CrossEncoderReranker(model_name="BAAI/bge-reranker-base")
    retrieval_pipeline = RetrievalPipeline(hybrid, reranker)

    # 2. Phase 4 LLM Engine with meta/llama-3.3-70b-instruct
    llm_engine = LLMEngine(
        provider="nvidia",
        model_name="nvidia/nemotron-3-nano-30b-a3b",
        temperature=0.2,  # Lower temperature slightly for RAG consistency
        top_p=0.95,
        max_tokens=4096,
        reasoning_budget=4096,
    )

    # 3. Full RAG Pipeline
    rag_pipeline = RAGPipeline(
        retrieval_pipeline=retrieval_pipeline,
        llm_engine=llm_engine,
    )
    rag_service = RAGService(rag_pipeline)

    test_queries = [
        "What are the details and mitigations for CVE-2024-3094?",
        "Explain Cisco ASA authentication bypass vulnerabilities.",
    ]

    for question in test_queries:
        print("\n" + "=" * 80)
        print(f"QUESTION: {question}")
        print("=" * 80)

        result = rag_service.query(question, top_n=3)

        print(f"\n[GENERATED ANSWER]:\n{result['answer']}")
        print("\n[SOURCES CITED]:")
        for src in result["sources"]:
            print(
                f" - [{src['source']}] {src['document_id']}: {src['title']} ({src['url']})"
            )

        print(f"\n[METRICS]: {result['metrics']}")
        print("=" * 80)


if __name__ == "__main__":
    test_rag_system()
