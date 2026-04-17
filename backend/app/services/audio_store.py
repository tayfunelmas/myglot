from __future__ import annotations

import uuid
from pathlib import Path

from ..config import get_config

# Map MIME to file extension
_EXT_MAP = {
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/wav": ".wav",
    "audio/ogg": ".ogg",
    "audio/webm": ".webm",
}


def save(audio_bytes: bytes, mime: str) -> str:
    """Save audio bytes to disk. Returns relative path under audio dir."""
    cfg = get_config()
    ext = _EXT_MAP.get(mime.split(";")[0], ".mp3")
    filename = f"{uuid.uuid4()}{ext}"
    filepath = cfg.audio_dir / filename
    filepath.write_bytes(audio_bytes)
    return filename


def get_absolute_path(relative_path: str) -> Path:
    """Get absolute path for an audio file."""
    cfg = get_config()
    return cfg.audio_dir / relative_path


def delete(relative_path: str) -> None:
    """Delete an audio file. Silently ignores missing files."""
    path = get_absolute_path(relative_path)
    path.unlink(missing_ok=True)
