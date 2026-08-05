import re
import html


class TextCleaner:
    """Sanitizes raw text strings into clean natural language."""

    @classmethod
    def clean(cls, text: str) -> str:
        if not text:
            return ""

        # Decode HTML entities (e.g., &amp; -> &)
        text = html.unescape(text)

        # Remove HTML tags if any present
        text = re.sub(r"<[^>]+>", " ", text)

        # Strip STIX/MITRE citation tags like (Citation: FireEye SUNBURST...)
        text = re.sub(r"\(Citation:[^\)]+\)", "", text)

        # Replace non-breaking spaces and control characters
        text = re.sub(r"[\r\t]", " ", text)

        # Collapse multi-spaces and multi-newlines
        text = re.sub(r" +", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text)

        return text.strip()
