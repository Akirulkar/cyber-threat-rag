from app.core.logger import logger
from app.pipeline.retrieve import RetrievalPipeline
from app.retrieval.dense import DenseRetriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.reranker import CrossEncoderReranker
from app.retrieval.sparse import SparseRetriever
from app.services.retrieval_service import RetrievalService


def verify_phase3():
    logger.info("Initializing Phase 3 Hybrid Retrieval Pipeline...")

    dense_retriever = DenseRetriever(vectorstore_dir="vectorstore")
    sparse_retriever = SparseRetriever(vectorstore_dir="vectorstore")
    hybrid_retriever = HybridRetriever(dense_retriever, sparse_retriever)
    reranker = CrossEncoderReranker(model_name="BAAI/bge-reranker-base")

    pipeline = RetrievalPipeline(hybrid_retriever, reranker)
    service = RetrievalService(pipeline)

    test_queries = [
        "Remote code execution in Apache HTTP Server",
        "CVE-2024-3094 backdoor in xz utils",
        "Cisco ASA authentication bypass",
    ]

    for q in test_queries:
        print("\n" + "=" * 80)
        print(f"QUERY: {q}")
        print("=" * 80)

        output = service.search_threat_intel(q, top_n=3)
        metrics = output["metrics"]

        print(
            f"Metrics: Latency={metrics['total_latency_ms']}ms | Candidates={metrics['candidates_found']}"
        )
        print("-" * 80)

        for rank, (chunk, score) in enumerate(output["results"], start=1):
            meta = chunk.metadata
            print(f"Rank #{rank} | Score: {score:.4f} | Chunk ID: {chunk.chunk_id}")
            print(f"Title: {meta.title} ({meta.source} - {meta.severity})")
            print(f"Snippet: {chunk.text[:250]}...\n")


if __name__ == "__main__":
    verify_phase3()
