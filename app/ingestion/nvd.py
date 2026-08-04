# app/ingestion/nvd.py
import time
from typing import List, Dict, Any
from datetime import datetime, timezone
from loguru import logger

from app.ingestion.base import BaseIngestor
from app.ingestion.downloader import downloader
from app.ingestion.models import (
    SourceType,
    DocumentType,
    DocumentMetadata,
    Severity,
    IngestionSummary,
)
from app.core.config import NVD_API_KEY


class NVDIngestor(BaseIngestor):
    """Ingestor implementation for National Vulnerability Database (NVD) CVEs with batch persistence."""

    BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

    def __init__(self, data_dir: str = "data/raw", results_per_page: int = 2000):
        super().__init__(data_dir=data_dir)
        self.results_per_page = min(results_per_page, 2000)
        self.headers = {}
        if NVD_API_KEY:
            self.headers["apiKey"] = NVD_API_KEY

    @classmethod
    def get_source_type(cls) -> SourceType:
        return SourceType.NVD

    def run(self) -> IngestionSummary:
        """Overridden run method to perform streaming batch ingestion and disk persistence."""
        summary = IngestionSummary(
            source=self.get_source_type(),
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
        )

        logger.info(f"Starting streaming ingestion for {self.get_source_type().value}...")
        
        start_index = 0
        sleep_delay = 0.6 if NVD_API_KEY else 6.0

        while True:
            params = {
                "resultsPerPage": self.results_per_page,
                "startIndex": start_index,
            }

            try:
                response = downloader.fetch_json(
                    self.BASE_URL,
                    headers=self.headers,
                    params=params,
                    timeout=60,
                )
            except Exception as e:
                logger.error(f"Failed to fetch batch starting at index {start_index}: {e}")
                summary.failed_count += self.results_per_page
                break

            vulnerabilities = response.get("vulnerabilities", [])
            total_results = response.get("totalResults", 0)

            # Process and save this batch immediately!
            for raw_item in vulnerabilities:
                try:
                    metadata = self.parse_raw_data(raw_item)
                    saved = self.save_raw_document(metadata, raw_item)
                    if saved:
                        summary.downloaded_count += 1
                    else:
                        summary.skipped_count += 1
                except Exception as parse_err:
                    logger.warning(f"Failed parsing item in batch {start_index}: {parse_err}")
                    summary.failed_count += 1

            start_index += len(vulnerabilities)
            logger.info(
                f"Progress: {start_index} / {total_results} CVEs evaluated | "
                f"Saved: {summary.downloaded_count} | Skipped: {summary.skipped_count}"
            )

            if start_index >= total_results or not vulnerabilities:
                break

            time.sleep(sleep_delay)

        summary.end_time = datetime.now(timezone.utc)
        logger.info(
            f"Finished NVD ingestion: Downloaded={summary.downloaded_count}, "
            f"Skipped={summary.skipped_count}, Failed={summary.failed_count}"
        )
        return summary

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
        title = (english_desc[:117] + "...") if len(english_desc) > 120 else english_desc

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
