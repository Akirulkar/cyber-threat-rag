import sys
from pathlib import Path
from loguru import logger
from app.core.config import LOG_LEVEL

log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logger.remove()
logger.add(sys.stdout, level=LOG_LEVEL)
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="7 days",
    level=LOG_LEVEL,
    enqueue=True,
)
