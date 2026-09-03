from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_local_env() -> None:
    """Load simple KEY=VALUE overrides without requiring another dependency."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


_load_local_env()
DATA_DIR = ROOT / "data"
VOICE_DIR = DATA_DIR / "voices"
PROJECT_DIR = DATA_DIR / "projects"
TEMP_DIR = DATA_DIR / "temp"
DB_PATH = DATA_DIR / "app.db"

MODEL_ROOT = Path(os.getenv("QWEN_TTS_MODEL_ROOT", str(ROOT / "models"))).expanduser()
MODEL_PATHS = {
    "voice_design": Path(
        os.getenv("QWEN_TTS_GENERATION_MODEL_PATH", str(MODEL_ROOT / "voice_design_1.7b"))
    ).expanduser(),
    "base": Path(
        os.getenv("QWEN_TTS_CLONE_MODEL_PATH", str(MODEL_ROOT / "voice_clone_1.7b"))
    ).expanduser(),
}

LANGUAGES = [
    "Chinese",
    "English",
    "Japanese",
    "Korean",
    "German",
    "French",
    "Russian",
    "Portuguese",
    "Spanish",
    "Italian",
    "Auto",
]

for directory in (DATA_DIR, VOICE_DIR, PROJECT_DIR, TEMP_DIR):
    directory.mkdir(parents=True, exist_ok=True)
