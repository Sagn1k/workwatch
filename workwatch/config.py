"""Configuration and history file management for WorkWatch."""

import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".workwatch.json"
HISTORY_PATH = Path.home() / ".workwatch_history.json"

DEFAULT_CONFIG = {
    "work_hours": 9,
    "sender": "attendance@vmock.com",
}


def load_config() -> dict:
    """Load config from ~/.workwatch.json, creating defaults if missing."""
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=2) + "\n")
        print(f"📄 Created default config at {CONFIG_PATH}")
        print(f"   Edit work_hours or sender if needed.\n")
        return dict(DEFAULT_CONFIG)

    with open(CONFIG_PATH) as f:
        config = json.load(f)

    # Merge with defaults for any missing keys
    for key, value in DEFAULT_CONFIG.items():
        config.setdefault(key, value)

    return config


def load_history() -> dict:
    """Load attendance history from ~/.workwatch_history.json."""
    if not HISTORY_PATH.exists():
        return {}

    with open(HISTORY_PATH) as f:
        return json.load(f)


def save_history(history: dict) -> None:
    """Save attendance history to ~/.workwatch_history.json."""
    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2)
        f.write("\n")
