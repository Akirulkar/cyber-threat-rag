import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from app.ingestion.base import BaseIngestor
from app.ingestion.downloader import downloader  # Import resilient downloader
from app.ingestion.models import (
    SourceType,
    DocumentType,
    DocumentMetadata,
    Severity,
)
from app.core.config import NVD_API_KEY


class NVDIngestor(BaseIngestor):
    """Ingestor implementation for National Vulnerability Database (NVD) CVEs."""

    BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

    def __init__(self, data_dir: str = "data/raw", results_per_page: int = 50):
        super().__init__(data_dir=data_dir)
        self.results_per_page = results_per_page
        self.headers = {}
        if NVD_API_KEY:
            self.headers["apiKey"] = NVD_API_KEY

    @classmethod
    def get_source_type(cls) -> SourceType:
        return SourceType.NVD

    def fetch_raw_data(self) -> List[Dict[str, Any]]:
        """Fetch latest CVE items from NVD API v2.0."""
        params = {
            "resultsPerPage": self.results_per_page,
            "startIndex": 0,
        }

        logger.info(f"Fetching up to {self.results_per_page} records from NVD API...")

        response = downloader.fetch_json(
            self.BASE_URL,
            headers=self.headers,
            params=params,
            timeout=30,
        )

        cve_items = response.get("vulnerabilities", [])
        return cve_items

    def parse_raw_data(self, raw_item: Dict[str, Any]) -> DocumentMetadata:
        """Parse raw NVD JSON vulnerability item into standardized DocumentMetadata."""
        cve_data = raw_item.get("cve", {})
        cve_id = cve_data.get("id")

        if not cve_id:
            raise ValueError("Missing CVE ID in raw NVD payload")

        # 1. Extract Description / Title
        descriptions = cve_data.get("descriptions", [])
        english_desc = next(
            (d["value"] for d in descriptions if d.get("lang") == "en"),
            "No description available",
        )
        # NVD doesn't provide explicit titles, so truncate description for title
        title = (
            (english_desc[:117] + "...") if len(english_desc) > 120 else english_desc
        )

        # 2. Extract CVSS Severity (Check CVSS v3.1, then v3.0, then v2)
        metrics = cve_data.get("metrics", {})
        severity = self._extract_severity(metrics)

        # 3. Extract Dates (Pydantic auto-parses ISO 8601 strings to datetime)
        published_str = cve_data.get("published")
        updated_str = cve_data.get("lastModified")

        if not published_str:
            raise ValueError(f"Missing publication date for {cve_id}")

        return DocumentMetadata(
            document_id=cve_id,
            source=SourceType.NVD,
            document_type=DocumentType.CVE,
            title=title,
            url=f"https://nvd.nist.gov/vuln/detail/{cve_id}",
            published_date=published_str,
            updated_date=updated_str,
            severity=severity,
        )

    def _extract_severity(self, metrics: Dict[str, Any]) -> Severity:
        """Extract severity rating from CVSS metrics payload."""
        cvss_v31 = metrics.get("cvssMetricV31", [])
        if cvss_v31:
            base_severity = cvss_v31[0].get("cvssData", {}).get("baseSeverity", "")
            return self._map_severity(base_severity)

        cvss_v30 = metrics.get("cvssMetricV30", [])
        if cvss_v30:
            base_severity = cvss_v30[0].get("cvssData", {}).get("baseSeverity", "")
            return self._map_severity(base_severity)

        cvss_v2 = metrics.get("cvssMetricV2", [])
        if cvss_v2:
            base_severity = cvss_v2[0].get("baseSeverity", "")
            return self._map_severity(base_severity)

        return Severity.UNKNOWN

    @staticmethod
    def _map_severity(raw_severity: str) -> Severity:
        """Map raw string severity to Severity Enum."""
        sev_upper = raw_severity.upper()
        if sev_upper in Severity.__members__:
            return Severity[sev_upper]
        return Severity.UNKNOWN


if __name__ == "__main__":
    from app.core.logger import logger

    ingestor = NVDIngestor(results_per_page=5)
    summary = ingestor.run()

    print("\n--- Ingestion Run Completed ---")
    print(f"Downloaded: {summary.downloaded_count}")
    print(f"Skipped: {summary.skipped_count}")
    print(f"Failed: {summary.failed_count}")
