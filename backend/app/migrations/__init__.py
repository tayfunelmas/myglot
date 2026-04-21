"""
Versioned database migration system.

Each migration is a Python module in this package with a numeric prefix
(e.g. ``001_add_sort_order.py``).  Every module must expose:

- ``VERSION: int``  — unique, ascending integer (matches the file prefix).
- ``def up(conn: sqlite3.Connection) -> None`` — apply the migration.

Migrations run in order.  A ``_migration`` table in SQLite tracks which
versions have already been applied so each migration runs at most once.
"""
