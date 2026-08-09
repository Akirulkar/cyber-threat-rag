# app/pipeline/build_bm25_index.py
import pickle
import re
from pathlib import Path
from rank_bm25 import BM25Okapi

from app.core.logger import logger
from app.vectorstore_scripts.sqlite_store import SQLiteMetadataStore


def tokenize_text(text: str) -> list[str]:
    """Tokenizes text for BM25 keyword matching while preserving CVE IDs as single tokens."""
    cve_pattern = r"CVE-\d{4}-\d{4,7}"
    cves = [c.upper() for c in re.findall(cve_pattern, text, flags=re.IGNORECASE)]

    # Remove CVE strings temporarily to process standard words
    text_sans_cves = re.sub(cve_pattern, "", text, flags=re.IGNORECASE)
    words = re.findall(r"\w+", text_sans_cves.lower())

    return cves + words


def build_bm25_index(vectorstore_dir: str = "vectorstore"):
    db_path = Path(vectorstore_dir) / "metadata.db"
    bm25_output_path = Path(vectorstore_dir) / "bm25.pkl"

    if not db_path.exists():
        logger.error(f"Database file '{db_path}' not found! Run Phase 2 first.")
        return

    logger.info("Loading all chunks from SQLite for BM25 indexing...")
    db_store = SQLiteMetadataStore(db_path=str(db_path))

    with db_store._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT faiss_id, text FROM chunk_metadata ORDER BY faiss_id ASC;"
        )
        rows = cursor.fetchall()

    logger.info(f"Tokenizing {len(rows)} chunks for BM25 index...")
    faiss_ids = [row[0] for row in rows]
    corpus_tokens = [tokenize_text(row[1]) for row in rows]

    logger.info("Building BM25Okapi index...")
    bm25 = BM25Okapi(corpus_tokens)

    logger.info(f"Saving BM25 index to '{bm25_output_path}'...")
    with open(bm25_output_path, "wb") as f:
        pickle.dump({"faiss_ids": faiss_ids, "bm25": bm25}, f)

    logger.info("SUCCESS: BM25 index built and saved successfully.")


if __name__ == "__main__":
    build_bm25_index()
