# MyGlot

A personal language learning web app. Accumulate your most-used words, phrases, and sentences, get translations and audio, and practice speaking.

See [SPEC.md](SPEC.md) for full specification and design.

## Quick Start (Docker)

```bash
# 1. Copy and edit config
cp .env.example .env
# Edit .env — set GOOGLE_APPLICATION_CREDENTIALS and provider settings

# 2. Place your Google Cloud service account key
mkdir -p secrets
# Copy your key to secrets/gcp.json (see docs/GOOGLE_CLOUD_SETUP.md)

# 3. Build and run
task build
task up

# 4. Open http://localhost:8000
```

## Usage notes

- To edit an item (or regenerate its audio), click the **Edit** (pencil) button in the Home list to open the edit dialog.
- The **Practice** tab hides target text by default (blurred); click **Reveal** to show.
- Category filters on both Home and Practice tabs are sticky (saved to `localStorage`).
- **Backup/Restore** is in Settings → Database Backup & Restore.
- **Automatic backups** can be configured in Settings with a cron expression.
- **Export to CSV** is in Settings → Export Data. Downloads all items (source text, translation, category) sorted by category and order — ready for Excel or Google Sheets.
- **Provider selection** is per-capability (translate, TTS, STT). Currently `google`, `fake`, and `ollama` (translate only) are implemented. Set via `.env` (see SPEC §8.3).
- **Ollama provider** uses a local Ollama server for translation. It also returns a word-by-word explanation rendered below the translation form. Set `MYGLOT_TRANSLATE_PROVIDER=ollama` and optionally configure `MYGLOT_OLLAMA_BASE_URL` and `MYGLOT_OLLAMA_MODEL` in `.env`. See [docs/OLLAMA_SETUP.md](docs/OLLAMA_SETUP.md) for full setup instructions.

## Development (without Docker)

```bash
# One-time setup: creates venv, installs deps, copies .env
task dev:setup
source .venv/bin/activate

# Run with auto-reload (runs from backend/ dir, loads ../.env)
task dev
```

## Tasks

This project uses [Task](https://taskfile.dev/) as a task runner. Run `task --list` to see all available tasks.

| Task | Description |
|---|---|
| `task dev:setup` | Create venv, install all deps, and init `.env` |
| `task setup` | Install dev + lint dependencies (no venv) |
| `task dev` | Run backend locally with auto-reload |
| `task build` | Build Docker image |
| `task up` | Start application via docker compose (detached) |
| `task down` | Stop application |
| `task restart` | Rebuild and restart |
| `task logs` | Tail application logs |
| `task lint` | Run all lint and type checks (backend + frontend) |
| `task lint:backend` | Ruff linter + mypy type checker |
| `task lint:frontend` | Biome linter for JS/HTML/CSS |
| `task format` | Auto-format all code (ruff + Biome) |
| `task check` | CI-friendly: format check + lint (no writes) |
| `task test` | Run backend tests with pytest |

## Project Structure

```
backend/          Python FastAPI backend
  app/            Application code
    main.py       FastAPI app, startup, static file mount
    config.py     Environment config (reads .env)
    db.py         SQLModel engine, session, init_db()
    models.py     SQLModel tables: Category, Item, Settings, BackupSchedule
    schemas.py    Pydantic DTOs for API request/response
    errors.py     Uniform error classes (AppError, NotFoundError, etc.)
    migrate.py    Versioned migration runner
    scheduler.py  Background task for automatic backups (croniter)
    routes/       API endpoints
      health.py   /health, /health/providers, /backup, /restore, /backup-schedule
      items.py    /items CRUD, /items/reorder, /translate, /translate-back, /tts/preview
      categories.py  /categories CRUD
      settings.py    /settings GET/PUT
      voices.py      /voices (list TTS voices)
    providers/    Pluggable Translate/TTS/STT providers
      base.py     Abstract interfaces (ABC) + DTOs
      registry.py Factory functions with @lru_cache
      google/     Google Cloud implementations (Translate v2, TTS, STT)
      fake/       Stubs for offline dev/testing
      ollama/     Local Ollama LLM translation (with word-by-word explanation)
    services/     Pure business logic
      similarity.py  Scoring + word diff
      audio_store.py File paths, save, delete
    migrations/   Versioned DB migration scripts
      001_add_sort_order.py
      002_add_backup_schedule.py
frontend/         Static HTML + JS + CSS (no build step)
  index.html      Shell with tabs: Home | Practice | Settings
  styles.css      All styling
  js/             ES modules
    api.js        Fetch wrappers for all API endpoints
    app.js        Tab switching, init
    home.js       Add items, list, edit modal, drag-to-reorder
    practice.js   Play, record, score, reveal/hide
    settings.js   Language config, voice, categories, backup/restore
    recorder.js   MediaRecorder wrapper
    util.js       Helpers: debounce, escapeHtml, renderDiff, scoreClass
data/             SQLite DB + audio files (gitignored)
secrets/          Google credentials (gitignored)
docs/             Setup guides
```

## Backup & Restore

- **Backup:** Go to Settings → Database Backup & Restore → **Download Backup**. This downloads a `.db` snapshot of the entire database.
- **Restore:** Select a `.db` backup file and click **Restore from Backup**. The current database is replaced (a safety copy `myglot_pre_restore_*.db` is kept in `data/`). The page reloads automatically.
- **Automatic backups:** Enable in Settings → Automatic Backups. Configure a cron expression, destination directory, and max backups to retain. A background task checks every 60 seconds.

## API Overview

All endpoints are under `/api`. See [SPEC.md §7](SPEC.md) for the full API table. Key endpoints:

| Endpoint | Description |
|---|---|
| `GET /api/health` | Basic health check |
| `GET /api/health/providers` | Per-capability provider status |
| `GET/PUT /api/settings` | Language and voice configuration |
| `GET /api/voices?lang=` | List TTS voices for a language |
| `GET/POST /api/categories` | Category CRUD |
| `GET/POST /api/items` | Item CRUD (POST creates with translate + TTS) |
| `POST /api/items/reorder` | Reorder items by drag-and-drop |
| `POST /api/translate` | Translate source → target (no persistence) |
| `POST /api/translate-back` | Translate target → source (no persistence) |
| `POST /api/tts/preview` | Generate audio preview (no persistence) |
| `POST /api/items/{id}/practice` | Record + STT + score |
| `GET /api/backup` | Download DB snapshot |
| `POST /api/restore` | Restore from backup file |
