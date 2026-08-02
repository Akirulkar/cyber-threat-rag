import time
from typing import List, Dict, Any, Optional
from loguru import logger

from app.ingestion.base import BaseIngestor
from app.ingestion.downloader import downloader
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

    def __init__(self, data_dir: str = "data/raw", results_per_page: int = 2000):
        super().__init__(data_dir=data_dir)
        # NVD API allows a maximum of 2,000 results per request
        self.results_per_page = min(results_per_page, 2000)
        self.headers = {}
        if NVD_API_KEY:
            self.headers["apiKey"] = NVD_API_KEY

    @classmethod
    def get_source_type(cls) -> SourceType:
        return SourceType.NVD

    def fetch_raw_data(self) -> List[Dict[str, Any]]:
        """Paginate through the entire NVD v2.0 REST API to fetch ALL CVEs."""
        all_cves: List[Dict[str, Any]] = []
        start_index = 0

        # NVD rate limits: 50 requests/30s with API key, 5 requests/30s without key
        sleep_delay = 0.6 if NVD_API_KEY else 6.0

        logger.info(
            f"Beginning full dataset ingestion from NVD API "
            f"(page size: {self.results_per_page}, key present: {bool(NVD_API_KEY)})..."
        )

        while True:
            params = {
                "resultsPerPage": self.results_per_page,
                "startIndex": start_index,
            }

            response = downloader.fetch_json(
                self.BASE_URL,
                headers=self.headers,
                params=params,
                timeout=60,
            )

            vulnerabilities = response.get("vulnerabilities", [])
            total_results = response.get("totalResults", 0)

            all_cves.extend(vulnerabilities)

            logger.info(
                f"Fetched {len(all_cves)} / {total_results} CVEs "
                f"(Batch: {start_index} - {start_index + len(vulnerabilities)})"
            )

            start_index += len(vulnerabilities)

            # Exit loop when all records are fetched or no items returned
            if start_index >= total_results or not vulnerabilities:
                break

            time.sleep(sleep_delay)

        logger.info(
            f"Successfully retrieved total {len(all_cves)} raw records from NVD."
        )
        return all_cves

    def parse_raw_data(self, raw_item: Dict[str, Any]) -> DocumentMetadata:
        """Parse raw NVD JSON vulnerability item into standardized DocumentMetadata."""
        cve_data = raw_item.get("cve", {})
        cve_id = cve_data.get("id")

        if not cve_id:
            raise ValueError("Missing CVE ID in raw NVD payload")

        descriptions = cve_data.get("descriptions", [])
        english_desc = next(
            (d["value"] for d in descriptions if d.get("lang") == "en"),
            "No description available",
        )
        title = (
            (english_desc[:117] + "...") if len(english_desc) > 120 else english_desc
        )

        metrics = cve_data.get("metrics", {})
        severity = self._extract_severity(metrics)

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

    ingestor = NVDIngestor()
    summary = ingestor.run()

    print("\n--- NVD Ingestion Completed ---")
    print(f"Downloaded: {summary.downloaded_count}")
    print(f"Skipped: {summary.skipped_count}")
    print(f"Failed: {summary.failed_count}")
