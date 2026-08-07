import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.models.chunk import Chunk, ChunkMetadata


class SQLiteMetadataStore:
    """Fast, persistent SQLite metadata store for FAISS vector indices."""

    def __init__(self, db_path: str = "vectorstore/metadata.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunk_metadata (
                    faiss_id INTEGER PRIMARY KEY,
                    chunk_id TEXT UNIQUE,
                    document_id TEXT,
                    text TEXT,
                    source TEXT,
                    severity TEXT,
                    title TEXT,
                    url TEXT,
                    metadata_json TEXT
                );
                """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_chunk_id ON chunk_metadata(chunk_id);"
            )

    def add_chunks_batch(self, chunks: List[Chunk], start_faiss_id: int):
        """Inserts a batch of Chunk models into SQLite starting at start_faiss_id."""
        records = []
        for idx, chunk in enumerate(chunks):
            faiss_id = start_faiss_id + idx
            meta = chunk.metadata

            records.append(
                (
                    faiss_id,
                    chunk.chunk_id,
                    chunk.document_id,
                    chunk.text,
                    meta.source,
                    meta.severity,
                    meta.title,
                    meta.url,
                    meta.model_dump_json(),
                )
            )

        with self._get_connection() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO chunk_metadata 
                (faiss_id, chunk_id, document_id, text, source, severity, title, url, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                records,
            )

    def get_chunk_by_faiss_id(self, faiss_id: int) -> Optional[Chunk]:
        """Retrieves and reconstructs a single Chunk Pydantic model by FAISS integer ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT chunk_id, document_id, text, metadata_json 
                FROM chunk_metadata WHERE faiss_id = ?;
                """,
                (faiss_id,),
            )
            row = cursor.fetchone()
            if row:
                chunk_id, document_id, text, metadata_json = row
                metadata_dict = json.loads(metadata_json)
                metadata = ChunkMetadata.model_validate(metadata_dict)

                return Chunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    text=text,
                    metadata=metadata,
                    embedding=None,  # Vectors remain in FAISS binary
                )
            return None

    def get_chunks_by_faiss_ids(self, faiss_ids: List[int]) -> Dict[int, Chunk]:
        """Retrieves top-K Chunk models in bulk by their FAISS integer IDs instantly."""
        if not faiss_ids:
            return {}

        placeholders = ",".join(["?"] * len(faiss_ids))
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT faiss_id, chunk_id, document_id, text, metadata_json 
                FROM chunk_metadata WHERE faiss_id IN ({placeholders});
                """,
                faiss_ids,
            )
            rows = cursor.fetchall()

            result = {}
            for row in rows:
                faiss_id, chunk_id, document_id, text, metadata_json = row
                metadata_dict = json.loads(metadata_json)
                metadata = ChunkMetadata.model_validate(metadata_dict)

                result[faiss_id] = Chunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    text=text,
                    metadata=metadata,
                    embedding=None,
                )
            return result
