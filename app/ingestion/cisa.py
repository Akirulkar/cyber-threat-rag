# app/ingestion/cisa.py
from typing import List, Dict, Any
from loguru import logger

from app.ingestion.base import BaseIngestor
from app.ingestion.downloader import downloader
from app.ingestion.models import (
    SourceType,
    DocumentType,
    DocumentMetadata,
    Severity,
)


class CISAIngestor(BaseIngestor):
    """Ingestor implementation for CISA Known Exploited Vulnerabilities (KEV) feed."""

    KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

    def __init__(self, data_dir: str = "data/raw", limit: int = None):
        super().__init__(data_dir=data_dir)
        self.limit = limit  # Default None fetches ALL records

    @classmethod
    def get_source_type(cls) -> SourceType:
        return SourceType.CISA

    def fetch_raw_data(self) -> List[Dict[str, Any]]:
        """Download complete CISA KEV JSON feed via resilient downloader."""
        logger.info(f"Downloading CISA KEV catalog from {self.KEV_URL}...")

        payload = downloader.fetch_json(self.KEV_URL, timeout=60)
        vulnerabilities = payload.get("vulnerabilities", [])

        logger.info(
            f"Retrieved total {len(vulnerabilities)} vulnerabilities from CISA KEV feed."
        )

        if self.limit:
            return vulnerabilities[: self.limit]

        return vulnerabilities

    def parse_raw_data(self, raw_item: Dict[str, Any]) -> DocumentMetadata:
        """Parse raw CISA KEV item into standardized DocumentMetadata."""
        cve_id = raw_item.get("cveID")

        if not cve_id:
            raise ValueError("Missing cveID in CISA item")

        title = raw_item.get("vulnerabilityName", f"CISA KEV Entry: {cve_id}")
        vendor = raw_item.get("vendorProject")
        product = raw_item.get("product")
        date_added = raw_item.get("dateAdded")

        if not date_added:
            raise ValueError(f"Missing dateAdded field for CISA KEV item: {cve_id}")

        return DocumentMetadata(
            document_id=f"CISA-KEV-{cve_id}",
            source=SourceType.CISA,
            document_type=DocumentType.KEV,
            title=title,
            url="https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
            published_date=date_added,
            severity=Severity.HIGH,
            vendor=vendor,
            product=product,
        )


if __name__ == "__main__":
    from app.core.logger import logger

    ingestor = CISAIngestor()
    summary = ingestor.run()

    print("\n--- CISA Ingestion Run Completed ---")
    print(f"Downloaded: {summary.downloaded_count}")
    print(f"Skipped: {summary.skipped_count}")
    print(f"Failed: {summary.failed_count}")
