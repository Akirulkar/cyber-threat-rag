# app/ingestion/mitre.py
import requests
from typing import List, Dict, Any
from loguru import logger

from app.ingestion.base import BaseIngestor
from app.ingestion.models import (
    SourceType,
    DocumentType,
    DocumentMetadata,
    Severity,
)


class MITREIngestor(BaseIngestor):
    """Ingestor implementation for MITRE ATT&CK Techniques (Enterprise Matrix)."""

    # Public STIX 2.1 JSON repository for MITRE Enterprise ATT&CK
    STIX_URL = "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json"

    def __init__(self, data_dir: str = "data/raw", limit: int = None):
        super().__init__(data_dir=data_dir)
        self.limit = limit  # Optional cap for testing/debugging

    @classmethod
    def get_source_type(cls) -> SourceType:
        return SourceType.MITRE

    def fetch_raw_data(self) -> List[Dict[str, Any]]:
        """Download STIX bundle and extract only attack-pattern objects (Techniques)."""
        logger.info(f"Downloading MITRE Enterprise ATT&CK STIX data from GitHub...")

        response = requests.get(self.STIX_URL, timeout=60)
        response.raise_for_status()

        bundle = response.json()
        all_objects = bundle.get("objects", [])

        # Filter for active attack-pattern (Technique) objects only
        techniques = [
            obj
            for obj in all_objects
            if obj.get("type") == "attack-pattern"
            and not obj.get("x_mitre_deprecated", False)
        ]

        logger.info(f"Retrieved {len(techniques)} active MITRE ATT&CK techniques.")

        if self.limit:
            return techniques[: self.limit]

        return techniques

    def parse_raw_data(self, raw_item: Dict[str, Any]) -> DocumentMetadata:
        """Parse raw STIX attack-pattern into standardized DocumentMetadata."""
        external_refs = raw_item.get("external_references", [])

        # Find the mitre-attack external reference containing the technique ID (e.g., T1003)
        mitre_ref = next(
            (ref for ref in external_refs if ref.get("source_name") == "mitre-attack"),
            None,
        )

        if not mitre_ref or "external_id" not in mitre_ref:
            # Fallback to STIX ID if external_id is missing
            technique_id = raw_item.get("id", "").replace("attack-pattern--", "MITRE-")
            tech_url = "https://attack.mitre.org/"
        else:
            technique_id = mitre_ref["external_id"]
            tech_url = mitre_ref.get(
                "url", f"https://attack.mitre.org/techniques/{technique_id}"
            )

        name = raw_item.get("name", "Unnamed Technique")
        created_date = raw_item.get("created")
        modified_date = raw_item.get("modified")

        if not created_date:
            raise ValueError(
                f"Missing created date for MITRE technique: {technique_id}"
            )

        return DocumentMetadata(
            document_id=f"MITRE-{technique_id}",
            source=SourceType.MITRE,
            document_type=DocumentType.ATTACK_PATTERN,
            title=f"{technique_id}: {name}",
            url=tech_url,
            published_date=created_date,
            updated_date=modified_date,
            severity=Severity.UNKNOWN,  # ATT&CK techniques describe behavior, not severity
        )


if __name__ == "__main__":
    from app.core.logger import logger

    # Test run with first 10 items
    ingestor = MITREIngestor(limit=10)
    summary = ingestor.run()

    print("\n--- MITRE Ingestion Run Completed ---")
    print(f"Downloaded: {summary.downloaded_count}")
    print(f"Skipped: {summary.skipped_count}")
    print(f"Failed: {summary.failed_count}")
