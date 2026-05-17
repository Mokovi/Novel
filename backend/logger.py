"""Loguru configuration."""

import sys
from pathlib import Path

from loguru import logger

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# File log: daily rotation, 30-day retention, DEBUG+
logger.add(
    str(LOG_DIR / "app_{time:YYYY-MM-DD}.log"),
    rotation="00:00",
    retention="30 days",
    level="DEBUG",
    encoding="utf-8",
)

# Console log: INFO+, colorized
logger.add(sys.stderr, level="INFO", colorize=True)
