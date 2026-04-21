"""Add backup_schedule table."""

import sqlite3

VERSION = 2


def up(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS backupschedule (
            id              INTEGER PRIMARY KEY,
            enabled         BOOLEAN NOT NULL DEFAULT 0,
            cron_expr       TEXT    NOT NULL DEFAULT '0 2 * * *',
            destination_dir TEXT    NOT NULL DEFAULT '',
            max_backups     INTEGER NOT NULL DEFAULT 7,
            last_run_at     TEXT,
            last_status     TEXT    NOT NULL DEFAULT ''
        )
        """
    )
