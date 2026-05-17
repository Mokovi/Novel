"""Configuration loader — reads .env + data/config.json."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"


def load_config() -> dict:
    config_path = DATA_DIR / "config.json"
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_env(key: str, default: str | None = None) -> str | None:
    return os.getenv(key, default)
