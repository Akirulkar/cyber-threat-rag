# tests/conftest.py
import pytest
from pathlib import Path
from typing import Dict, Any


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """Provides a isolated temporary directory structure for file storage testing."""
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir


@pytest.fixture
def sample_cisa_raw_item() -> Dict[str, Any]:
    """Sample raw payload item from CISA KEV feed."""
    return {
        "cveID": "CVE-2023-23397",
        "vendorProject": "Microsoft",
        "product": "Outlook",
        "vulnerabilityName": "Microsoft Outlook Elevation of Privilege Vulnerability",
        "dateAdded": "2023-03-14",
        "shortDescription": "Microsoft Outlook contains a privilege escalation vulnerability.",
        "requiredAction": "Apply updates per vendor instructions.",
        "dueDate": "2023-04-04",
    }


@pytest.fixture
def sample_nvd_raw_item() -> Dict[str, Any]:
    """Sample raw payload item from NVD REST API."""
    return {
        "cve": {
            "id": "CVE-2021-44228",
            "published": "2021-12-10T10:15:00.000",
            "lastModified": "2021-12-14T21:15:00.000",
            "descriptions": [
                {
                    "lang": "en",
                    "value": "Apache Log4j2 JNDI features do not protect against attacker controlled LDAP.",
                }
            ],
            "metrics": {"cvssMetricV31": [{"cvssData": {"baseSeverity": "CRITICAL"}}]},
        }
    }
