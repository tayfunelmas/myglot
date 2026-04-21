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

## Development (without Docker)

```bash
# One-time setup: creates venv, installs deps, copies .env
task dev:setup
source .venv/bin/activate

# Run with auto-reload
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
    routes/       API endpoints
    providers/    Pluggable Translate/TTS/STT providers
    services/     Pure business logic
    migrations/   Versioned DB migration scripts
frontend/         Static HTML + JS + CSS
data/             SQLite DB + audio files (gitignored)
secrets/          Google credentials (gitignored)
docs/             Setup guides
```

## Backup & Restore

- **Backup:** Go to Settings → Database Backup & Restore → **Download Backup**. This downloads a `.db` snapshot of the entire database.
- **Restore:** Select a `.db` backup file and click **Restore from Backup**. The current database is replaced (a safety copy is kept in `data/`). The page reloads automatically.
