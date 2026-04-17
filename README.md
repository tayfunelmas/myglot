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
docker compose up --build

# 4. Open http://localhost:8000
```

## Development (without Docker)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

## Project Structure

```
backend/          Python FastAPI backend
  app/            Application code
    routes/       API endpoints
    providers/    Pluggable Translate/TTS/STT providers
    services/     Pure business logic
frontend/         Static HTML + JS + CSS
data/             SQLite DB + audio files (gitignored)
secrets/          Google credentials (gitignored)
docs/             Setup guides
```
