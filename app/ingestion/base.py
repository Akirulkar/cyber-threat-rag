from abc import ABC, abstractmethod
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Tuple, Any

from loguru import logger
from app.ingestion.models import (
    DocumentMetadata,
    RawDocument,
    IngestionSummary,
    SourceType,
)


class BaseIngestor(ABC):
    def __init__(self, data_dir: str = "data/raw"):
        self.source = self.get_source_type()
        self.output_dir = Path(data_dir) / self.source.value.lower()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    @abstractmethod
    def get_source_type(cls) -> SourceType:
        """Return the specific SourceType Enum value for this ingestor."""
        pass

    @abstractmethod
    def parse_raw_data(self, raw_item: Any) -> DocumentMetadata:
        """Transform a single raw item into the standardized DocumentMetadata model.

        Must be implemented by each source ingestor.
        """
        pass

    def get_file_path(self, document_id: str) -> Path:
        """Construct the standard file path for storing a raw record."""
        # Sanitize filename (e.g. replace slashes in IDs)
        safe_id = document_id.replace("/", "_").replace("\\", "_")
        return self.output_dir / f"{safe_id}.json"

    def _is_duplicate(self, document_id: str) -> bool:
        """Check if document raw JSON already exists on disk."""
        file_path = self.get_file_path(document_id)
        return file_path.exists()

    def _save_raw_file(self, raw_doc: RawDocument) -> Path:
        """Save raw document data and metadata onto disk as standard JSON source of truth."""
        file_path = Path(raw_doc.file_path)

        # Combine canonical metadata and original API payload
        payload = {
            "metadata": raw_doc.metadata.model_dump(mode="json"),
            "raw_content": raw_doc.raw_content,
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        return file_path

    def run(self) -> IngestionSummary:
        """Execute the standard ingestion lifecycle.

        Template method that drives the ingestion pipeline step-by-step.
        """
        start_time = datetime.now(timezone.utc)
        logger.info(f"Starting ingestion for {self.source.value}...")

        summary = IngestionSummary(
            source=self.source,
            start_time=start_time,
            end_time=start_time,
        )

        try:
            # Step 1: Fetch raw records from external API
            raw_items = self.fetch_raw_data()
            logger.info(f"Fetched {len(raw_items)} raw items from {self.source.value}.")

            for item in raw_items:
                try:
                    # Step 2: Parse raw record to standardized Pydantic model
                    metadata = self.parse_raw_data(item)

                    # Step 3: Duplicate Check
                    if self._is_duplicate(metadata.document_id):
                        logger.debug(
                            f"Skipping duplicate document: {metadata.document_id}"
                        )
                        summary.skipped_count += 1
                        continue

                    # Step 4: Construct RawDocument wrapper
                    file_path = self.get_file_path(metadata.document_id)
                    raw_doc = RawDocument(
                        metadata=metadata,
                        raw_content=(
                            item if isinstance(item, dict) else {"content": str(item)}
                        ),
                        file_path=str(file_path),
                    )

                    # Step 5: Save raw record on disk
                    self._save_raw_file(raw_doc)
                    summary.downloaded_count += 1
                    logger.debug(f"Saved raw document: {metadata.document_id}")

                except Exception as doc_err:
                    err_msg = f"Failed processing document item: {str(doc_err)}"
                    logger.error(err_msg)
                    summary.failed_count += 1
                    summary.errors.append(err_msg)

        except Exception as source_err:
            critical_msg = f"Fatal error during {self.source.value} download phase: {str(source_err)}"
            logger.critical(critical_msg)
            summary.errors.append(critical_msg)

        summary.end_time = datetime.now(timezone.utc)
        logger.info(
            f"Finished {self.source.value} ingestion: "
            f"Downloaded={summary.downloaded_count}, "
            f"Skipped={summary.skipped_count}, "
            f"Failed={summary.failed_count}"
        )

        return summary
