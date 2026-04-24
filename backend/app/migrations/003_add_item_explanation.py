"""Add explanation column to item table."""

import sqlite3

VERSION = 3


def up(conn: sqlite3.Connection) -> None:
    conn.execute("ALTER TABLE item ADD COLUMN explanation TEXT")
