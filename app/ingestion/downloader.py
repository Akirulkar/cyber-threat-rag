# app/ingestion/downloader.py
from typing import Dict, Any, Optional
import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception,
    before_sleep_log,
)
from loguru import logger

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _is_retryable_exception(exception: Exception) -> bool:
    if isinstance(exception, requests.exceptions.HTTPError):
        response = exception.response
        if response is not None:
            return response.status_code in RETRYABLE_STATUS_CODES

    if isinstance(
        exception, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)
    ):
        return True

    return False


class ResilientDownloader:
    """HTTP client wrapper with exponential backoff retries via Tenacity."""

    def __init__(self, user_agent: str = "CyberThreatRAG/1.0", timeout: int = 30):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.default_timeout = timeout

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential_jitter(initial=2, max=30),
        retry=retry_if_exception(_is_retryable_exception),
        before_sleep=before_sleep_log(logger, "WARNING"),
        reraise=True,
    )
    def fetch_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,  # Accept optional timeout override
    ) -> Dict[str, Any]:
        """Fetch JSON payload with automatic retries on rate limits and server errors."""
        logger.debug(f"GET Request -> {url} (params: {params})")

        request_timeout = timeout if timeout is not None else self.default_timeout

        response = self.session.get(
            url, params=params, headers=headers, timeout=request_timeout
        )

        response.raise_for_status()
        return response.json()


# Shared singleton downloader instance
downloader = ResilientDownloader()
