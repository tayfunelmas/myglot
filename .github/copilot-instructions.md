# MyGlot — Copilot Instructions

This is the MyGlot project — a personal language learning web app.

## Required Context

Before making any changes or answering questions about this project, **always read these files first**:

1. **[SPEC.md](../SPEC.md)** — Full specification and design document. Contains architecture, data model, API definitions, provider abstraction, configuration, and all design decisions.
2. **[README.md](../README.md)** — Quick start, task runner commands, and project structure overview.

## Key Rules

- Any change (or findings you discover) to design, architecture, or code organization **must** update `SPEC.md`.
- Any change (or findings you discover) that affects how the user runs or interacts with the app **must** update `README.md`.
- Database schema changes **must** use the versioned migration system in `backend/app/migrations/` (see SPEC §6.2). Never modify an existing released migration.
- All code must pass `task check` (ruff format + ruff lint + mypy + Biome) before being considered complete.

## Tech Stack

- **Backend:** Python 3.11, FastAPI, SQLModel, SQLite (`data/myglot.db`)
- **Frontend:** Vanilla HTML + JS ES modules + CSS (no build step)
- **Providers:** Pluggable Google Cloud / Fake providers for Translate, TTS, STT
- **Task runner:** [Taskfile.yml](../Taskfile.yml) — use `task dev` for local dev, `task check` for CI checks
- **Lint:** ruff + mypy (Python), Biome (JS/HTML/CSS)
- **Docker:** `docker-compose.yml` with bind mounts for `./data` and `./secrets`

## Project Layout

```
backend/app/          FastAPI application
  routes/             API endpoints
  providers/          Pluggable Translate/TTS/STT
  services/           Pure business logic
  migrations/         Versioned DB migrations
frontend/             Static HTML + JS + CSS
data/                 SQLite DB + audio (gitignored)
secrets/              Google credentials (gitignored)
```
