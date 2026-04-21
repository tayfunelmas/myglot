"""Background auto-backup scheduler.

Runs as an asyncio task inside the FastAPI process.
Every 60 seconds it checks whether a backup is due (based on the cron expression
stored in the BackupSchedule DB row) and, if so, creates a consistent SQLite
snapshot in the configured destination directory.
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from croniter import croniter
from sqlmodel import Session

from .config import get_config
from .db import get_engine
from .models import BackupSchedule

logger = logging.getLogger(__name__)


def _resolve_destination(schedule: BackupSchedule) -> Path:
    """Return the directory where backups should be written."""
    if schedule.destination_dir:
        return Path(schedule.destination_dir)
    return get_config().data_dir / "backups"


def _run_backup(db_path: Path, dest_dir: Path, max_backups: int) -> str:
    """Perform a single backup and rotate old files.  Returns the backup filename."""
    dest_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    backup_name = f"myglot_auto_{timestamp}.db"
    backup_path = dest_dir / backup_name

    source = sqlite3.connect(str(db_path))
    dest = sqlite3.connect(str(backup_path))
    try:
        source.backup(dest)
    finally:
        dest.close()
        source.close()

    # Rotate: keep only the newest max_backups files
    backups = sorted(dest_dir.glob("myglot_auto_*.db"), key=lambda p: p.stat().st_mtime)
    while len(backups) > max_backups:
        oldest = backups.pop(0)
        oldest.unlink()

    return backup_name


async def _scheduler_loop() -> None:
    """Infinite loop: sleep 60s, check cron, run backup if due."""
    while True:
        await asyncio.sleep(60)
        try:
            with Session(get_engine()) as session:
                schedule = session.get(BackupSchedule, 1)
                if schedule is None or not schedule.enabled:
                    continue

                # Determine if a backup is due
                now = datetime.now(UTC)
                cron = croniter(schedule.cron_expr, schedule.last_run_at or now)
                next_run = cron.get_next(datetime)

                # If last_run_at is None we haven't run yet — trigger immediately
                if schedule.last_run_at is not None and next_run > now:
                    continue

                cfg = get_config()
                db_path = cfg.data_dir / "myglot.db"
                dest_dir = _resolve_destination(schedule)

                try:
                    backup_name = _run_backup(db_path, dest_dir, schedule.max_backups)
                    schedule.last_run_at = now
                    schedule.last_status = f"ok: {backup_name}"
                    logger.info("Auto-backup created: %s in %s", backup_name, dest_dir)
                except Exception as e:
                    schedule.last_run_at = now
                    schedule.last_status = f"error: {e}"
                    logger.error("Auto-backup failed: %s", e)

                session.add(schedule)
                session.commit()
        except Exception:
            logger.exception("Scheduler loop error")


def start_scheduler() -> asyncio.Task:  # type: ignore[type-arg]
    """Create and return the background task.  Call from FastAPI startup."""
    return asyncio.get_event_loop().create_task(_scheduler_loop())
