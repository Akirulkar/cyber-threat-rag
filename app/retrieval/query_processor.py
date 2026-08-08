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
        """Robust check for meta/formatting/simplification requests."""
        cleaned = raw_query.strip().lower()

        # Keywords that indicate the user wants a re-explanation of current context
        phrases = [
            "explain this",
            "simpler words",
            "simple terms",
            "make it simpler",
            "summarize this",
            "translate this",
            "rephrase",
            "in short",
            "tldr",
            "tl;dr",
            "bullet points",
            "explain like i'm 5",
            "eli5",
            "simplify",
        ]

        if any(phrase in cleaned for phrase in phrases):
            return True

        # Regex fallback for patterns like "explain ... in simpler ..."
        regex_patterns = [
            r"explain.*simpl",
            r"simpl.*word",
            r"simpl.*term",
            r"what.*does.*this.*mean",
        ]

        return any(re.search(pattern, cleaned) for pattern in regex_patterns)

    @staticmethod
    def rewrite_query_with_history(
        raw_query: str,
        chat_history: List[Dict[str, str]],
        llm_engine: Any = None,
    ) -> Tuple[str, bool]:
        cleaned_query = QueryProcessor.process(raw_query)

        if not chat_history:
            return cleaned_query, False

        # Check for simplification/meta requests FIRST
        if QueryProcessor.is_meta_or_formatting_request(raw_query):
            logger.info(
                f"Meta/formatting request detected for query: '{raw_query}'. Bypassing vector retrieval."
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
