# tests/test_ingestion.py
import json
from pathlib import Path
from app.ingestion.cisa import CISAIngestor
from app.ingestion.nvd import NVDIngestor
from app.ingestion.models import SourceType, Severity


def test_cisa_parser(sample_cisa_raw_item):
    """Verify CISAIngestor correctly parses raw KEV feed objects."""
    ingestor = CISAIngestor()
    doc = ingestor.parse_raw_data(sample_cisa_raw_item)

    assert doc.document_id == "CISA-KEV-CVE-2023-23397"
    assert doc.source == SourceType.CISA
    assert doc.vendor == "Microsoft"
    assert doc.product == "Outlook"
    assert doc.severity == Severity.HIGH


def test_nvd_parser(sample_nvd_raw_item):
    """Verify NVDIngestor correctly extracts CVSS severity and description."""
    ingestor = NVDIngestor()
    doc = ingestor.parse_raw_data(sample_nvd_raw_item)

    assert doc.document_id == "CVE-2021-44228"
    assert doc.source == SourceType.NVD
    assert doc.severity == Severity.CRITICAL
    assert "Log4j2 JNDI" in doc.title


def test_duplicate_detection_skips_existing_files(
    tmp_data_dir, sample_cisa_raw_item, mocker
):
    """Verify that BaseIngestor skips saving items if the file already exists on disk."""
    # 1. Create ingestor pointing to temporary data directory
    ingestor = CISAIngestor(data_dir=str(tmp_data_dir))

    # Mock network call to return a single item
    mocker.patch.object(ingestor, "fetch_raw_data", return_value=[sample_cisa_raw_item])

    # 2. First Run: File does not exist -> Should be downloaded/saved
    summary_1 = ingestor.run()
    assert summary_1.downloaded_count == 1
    assert summary_1.skipped_count == 0

    # Verify JSON file exists in target path
    expected_file = tmp_data_dir / "cisa" / "CISA-KEV-CVE-2023-23397.json"
    assert expected_file.exists()

    # 3. Second Run: File now exists on disk -> Should be skipped
    summary_2 = ingestor.run()
    assert summary_2.downloaded_count == 0
    assert summary_2.skipped_count == 1
