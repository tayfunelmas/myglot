import shutil
import sqlite3
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, UploadFile
from fastapi.responses import FileResponse

from ..config import get_config
from ..db import reset_engine
from ..errors import ValidationError
from ..providers.base import ProviderError
from ..providers.registry import get_stt, get_translator, get_tts
from ..schemas import HealthProviders, ProviderStatus

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/health/providers", response_model=HealthProviders)
def health_providers():
    cfg = get_config()

    def check_translator() -> ProviderStatus:
        try:
            t = get_translator()
            return ProviderStatus(provider=t.name, ok=True)
        except (ProviderError, Exception) as e:
            return ProviderStatus(provider=cfg.translate_provider, ok=False, error=str(e))

    def check_tts() -> ProviderStatus:
        try:
            t = get_tts()
            return ProviderStatus(provider=t.name, ok=True)
        except (ProviderError, Exception) as e:
            return ProviderStatus(provider=cfg.tts_provider, ok=False, error=str(e))

    def check_stt() -> ProviderStatus:
        try:
            s = get_stt()
            return ProviderStatus(provider=s.name, ok=True)
        except (ProviderError, Exception) as e:
            return ProviderStatus(provider=cfg.stt_provider, ok=False, error=str(e))

    return HealthProviders(
        translator=check_translator(),
        tts=check_tts(),
        stt=check_stt(),
    )


@router.get("/backup")
def backup_database():
    """Download a consistent snapshot of the SQLite database."""
    cfg = get_config()
    db_path = str(cfg.data_dir / "myglot.db")

    # Use SQLite Online Backup API for a consistent, lock-free copy
    source = sqlite3.connect(db_path)
    tmp_path = tempfile.mktemp(suffix=".db")
    dest = sqlite3.connect(tmp_path)
    try:
        source.backup(dest)
    finally:
        dest.close()
        source.close()

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    filename = f"myglot_backup_{timestamp}.db"
    return FileResponse(
        path=tmp_path,
        media_type="application/x-sqlite3",
        filename=filename,
    )


@router.post("/restore")
async def restore_database(file: UploadFile):
    """Replace the current database with an uploaded backup.

    Validates that the uploaded file is a valid SQLite database containing
    the expected tables before swapping it in.
    """
    cfg = get_config()
    db_path = Path(cfg.data_dir / "myglot.db")

    # Save upload to a temp file
    tmp_path = tempfile.mktemp(suffix=".db")
    try:
        content = await file.read()
        Path(tmp_path).write_bytes(content)

        # Validate: must be a valid SQLite DB with expected tables
        conn = sqlite3.connect(tmp_path)
        try:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            required = {"item", "settings"}
            missing = required - tables
            if missing:
                raise ValidationError(
                    f"Invalid backup: missing tables {missing}. "
                    "This does not look like a MyGlot database."
                )
        finally:
            conn.close()

        # Dispose the current engine so connections are closed
        reset_engine()

        # Create a timestamped backup of the current DB before overwriting
        if db_path.exists():
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            pre_restore = db_path.with_name(f"myglot_pre_restore_{timestamp}.db")
            shutil.copy2(str(db_path), str(pre_restore))

        # Replace the database file
        shutil.move(tmp_path, str(db_path))

        # Re-initialize the engine (picks up the restored DB)
        from ..db import init_db

        init_db()

        return {"status": "ok", "message": "Database restored successfully."}
    except ValidationError:
        raise
    except Exception as e:
        # Try to re-init even on error so the app keeps working
        try:
            from ..db import init_db

            init_db()
        except Exception:
            pass
        raise ValidationError(f"Restore failed: {e}") from e
    finally:
        # Clean up temp file if it still exists
        tmp = Path(tmp_path)
        if tmp.exists():
            tmp.unlink()
