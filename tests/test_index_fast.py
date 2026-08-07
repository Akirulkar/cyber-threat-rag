from pathlib import Path
import faiss
import numpy as np

from app.core.logger import logger
from app.embedding.embedder import TextEmbedder
from app.vectorstore.sqlite_store import SQLiteMetadataStore


def fast_search(
    query_text: str,
    top_k: int = 3,
    vectorstore_dir: str = "vectorstore",
    embedding_model_name: str = "BAAI/bge-base-en-v1.5",
):
    index_path = Path(vectorstore_dir) / "faiss.index"
    db_path = Path(vectorstore_dir) / "metadata.db"

    if not index_path.exists() or not db_path.exists():
        logger.error("Missing faiss.index or metadata.db. Run migration first!")
        return

    logger.info("Loading FAISS binary index...")
    faiss_index = faiss.read_index(str(index_path))
    logger.info(f"Loaded FAISS index containing {faiss_index.ntotal} vectors.")

    logger.info("Connecting to SQLite metadata store...")
    db_store = SQLiteMetadataStore(db_path=str(db_path))

    logger.info("Embedding query vector...")
    embedder = TextEmbedder(model_name=embedding_model_name)
    query_vector = embedder.embed_query(query_text)

    logger.info(f"Executing FAISS matrix search for top {top_k} results...")
    distances, indices = faiss_index.search(query_vector.astype(np.float32), top_k)

    top_ids = [int(i) for i in indices[0] if i != -1]
    scores = distances[0].tolist()

    logger.info("Fetching target metadata rows from SQLite...")
    chunks_map = db_store.get_chunks_by_faiss_ids(top_ids)

    print("\n" + "=" * 80)
    print(f"QUERY: {query_text}")
    print("=" * 80)

    for idx, (faiss_id, score) in enumerate(zip(top_ids, scores), start=1):
        chunk = chunks_map.get(faiss_id)
        if chunk:
            print(f"\n--- Result #{idx} (Score: {score:.4f}) ---")
            print(f"Chunk ID:  {chunk.chunk_id}")
            print(f"Doc ID:    {chunk.document_id}")
            print(f"Source:    {chunk.metadata.source}")
            print(f"Severity:  {chunk.metadata.severity}")
            print(f"Title:     {chunk.metadata.title}")
            print("Content Preview:")
            print(
                f"  {chunk.text[:300]}..."
                if len(chunk.text) > 300
                else f"  {chunk.text}"
            )

    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    fast_search("Remote code execution in Apache HTTP Server", top_k=3)
