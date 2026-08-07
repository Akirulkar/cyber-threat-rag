import pickle
from pathlib import Path

from app.core.logger import logger
from app.models.chunk import Chunk
from app.vectorstore.sqlite_store import SQLiteMetadataStore


def migrate_pickle_to_sqlite(vectorstore_dir: str = "vectorstore"):
    pkl_path = Path(vectorstore_dir) / "metadata.pkl"
    if not pkl_path.exists():
        logger.error(f"File '{pkl_path}' does not exist.")
        return

    logger.info(
        "Loading metadata.pkl into memory for migration (one-time operation)..."
    )
    with open(pkl_path, "rb") as f:
        doc_map = pickle.load(f)

    total_chunks = len(doc_map)
    logger.info(f"Loaded {total_chunks} chunks from pickle file.")

    db_store = SQLiteMetadataStore(db_path=f"{vectorstore_dir}/metadata.db")

    batch_size = 10000
    sorted_keys = sorted(doc_map.keys())

    logger.info(
        f"Migrating {total_chunks} chunks to SQLite in batches of {batch_size}..."
    )

    for i in range(0, total_chunks, batch_size):
        batch_keys = sorted_keys[i : i + batch_size]
        batch_chunks = [doc_map[k] for k in batch_keys]
        start_faiss_id = batch_keys[0]

        db_store.add_chunks_batch(batch_chunks, start_faiss_id=start_faiss_id)
        logger.info(f"Migrated chunks {i + len(batch_chunks)} / {total_chunks}...")

    logger.info(
        f"SUCCESS: Migration complete! 'vectorstore/metadata.db' created successfully."
    )


if __name__ == "__main__":
    migrate_pickle_to_sqlite()
