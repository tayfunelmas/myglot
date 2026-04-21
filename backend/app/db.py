from __future__ import annotations

from sqlmodel import Session, SQLModel, create_engine

from .config import get_config

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        cfg = get_config()
        db_path = cfg.data_dir / "myglot.db"
        _engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,
            connect_args={"check_same_thread": False},
        )
    return _engine


def init_db() -> None:
    from . import models  # noqa: F401 — ensure models registered
    from .migrate import run_migrations

    engine = get_engine()
    SQLModel.metadata.create_all(engine)

    db_path = str(get_config().data_dir / "myglot.db")
    applied = run_migrations(db_path)
    if applied:
        import logging

        logging.getLogger(__name__).info("Applied migrations: %s", applied)


def get_session():
    with Session(get_engine()) as session:
        yield session
