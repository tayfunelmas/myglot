"""Add sort_order column to the item table."""

import sqlite3

VERSION = 1


def up(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(item)").fetchall()}
    if "sort_order" not in cols:
        conn.execute("ALTER TABLE item ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0")
    conn.execute("CREATE INDEX IF NOT EXISTS ix_item_sort_order ON item (sort_order)")
