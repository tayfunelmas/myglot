from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (two levels up from this file, or cwd)
_project_root = Path(__file__).resolve().parent.parent.parent
_env_path = _project_root / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    load_dotenv()  # fall back to cwd


class Config:
    google_credentials: str | None
    data_dir: Path
    audio_dir: Path
    host: str
    port: int
    default_source_lang: str
    default_target_lang: str
    default_tts_voice: str
    translate_provider: str
    tts_provider: str
    stt_provider: str
    openai_api_key: str
    deepgram_api_key: str
    max_source_chars: int
    max_audio_upload_bytes: int

    def __init__(self) -> None:
        self.google_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.data_dir = Path(os.getenv("MYGLOT_DATA_DIR", "./data"))
        self.audio_dir = self.data_dir / "audio"
        self.host = os.getenv("MYGLOT_HOST", "127.0.0.1")
        self.port = int(os.getenv("MYGLOT_PORT", "8000"))
        self.default_source_lang = os.getenv("MYGLOT_DEFAULT_SOURCE_LANG", "en-US")
        self.default_target_lang = os.getenv("MYGLOT_DEFAULT_TARGET_LANG", "de-DE")
        self.default_tts_voice = os.getenv("MYGLOT_DEFAULT_TTS_VOICE", "")
        self.translate_provider = os.getenv("MYGLOT_TRANSLATE_PROVIDER", "google")
        self.tts_provider = os.getenv("MYGLOT_TTS_PROVIDER", "google")
        self.stt_provider = os.getenv("MYGLOT_STT_PROVIDER", "google")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.deepgram_api_key = os.getenv("DEEPGRAM_API_KEY", "")
        self.max_source_chars = int(os.getenv("MYGLOT_MAX_SOURCE_CHARS", "2000"))
        max_mb = int(os.getenv("MYGLOT_MAX_AUDIO_UPLOAD_MB", "10"))
        self.max_audio_upload_bytes = max_mb * 1024 * 1024

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_config() -> Config:
    cfg = Config()
    cfg.ensure_dirs()
    return cfg
