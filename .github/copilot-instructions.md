# MyGlot — Copilot Instructions

This is the MyGlot project — a personal language learning web app.

## Required Context

Before making any changes or answering questions about this project, **always read these files first**:

1. **[SPEC.md](../SPEC.md)** — Full specification and design document. Contains architecture, data model, API definitions, provider abstraction, configuration, and all design decisions.
2. **[README.md](../README.md)** — Quick start, task runner commands, and project structure overview.

## Key Rules

- Any change (or findings you discover) to design, architecture, or code organization **must** update `SPEC.md`.
- Any change (or findings you discover) that affects how the user runs or interacts with the app **must** update `README.md`.
- Database schema changes **must** use the versioned migration system in `backend/app/migrations/` (see SPEC §6.2). Never modify an existing released migration. Always update `models.py` to match.
- All code must pass `task check` (ruff format + ruff lint + mypy + Biome) before being considered complete.
- When adding new API endpoints, update the API table in SPEC §7.
- When adding new files, update the file layout in SPEC §16.15.

## Tech Stack

- **Backend:** Python 3.11, FastAPI, SQLModel, SQLite (`data/myglot.db`), croniter (for backup scheduling)
- **Frontend:** Vanilla HTML + JS ES modules + CSS (no build step, no framework)
- **Providers:** Pluggable Google Cloud / Fake providers for Translate, TTS, STT (see SPEC §8)
- **Google Translate:** Uses v2 API (`google.cloud.translate_v2`), not v3
- **Task runner:** [Taskfile.yml](../Taskfile.yml) — use `task dev` for local dev, `task check` for CI checks
- **Lint:** ruff + mypy (Python), Biome (JS/HTML/CSS)
- **Docker:** `docker-compose.yml` with bind mounts for `./data` and `./secrets`

## Project Layout

```
backend/app/          FastAPI application
  main.py             App + startup + static file mount
  config.py           Env config (reads .env)
  db.py               SQLModel engine, session
  models.py           SQLModel tables: Category, Item, Settings, BackupSchedule
  schemas.py          Pydantic DTOs
  errors.py           Uniform error classes
  migrate.py          Versioned migration runner
  scheduler.py        Background backup task (croniter)
  routes/             API endpoints
    health.py         Also contains backup, restore, backup-schedule routes
    items.py          Also contains translate, translate-back, tts/preview routes
    categories.py     Category CRUD
    settings.py       Settings GET/PUT
    voices.py         Voice listing
  providers/          Pluggable Translate/TTS/STT (ABC-based)
    base.py           Abstract interfaces + DTOs
    registry.py       Factory functions (@lru_cache), if/elif dispatch
    google/           Google Cloud implementations
    fake/             Stubs for offline dev/testing
    ollama/           Local Ollama LLM translation
  services/           Pure business logic
    similarity.py     Scoring + word diff
    audio_store.py    File paths, save, delete
  migrations/         Versioned DB migrations (raw SQL, no app imports)
frontend/             Static HTML + JS + CSS
  js/                 ES modules: api.js, app.js, home.js, practice.js, settings.js, recorder.js, util.js
data/                 SQLite DB + audio (gitignored)
secrets/              Google credentials (gitignored)
```

## Important Conventions

- **Error handling:** Use error classes from `errors.py` (AppError, NotFoundError, ValidationError, ProviderAPIError, ProviderNotConfiguredError, AudioMissingError). Error codes: `NOT_FOUND`, `VALIDATION_ERROR`, `PROVIDER_API_ERROR`, `PROVIDER_NOT_CONFIGURED`, `AUDIO_MISSING`.
- **Provider abstraction:** Routes depend on abstract interfaces from `providers/base.py`. New providers go in `providers/<vendor>/` and are registered in `registry.py`. Providers must raise `ProviderError` on failure.
- **Frontend patterns:** All API calls go through `api.js` wrappers. Category filters use `localStorage` for persistence. The home.js handles the add-item form, item list, edit modal, and drag-to-reorder. The practice.js handles play, record, score display.
- **`task dev`** runs from `backend/` dir (Taskfile `dir` key) and loads `../.env` via `dotenv` directive.
- **Tests** directory (`backend/tests/`) does not yet exist but `task test` is configured to run `pytest -v`.
