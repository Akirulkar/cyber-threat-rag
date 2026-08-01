# app/ingestion/scheduler.py
from typing import List
from datetime import datetime, timezone
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.logger import logger
from app.ingestion.base import BaseIngestor
from app.ingestion.models import IngestionSummary
from app.ingestion.nvd import NVDIngestor
from app.ingestion.cisa import CISAIngestor
from app.ingestion.mitre import MITREIngestor


def run_all_ingestors() -> List[IngestionSummary]:
    """Execute all registered ingestors sequentially.

    Returns a list of IngestionSummary objects representing the run status
    for each source.
    """
    logger.info("=== Starting Security Ingestion Pipeline Run ===")
    start_time = datetime.now(timezone.utc)

    # Register all ingestors in the pipeline
    ingestors: List[BaseIngestor] = [
        NVDIngestor(),
        CISAIngestor(),
        MITREIngestor(),
    ]

    summaries: List[IngestionSummary] = []

    for ingestor in ingestors:
        try:
            summary = ingestor.run()
            summaries.append(summary)
        except Exception as e:
            logger.error(
                f"Ingestor '{ingestor.get_source_type().value}' failed critically: {str(e)}"
            )

    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
    logger.info(f"=== Finished Ingestion Pipeline Run in {elapsed:.2f} seconds ===")

    # Summary report across all sources
    total_downloaded = sum(s.downloaded_count for s in summaries)
    total_skipped = sum(s.skipped_count for s in summaries)
    total_failed = sum(s.failed_count for s in summaries)

    logger.info(
        f"Pipeline Totals: Downloaded={total_downloaded} | "
        f"Skipped={total_skipped} | "
        f"Failed={total_failed}"
    )

    return summaries


def start_scheduler(hours: int = 24, run_immediately: bool = True):
    """Start the APScheduler blocking loop.

    Args:
        hours: How often (in hours) to trigger the ingestion pipeline.
        run_immediately: Whether to perform a run immediately upon startup.
    """
    scheduler = BlockingScheduler()

    # Schedule the pipeline job to run every `hours` hours
    scheduler.add_job(
        run_all_ingestors,
        trigger=IntervalTrigger(hours=hours),
        id="security_document_ingestion_job",
        name="Security Document Ingestion Pipeline",
        replace_existing=True,
    )

    logger.info(f"Scheduler initialized. Configured to run every {hours} hours.")

    if run_immediately:
        logger.info("Executing initial startup ingestion run...")
        run_all_ingestors()

    try:
        logger.info("Scheduler running. Press Ctrl+C to exit.")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler shut down gracefully.")


if __name__ == "__main__":
    # Command line entry point: run once immediately or run scheduler loop
    import sys

    if "--once" in sys.argv:
        # Single-run mode (ideal for CI/CD or manual cron jobs)
        run_all_ingestors()
    else:
        # Daemon/Scheduler mode (runs continuously)
        start_scheduler(hours=24, run_immediately=True)
