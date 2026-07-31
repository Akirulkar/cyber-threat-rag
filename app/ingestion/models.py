from enum import Enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, HttpUrl, Field


class SourceType(str, Enum):
    NVD = "NVD"
    CISA = "CISA"
    MITRE = "MITRE"


class DocumentType(str, Enum):
    CVE = "CVE"  # Common Vulnerabilities and exposures
    KEV = "KEV"  # Known Exploited Vulnerabilities
    ADVISORY = "ADVISIORY"
    ATTACK_PATTERN = "ATTACK_PATTERN"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class DocumentMetadata(BaseModel):
    document_id: str = Field(..., description="Unique ID e.g., CVE-2026-1234")
    source: SourceType
    document_type: DocumentType
    title: str
    url: HttpUrl
    published_date: datetime
    updated_date: Optional[datetime] = None
    severity: Severity = Severity.UNKNOWN
    vendor: Optional[str] = None
    product: Optional[str] = None

    class Config:
        use_enum_values = True


class RawDocument(BaseModel):
    """Represents raw payload saved to disk before standardizing."""

    metadata: DocumentMetadata
    raw_content: dict  # Or string/bytes if file is PDF/HTML
    file_path: str


class IngestionSummary(BaseModel):
    """Logged at the end of a run for monitoring."""

    source: SourceType
    start_time: datetime
    end_time: datetime
    downloaded_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    errors: List[str] = []
