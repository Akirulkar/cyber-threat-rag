from typing import List, Tuple
import tiktoken

from app.models.chunk import Chunk


class ContextBuilder:
    """Formats retrieved chunks into a structured context string within token limits."""

    def __init__(self, model_name: str = "gpt-3.5-turbo", max_tokens: int = 3000):
        try:
            self.tokenizer = tiktoken.encoding_for_model(model_name)
        except Exception:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.max_tokens = max_tokens

    def count_tokens(self, text: str) -> int:
        return len(self.tokenizer.encode(text))

    def build_context(
        self, chunk_score_pairs: List[Tuple[Chunk, float]]
    ) -> Tuple[str, List[dict]]:
        """
        Formats chunks into context blocks and tracks source citations.
        Returns (context_string, sources_list).
        """
        context_blocks = []
        sources = []
        current_tokens = 0

        for rank, (chunk, score) in enumerate(chunk_score_pairs, start=1):
            meta = chunk.metadata

            # Format explicit source metadata header for the LLM
            block_header = (
                f"--- [SOURCE #{rank}] ---\n"
                f"Document ID: {meta.document_id}\n"
                f"Source: {meta.source} | Type: {meta.document_type} | Severity: {meta.severity}\n"
                f"Title: {meta.title}\n"
                f"URL: {meta.url}\n"
                f"Content:\n"
            )
            block_text = (
                f"{block_header}{chunk.text.strip()}\n-------------------------\n\n"
            )

            block_tokens = self.count_tokens(block_text)

            # Enforce max token limit
            if current_tokens + block_tokens > self.max_tokens:
                break

            context_blocks.append(block_text)
            current_tokens += block_tokens

            sources.append(
                {
                    "rank": rank,
                    "chunk_id": chunk.chunk_id,
                    "document_id": meta.document_id,
                    "source": meta.source,
                    "document_type": meta.document_type,
                    "title": meta.title,
                    "severity": meta.severity,
                    "url": meta.url,
                    "rerank_score": score,
                }
            )

        formatted_context = "".join(context_blocks)
        return formatted_context, sources
