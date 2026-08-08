# streamlit_app/api_client.py
import os
import requests
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env explicitly for Streamlit
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY_SECRET")


class APIClient:
    """Client for communicating with the FastAPI backend service."""

    def __init__(self, base_url: str = API_BASE_URL, api_key: str = API_KEY):
        self.base_url = base_url.rstrip("/")
        self.headers = {"Content-Type": "application/json", "X-API-Key": api_key}

    def health_check(self) -> bool:
        """Query /health endpoint to check backend status."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=3)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def query(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """Send a threat intelligence query to POST /query."""
        url = f"{self.base_url}/query"
        payload = {"query": question, "top_k": top_k}

        try:
            response = requests.post(
                url, json=payload, headers=self.headers, timeout=120
            )
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            elif response.status_code == 401:
                return {"success": False, "error": "Unauthorized: Invalid API Key."}
            else:
                return {
                    "success": False,
                    "error": f"Backend Error ({response.status_code}): {response.text}",
                }
        except requests.Timeout:
            return {
                "success": False,
                "error": "Request timed out while waiting for LLM response.",
            }
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"Could not connect to FastAPI backend at {self.base_url}",
            }

    def get_stats(self) -> Dict[str, Any]:
        """Fetch system and knowledge base metrics from GET /stats."""
        url = f"{self.base_url}/stats"
        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            return {"success": False, "error": f"Error {response.status_code}"}
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}


api_client = APIClient()
