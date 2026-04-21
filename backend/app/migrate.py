"""Migration runner — discovers and applies versioned migration scripts."""

from __future__ import annotations

import importlib
import pkgutil
import sqlite3
from pathlib import Path

from . import migrations as _migrations_pkg


def _ensure_migration_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS _migration (
            version  INTEGER PRIMARY KEY,
            name     TEXT    NOT NULL,
            applied  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()


def _applied_versions(conn: sqlite3.Connection) -> set[int]:
    rows = conn.execute("SELECT version FROM _migration").fetchall()
    return {r[0] for r in rows}


def _discover_migrations() -> list[tuple[int, str, object]]:
    """Return sorted list of (version, module_name, module)."""
    results: list[tuple[int, str, object]] = []
    pkg_path = Path(_migrations_pkg.__file__).parent
    for _finder, name, _ispkg in pkgutil.iter_modules([str(pkg_path)]):
        if name.startswith("_"):
            continue
        mod = importlib.import_module(f"app.migrations.{name}")
        version = getattr(mod, "VERSION", None)
        if version is None:
            raise RuntimeError(
                f"Migration module app.migrations.{name} is missing a VERSION attribute"
            )
        results.append((version, name, mod))
    results.sort(key=lambda t: t[0])
    return results


def run_migrations(db_path: str) -> list[int]:
    """Apply all pending migrations.  Returns list of newly applied versions."""
    conn = sqlite3.connect(db_path)
    try:
        _ensure_migration_table(conn)
        applied = _applied_versions(conn)
        newly_applied: list[int] = []
        for version, name, mod in _discover_migrations():
            if version in applied:
                continue
            mod.up(conn)  # type: ignore[attr-defined]
            conn.execute(
                "INSERT INTO _migration (version, name) VALUES (?, ?)",
                (version, name),
            )
            conn.commit()
            newly_applied.append(version)
        return newly_applied
    finally:
        conn.close()
