from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.models.document import ProcessedDocument
from app.models.chunk import Chunk, ChunkMetadata


class ChunkProcessor:
    """Splits processed documents into context-preserved chunks with metadata."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def process_document(self, doc: ProcessedDocument) -> List[Chunk]:
        raw_chunks = self.splitter.split_text(doc.extracted_text)
        total_chunks = len(raw_chunks)
        chunks: List[Chunk] = []

        for idx, text_chunk in enumerate(raw_chunks):
            chunk_id = f"{doc.document_id}_chunk_{idx}"

            metadata = ChunkMetadata(
                chunk_id=chunk_id,
                document_id=doc.document_id,
                source=doc.source,
                document_type=doc.document_type,
                title=doc.title,
                url=doc.url,
                severity=doc.severity,
                vendor=doc.vendor,
                product=doc.product,
                chunk_index=idx,
                total_chunks=total_chunks,
            )

            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=doc.document_id,
                    text=text_chunk,
                    metadata=metadata,
                )
            )

        return chunks
