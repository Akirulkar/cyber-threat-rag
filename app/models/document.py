from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl, Field
from app.ingestion.models import (
    SourceType,
    DocumentType,
    Severity,
)  # Import from Phase 1 models


class ProcessedDocument(BaseModel):
    """Normalized document payload ready for chunking."""

    document_id: str
    source: SourceType
    document_type: DocumentType
    title: str
    url: str
    published_date: datetime
    updated_date: Optional[datetime] = None
    severity: Severity = Severity.UNKNOWN
    vendor: Optional[str] = None
    product: Optional[str] = None

    # Cleaned narrative text extracted from source payload
    extracted_text: str

    # Source-specific domain attributes
    extra_attributes: Dict[str, Any] = Field(default_factory=dict)
