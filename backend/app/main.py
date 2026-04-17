from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .db import init_db
from .config import get_config
from .routes import health, settings, voices, categories, items

app = FastAPI(title="MyGlot", version="0.1.0")

# Register API routes
app.include_router(health.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(voices.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(items.router, prefix="/api")


@app.on_event("startup")
def startup():
    cfg = get_config()
    cfg.ensure_dirs()
    init_db()
    # Seed settings row
    from .db import get_engine
    from sqlmodel import Session
    from .models import Settings
    with Session(get_engine()) as session:
        if session.get(Settings, 1) is None:
            session.add(Settings(
                id=1,
                source_lang=cfg.default_source_lang,
                target_lang=cfg.default_target_lang,
                tts_voice=cfg.default_tts_voice,
            ))
            session.commit()


# Serve frontend static files — must be AFTER API routes
# Resolve frontend path: works both in Docker (/app/frontend) and local dev
_frontend_candidates = [
    Path(__file__).resolve().parent.parent.parent / "frontend",  # local dev: backend/app -> myglot/frontend
    Path("/app/frontend"),  # Docker
]
for _fe_path in _frontend_candidates:
    if _fe_path.is_dir():
        app.mount("/", StaticFiles(directory=str(_fe_path), html=True), name="frontend")
        break
