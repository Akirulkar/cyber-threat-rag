import glob
import json
import os
from pathlib import Path
from typing import Generator, List, Optional


from app.core.logger import logger
from app.embedding.embedder import TextEmbedder
from app.ingestion.models import RawDocument
from app.models.chunk import Chunk
from app.processing.cleaner import TextCleaner
from app.processing.extractor import DocumentExtractor
from app.processing.metadata import ChunkProcessor
from app.vectorstore.faiss_store import FAISSVectorStore


def generate_chunk_batches(
    json_files: List[str],
    chunk_processor: ChunkProcessor,
    batch_size: int = 500,
) -> Generator[List[Chunk], None, None]:
    """Streams documents from disk, cleans/chunks them, and yields batches of chunks."""
    buffer: List[Chunk] = []
    processed_docs = 0
    failed_docs = 0
    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            # Validate JSON data
            raw_doc = RawDocument.model_validate(raw_data)
            raw_doc.file_path = str(file_path)

            # Extract structured text
            processed_doc = DocumentExtractor.extract(raw_doc)

            # Clean extracted narrative text
            processed_doc.extracted_text = TextCleaner.clean(
                processed_doc.extracted_text
            )

            # Split into chunks with metadata
            doc_chunks = chunk_processor.process_document(processed_doc)
            buffer.extend(doc_chunks)
            processed_docs += 1

            # Yield accumulated batch when threshold is reached
            while len(buffer) >= batch_size:
                yield buffer[:batch_size]
                buffer = buffer[batch_size:]
        except Exception as e:
            logger.error(f"Failed processing file {file_path}: {e}")
            failed_docs += 1

    # Yield remaining tail chunks in buffer
    if buffer:
        yield buffer
    logger.info(
        f"Ingestion stream finished. Total docs processed: {processed_docs}, Failed docs: {failed_docs}"
    )


def run_build_pipeline(
    raw_data_dir: str = "data/raw",
    vectorstore_dir: str = "vectorstore",
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    batch_size: int = 500,
    max_files: Optional[int] = None,
    embedding_model_name: str = "BAAI/bge-base-en-v1.5",
    checkpoint_interval: int = 20,
):
    """Pipeline executor using memory-efficient batched streaming."""

    # 1. Discover Raw Files
    logger.info(f"Scanning raw files in {raw_data_dir}...")
    json_files = glob.glob(os.path.join(raw_data_dir, "**/*.json"), recursive=True)
    if not json_files:
        logger.warning(f"No JSON raw files found in {raw_data_dir}. Exiting pipeline.")
        return

    # Cap processing if max_files is passed (e.g., during mini-pipeline test)
    if max_files and max_files > 0:
        json_files = json_files[:max_files]
        logger.info(f"Testing mode enabled: Capping run to {len(json_files)} files.")

    else:
        logger.info(f"Found {len(json_files)} raw documents to process.")

    # 2. Initialize Embedder & Vector Store

    logger.info(f"Loading embedding model: {embedding_model_name}...")
    embedder = TextEmbedder(model_name=embedding_model_name)
    faiss_store = FAISSVectorStore(dimension=embedder.embedding_dim)
    chunk_processor = ChunkProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    # 3. Stream, Embed & Index in Batches
    logger.info(
        f"Starting batched ingestion & indexing (Batch Size: {batch_size} chunks)..."
    )

    total_indexed_chunks = 0
    batch_num = 1

    for chunk_batch in generate_chunk_batches(
        json_files=json_files,
        chunk_processor=chunk_processor,
        batch_size=batch_size,
    ):
        logger.info(f"Processing Batch {batch_num} ({len(chunk_batch)} chunks)...")

        # Generate embeddings for current batch
        embedded_batch = embedder.embed_chunks(chunk_batch)

        # Incrementally add to FAISS store
        faiss_store.add_chunks(embedded_batch)
        total_indexed_chunks += len(embedded_batch)

        # Intermediate Checkpoint: Save store periodically
        if batch_num % checkpoint_interval == 0:
            logger.info(
                f"Checkpoint: Saving intermediate FAISS index ({total_indexed_chunks} chunks indexed so far)..."
            )
            faiss_store.save(folder_path=vectorstore_dir)
        batch_num += 1

    if total_indexed_chunks == 0:
        logger.warning("No valid chunks were generated. Aborting index save.")
        return

    # 4. Save Persistent FAISS Index
    logger.info(f"Persisting index with total {total_indexed_chunks} chunks to disk...")
    faiss_store.save(folder_path=vectorstore_dir)
    logger.info(f"SUCCESS: FAISS index successfully stored at '{vectorstore_dir}/'")


if __name__ == "__main__":
    run_build_pipeline()
