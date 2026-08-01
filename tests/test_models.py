# tests/test_models.py
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from app.ingestion.models import (
    DocumentMetadata,
    SourceType,
    DocumentType,
    Severity,
    IngestionSummary,
)


def test_document_metadata_valid_creation():
    """Verify DocumentMetadata instantiates correctly with valid inputs."""
    doc = DocumentMetadata(
        document_id="CVE-2023-23397",
        source=SourceType.CISA,
        document_type=DocumentType.KEV,
        title="Microsoft Outlook Privilege Escalation",
        url="https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
        published_date="2023-03-14",
        severity=Severity.HIGH,
    )

    assert doc.document_id == "CVE-2023-23397"
    assert doc.source == SourceType.CISA
    assert isinstance(doc.published_date, datetime)
    assert doc.severity == Severity.HIGH


def test_document_metadata_missing_required_fields():
    """Verify validation fails when mandatory fields are omitted."""
    with pytest.raises(ValidationError):
        # Omitting mandatory 'document_id' and 'source'
        DocumentMetadata(
            title="Invalid Document",
            url="https://example.com",
            published_date="2023-01-01",
        )


def test_ingestion_summary_accumulators():
    """Verify IngestionSummary helper methods work as expected."""
    now = datetime.now(timezone.utc)
    summary = IngestionSummary(
        source=SourceType.NVD,
        start_time=now,
        end_time=now,
    )

    summary.downloaded_count += 5
    summary.skipped_count += 2
    summary.failed_count += 1

    assert summary.downloaded_count == 5
    assert summary.skipped_count == 2
    assert summary.failed_count == 1
