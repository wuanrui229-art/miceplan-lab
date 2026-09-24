from __future__ import annotations

import os
from pathlib import Path


SYSTEM_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_PATH = SYSTEM_ROOT / ".env"


def load_local_env(path: Path | None = None) -> Path:
    """Load local KEY=VALUE settings without overwriting process variables."""
    env_path = path or DEFAULT_ENV_PATH
    if not env_path.exists():
        return env_path

    for line_number, raw_line in enumerate(env_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            raise RuntimeError(f"Invalid .env entry on line {line_number}")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if not key:
            raise RuntimeError(f"Invalid .env key on line {line_number}")
        os.environ.setdefault(key, value)
    return env_path


def configuration_summary() -> dict[str, str | bool]:
    load_local_env()
    return {
        "parser": os.getenv("MICEPLAN_PARSER", "baseline").lower(),
        "endpoint": os.getenv("MICEPLAN_LLM_ENDPOINT", ""),
        "model": os.getenv("MICEPLAN_LLM_MODEL", ""),
        "api_key_configured": bool(os.getenv("MICEPLAN_LLM_API_KEY", "")),
    }
