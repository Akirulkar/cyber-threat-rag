import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

NVD_API_KEY = os.getenv("NVD_API_KEY", None)
DATA_DIR = os.getenv("DATA_DIR", "data/raw")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
