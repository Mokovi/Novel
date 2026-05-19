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


def save_config(config: dict) -> None:
    """Write the full config dict back to config.json."""
    config_path = DATA_DIR / "config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_env(key: str, default: str | None = None) -> str | None:
    return os.getenv(key, default)


def get_admin_password() -> str:
    return os.getenv("ADMIN_PASSWORD", "root")


def get_jwt_secret() -> str:
    return os.getenv("JWT_SECRET", "change-me-in-production")
