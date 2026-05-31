"""Add generatedtext table for generated learning texts."""

import sqlite3

VERSION = 5


def up(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS generatedtext (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            title          TEXT    NOT NULL,
            body           TEXT    NOT NULL,
            vocabulary_md  TEXT    NOT NULL DEFAULT '',
            source_lang    TEXT    NOT NULL,
            target_lang    TEXT    NOT NULL,
            audio_path     TEXT,
            audio_voice    TEXT,
            audio_provider TEXT,
            created_at     TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at     TEXT    NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
