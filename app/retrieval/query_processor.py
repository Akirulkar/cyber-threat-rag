import re


class QueryProcessor:
    @staticmethod
    def process(query: str) -> str:
        if not query:
            return ""

        # Clean extra whitespace
        query = re.sub(r"\s+", " ", query.strip())

        # Preserve CVE IDs (e.g., CVE-2024-3094, CVE-2026-46621)
        cve_pattern = r"(CVE-\d{4}-\d{4,7})"
        cves = re.findall(cve_pattern, query, flags=re.IGNORECASE)

        query_lower = query.lower()

        # Ensure preserved CVE IDs maintain standard uppercase formatting
        for cve in cves:
            query_lower = re.sub(re.escape(cve.lower()), cve.upper(), query_lower)

        return query_lower
