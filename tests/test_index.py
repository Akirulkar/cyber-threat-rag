import sys
from pathlib import Path
from typing import List

from app.core.logger import logger
from app.embedding.embedder import TextEmbedder
from app.vectorstore.faiss_store import FAISSVectorStore


def verify_semantic_search(
    vectorstore_dir: str = "vectorstore",
    query_text: str = "SQL injection vulnerability in web application",
    top_k: int = 3,
    embedding_model_name: str = "BAAI/bge-base-en-v1.5",
):
    """Loads the stored FAISS index and performs a test retrieval query."""
    index_path = Path(vectorstore_dir) / "faiss.index"

    if not index_path.exists():
        logger.error(
            f"FAISS index file not found at '{index_path}'. "
            "Please run the build index pipeline first!"
        )
        sys.exit(1)

    logger.info(f"Loading vector store from '{vectorstore_dir}'...")
    faiss_store = FAISSVectorStore.load(folder_path=vectorstore_dir)

    indexed_total = faiss_store.index.ntotal if hasattr(faiss_store, "index") else "N/A"
    logger.info(f"Successfully loaded index containing {indexed_total} chunks.")

    logger.info(f"Initializing embedder model '{embedding_model_name}'...")
    embedder = TextEmbedder(model_name=embedding_model_name)

    logger.info(f"Embedding query: '{query_text}'")
    query_vector = embedder.embed_query(query_text)

    logger.info(f"Executing vector search (top_k={top_k})...")
    # Supports similarity_search or search depending on FAISSVectorStore method signature

    if hasattr(faiss_store, "search"):
        results = faiss_store.search(query_vector, top_k=top_k)
    else:
        logger.error("Unable to locate search method on FAISSVectorStore.")
        return

    print("\n" + "=" * 80)
    print(f"QUERY: {query_text}")
    print("=" * 80)

    for idx, item in enumerate(results, start=1):
        # Handle variations in return tuples (chunk, score) or result objects
        if isinstance(item, tuple):
            chunk, score = item
        else:
            chunk = item
            score = getattr(item, "score", 0.0)

        chunk_text = getattr(chunk, "text", str(chunk))
        chunk_id = getattr(chunk, "chunk_id", f"chunk_{idx}")
        metadata = getattr(chunk, "metadata", {})

        print(f"\n--- Result #{idx} (Score: {score:.4f}) ---")
        print(f"Chunk ID: {chunk_id}")
        if metadata:
            source = metadata.get("source_file") or metadata.get("cve_id") or "N/A"
            print(f"Source:   {source}")
        print("Content Preview:")
        print(
            f"  {chunk_text[:300]}..." if len(chunk_text) > 300 else f"  {chunk_text}"
        )

    print("\n" + "=" * 80 + "\n")


def run_verification_suite():
    """Runs a suite of sample cybersecurity queries to test retrieval quality."""
    sample_queries = [
        "Remote code execution in Apache HTTP Server",
        "Privilege escalation via Windows Kernel vulnerability",
        "Cross-site scripting XSS vulnerability in web application",
    ]

    for q in sample_queries:
        verify_semantic_search(query_text=q, top_k=2)


if __name__ == "__main__":
    # Run verification suite across common threat queries
    run_verification_suite()
