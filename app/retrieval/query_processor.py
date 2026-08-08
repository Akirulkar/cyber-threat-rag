# app/retrieval/query_processor.py
import re
from typing import Any, Dict, List, Tuple
from app.core.logger import logger


class QueryProcessor:
    @staticmethod
    def process(query: str) -> str:
        if not query:
            return ""

        query = re.sub(r"\s+", " ", query.strip())
        cve_pattern = r"(CVE-\d{4}-\d{4,7})"
        cves = re.findall(cve_pattern, query, flags=re.IGNORECASE)

        query_lower = query.lower()
        for cve in cves:
            query_lower = re.sub(re.escape(cve.lower()), cve.upper(), query_lower)

        return query_lower

    @staticmethod
    def is_meta_or_formatting_request(raw_query: str) -> bool:
        """Checks if the query is asking to simplify, rephrase, or format previous context."""
        cleaned = raw_query.strip().lower()

        formatting_patterns = [
            r"explain.*simpler",
            r"simpler\s+words",
            r"simple\s+terms",
            r"make\s+it\s+simpler",
            r"summarize\s+this",
            r"translate\s+this",
            r"rephrase",
            r"in\short",
            r"tl;?dr",
            r"bullet\s+points",
            r"explain\s+like\s+i'?m\s+5",
            r"eli5",
        ]

        return any(re.search(pattern, cleaned) for pattern in formatting_patterns)

    @staticmethod
    def rewrite_query_with_history(
        raw_query: str,
        chat_history: List[Dict[str, str]],
        llm_engine: Any = None,
    ) -> Tuple[str, bool]:
        """
        Returns a tuple of (processed_query, skip_retrieval).
        If skip_retrieval is True, RAGPipeline bypasses vector search and relies on chat history.
        """
        cleaned_query = QueryProcessor.process(raw_query)

        if not chat_history:
            return cleaned_query, False

        # If user asks to simplify/rephrase previous response, bypass vector store retrieval
        if QueryProcessor.is_meta_or_formatting_request(raw_query):
            logger.info(
                f"Meta/formatting request detected for query: '{raw_query}'. Skipping retrieval."
            )
            return cleaned_query, True

        # Check for pronouns or ambiguous follow-up triggers
        ambiguous_triggers = [
            "this",
            "it",
            "that",
            "explain",
            "how",
            "why",
            "mitigate",
            "them",
            "above",
        ]
        is_ambiguous = any(
            trigger in cleaned_query.lower().split() for trigger in ambiguous_triggers
        )

        if not is_ambiguous or not llm_engine:
            return cleaned_query, False

        # Prepare summary of recent chat history
        history_str = ""
        for msg in chat_history[-6:]:
            role = "User" if msg.get("role") == "user" else "Assistant"
            content = str(msg.get("content", ""))[:300]
            history_str += f"{role}: {content}\n"

        prompt = [
            {
                "role": "system",
                "content": (
                    "Given the following conversation history and a follow-up question, rewrite the follow-up question "
                    "into a single, self-contained, specific cybersecurity search query. Do NOT answer the question, "
                    "and do NOT include preamble. Return ONLY the rewritten query."
                ),
            },
            {
                "role": "user",
                "content": f"Chat History:\n{history_str}\nFollow-up Question: {cleaned_query}\n\nStandalone Search Query:",
            },
        ]

        try:
            standalone_query = llm_engine.generate(prompt).strip()
            logger.info(f"Query Rewritten: '{cleaned_query}' -> '{standalone_query}'")
            return standalone_query, False
        except Exception as e:
            logger.warning(
                f"Failed to rewrite query with history: {str(e)}. Falling back to raw query."
            )
            return cleaned_query, False
