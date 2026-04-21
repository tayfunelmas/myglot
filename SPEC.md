# MyGlot — Specification & Design

A personal, single-user web app for learning a target language by accumulating and practicing your own most-used words, phrases, and sentences.

> **Status:** Living document. Updated as code evolves. Reflects the current implementation.

> **Maintenance rules:**
> - Any change to design, architecture, or code organization **must** update this SPEC file to stay in sync.
> - Any change that affects how the user runs or interacts with the app **must** update the README file.

---

## 1. Goals & Non-Goals

### 1.1 Goals
- Let the user maintain a personal corpus of **items** (word / phrase / sentence) in their **source language**.
- Use **Google Translate** to translate each item to the **target language**.
- Use **Google Text-to-Speech (TTS)** to generate audio of the target-language text.
- Persist source text, target text, and audio so they don't need to be regenerated.
- Allow **editing the target text** and **regenerating audio** on demand.
- Provide a **practice view** listing all items with play, record, and compare features.
- Use **Google Speech-to-Text (STT)** to transcribe the user's spoken attempt and **compare** it to the stored target text, giving a similarity score.
- Allow **downloading** the audio file for any item.
- Let the user organize items into **categories** (e.g. "Greetings", "At the restaurant") and filter by category when practicing.

### 1.2 Non-Goals (for v1)
- Multi-user / auth / cloud sync.
- Spaced-repetition scheduling (SRS), gamification, streaks.
- Mobile-native app (web only; mobile browser should work).
- Offline mode.
- Multiple target languages per item (one source lang + one target lang configured globally; can be changed later).
- Grammar analysis, conjugation drills.

### 1.3 Assumptions
- Single local user on `localhost` (or a personal server).
- User has a **Google Cloud project** with Translate, TTS, and STT APIs enabled and a service-account JSON key available.
- Internet access is available for API calls; existing items (with cached audio) can be practiced offline.

---

## 2. Primary User Flows

### 2.1 Configure languages
1. User opens Settings.
2. Sets **source language** (e.g., `en`) and **target language** (e.g., `de`).
3. Optionally picks a **TTS voice** for the target language (dropdown populated from Google TTS).
4. Saves. Settings are persisted.

### 2.2 Add a new item (3-step workflow)
1. User types source text into an input on the Home page.
2. Optionally selects a **category** from a dropdown (or types a new one to create it inline).
3. Clicks **Translate** → backend calls Translate API, result fills an editable translation textarea. *Alternatively*, the user can type the translation directly and skip this step entirely.
4. User may edit the translation text freely.
5. Clicks **Generate Audio** → backend runs TTS on the (edited) translation, returns an audio preview that plays inline. Only enabled when translation text is present.
6. Clicks **Add Item** → backend creates the DB row. If `target_text` is provided in the request, translation is skipped server-side. TTS runs server-side to store the MP3 on disk.
7. UI clears the form and shows the new item at the top of the list.

### 2.2b Add a new item — reverse flow ("Translate back")
1. User types a **target-language** sentence they heard into the translation textarea on the Home page.
2. Clicks **Translate back** → backend translates from target lang to source lang; the result fills the source text field.
3. User reviews the back-translation to confirm understanding.
4. From here, the normal add-item flow continues: user can edit either field, generate audio, and click **Add Item**.

### 2.3 Edit translation & regenerate audio
1. In an item's detail/edit view, user edits `target_text`.
2. Saves → DB row updated, `audio_stale = true`.
3. User clicks **Regenerate audio** → backend re-runs TTS, replaces the MP3 file, sets `audio_stale = false`.

### 2.4 Reorder items
1. On the Home tab, items are displayed in a **table** with drag handles on the left.
2. User drags an item's handle (☰) to reorder it above or below other items.
3. The new order is persisted immediately via `POST /api/items/reorder`.
4. On next visit, items appear in the saved order.

### 2.5 Practice
1. User opens **Practice**.
2. Optionally selects one or more **categories** to filter (multi-select; selecting none shows all). The selection is **sticky** — persisted in `localStorage` and restored on next visit.
3. Sees a **table** of the filtered items:
   - Source text.
   - Target text (**hidden by default**; press a **Reveal** button to show it).
   - **▶ Play** button (plays stored MP3).
   - **🎤 Record** button (records mic audio in browser, sends to backend).
   - Backend runs STT → returns transcript + similarity score (ephemeral — not persisted).
   - UI shows: your transcript, the expected target text, a score (0–100), and a diff highlighting mismatched words. The score is displayed until the user navigates away; it is not saved.
3. User can **Download audio** (MP3) per item.

### 2.6 Backup & Restore
1. User opens **Settings** and scrolls to **Database Backup & Restore**.
2. **Download Backup** — downloads a consistent `.db` snapshot of the entire database via `GET /api/backup`.
3. **Restore from Backup** — user selects a `.db` file and clicks **Restore from Backup**. The server validates the file, creates a safety copy of the current DB, then swaps it in. The page reloads automatically.

### 2.6b Configure automatic backups
1. User opens **Settings** and scrolls to **Automatic Backups**.
2. Enables the checkbox, enters a **cron expression** (e.g. `0 2 * * *` for daily at 2 AM), an optional **destination directory** (absolute path; empty uses `<data_dir>/backups`), and the **max backups** to retain.
3. Clicks **Save Schedule**. The backend validates the cron expression and persists the config.
4. A background task runs every 60 seconds, checks whether a backup is due, and creates a timestamped SQLite snapshot. Old backups beyond the max are automatically deleted.
5. The last run time and status are displayed in the UI.

### 2.7 Manage categories
- User can create, rename, and delete categories from the **Home** page or a dedicated section.
- Deleting a category does **not** delete its items — they become uncategorized (`category_id = NULL`).
- Items can be moved between categories (change category via edit).

### 2.8 Manage items
- Search / filter by source or target text, **and/or by multiple categories** (multi-select filter, sticky across sessions via `localStorage`).
- Delete an item (removes DB row + audio file).
- Change an item's category.

---

## 3. Functional Requirements

| ID | Requirement |
|----|-------------|
| F1 | CRUD for items: create, list, get, update (target text and category; source is immutable after create to keep history simple), delete. |
| F1b | CRUD for categories: create, list, rename, delete (soft — items become uncategorized). |
| F2 | Standalone translate endpoint (`POST /api/translate`): given source text → target text (no persistence). Used by the UI before adding an item, or skipped if the user types the translation manually. |
| F2b | Reverse translate endpoint (`POST /api/translate-back`): given target text → source text (no persistence). Used when the user hears a target-language sentence and wants to confirm its meaning before adding. |
| F3 | TTS preview endpoint (`POST /api/tts/preview`): given text → returns audio bytes for inline playback. Stored audio is generated separately when the item is created. |
| F4 | STT endpoint: accepts uploaded audio blob + expected target lang → returns transcript. |
| F5 | Similarity scoring: server computes normalized similarity between transcript and stored target text (see §6.4). |
| F6 | Settings: persist source lang, target lang, voice. |
| F7 | Audio download endpoint serving the stored MP3 with correct `Content-Type` and `Content-Disposition`. |
| F8 | Regenerate audio endpoint for an item (always available, not only when stale). |
| F9 | List voices endpoint (proxies Google TTS `ListVoices`, filtered by target lang). |
| F10 | Reorder items: `POST /api/items/reorder` accepts an ordered list of item IDs and persists the sort order. |
| F11 | Multi-category filter: `GET /api/items` accepts `category_ids` (comma-separated) for filtering by multiple categories. |
| F12 | Database backup: `GET /api/backup` downloads a consistent SQLite snapshot. |
| F13 | Database restore: `POST /api/restore` accepts a `.db` file upload, validates it, and replaces the current database. |
| F14 | Automatic backup schedule: configurable via `GET/PUT /api/backup-schedule`. Background task checks cron expression every 60s and creates a consistent SQLite snapshot in the configured destination, rotating old backups. |

## 4. Non-Functional Requirements
- **Simplicity:** minimal dependencies; easy to run with one command.
- **Portability:** works on macOS/Linux; Python 3.11+.
- **Cost safety:** no auto-retranslation loops; TTS/Translate only called on explicit user action.
- **Privacy:** all data local; only text/audio sent to Google APIs on demand.
- **Latency:** add-item round-trip < ~3s typical for a short sentence.

---

## 5. Architecture Overview

```
┌─────────────────────────┐      HTTP/JSON      ┌──────────────────────────┐
│   Browser (frontend)    │  ────────────────▶  │   Python backend (API)   │
│   Vanilla HTML + JS     │                     │   FastAPI + Uvicorn      │
│   (+ a little CSS)      │  ◀────────────────  │                          │
└─────────────────────────┘                     │  - Routes                │
        │  MediaRecorder (mic)                  │  - Services              │
        │  <audio> playback                     │  - SQLite via SQLModel   │
        ▼                                        │  - Audio files on disk   │
                                                 └──────────────┬───────────┘
                                                                │
                                                                ▼
                                                ┌──────────────────────────┐
                                                │  Google Cloud APIs       │
                                                │  - Translate v3          │
                                                │  - Text-to-Speech        │
                                                │  - Speech-to-Text        │
                                                └──────────────────────────┘
```

### 5.1 Tech choices
- **Backend:** Python 3.11, **FastAPI**, Uvicorn, **SQLModel** (SQLAlchemy + Pydantic), SQLite, **croniter** (for cron expression parsing in the automatic backup scheduler).
- **External AI providers:** pluggable behind abstract interfaces (see §8.1). Default stack is **Google Cloud** (Translate v2, Text-to-Speech, Speech-to-Text). A `fake` provider set is included for offline dev/testing. Additional providers (OpenAI, Deepgram, …) can be added via config without code changes in routes (see §8.3).
- **Frontend:** Plain HTML + vanilla JS ES modules. No build step. One small CSS file. (Could swap to Alpine.js or HTMX later; kept vanilla to stay simple.)
- **DB:** SQLite file at `data/myglot.db`.
- **Audio storage:** `data/audio/<uuid>.mp3`.
- **Config:** `.env` file (python-dotenv) with `GOOGLE_APPLICATION_CREDENTIALS` path and optional defaults.

### 5.2 Why these choices
- FastAPI: auto docs, simple async, type-safe.
- SQLModel + SQLite: zero setup, single file, sufficient for a personal corpus up to ~tens of thousands of rows.
- Vanilla JS: no toolchain, matches the "simple frontend" requirement.

---

## 6. Data Model

### 6.1 SQLite schema (via SQLModel)

**Table: `category`**

| Column       | Type        | Notes |
|--------------|-------------|-------|
| `id`         | INTEGER PK  | autoincrement |
| `name`       | TEXT        | NOT NULL, UNIQUE, e.g. "Greetings" |
| `created_at` | DATETIME    | UTC |

**Table: `item`**

| Column         | Type        | Notes |
|----------------|-------------|-------|
| `id`           | INTEGER PK  | autoincrement |
| `category_id`  | INTEGER FK  | → `category.id`, nullable (uncategorized), ON DELETE SET NULL |
| `source_lang`  | TEXT        | BCP-47, e.g. `en` |
| `target_lang`  | TEXT        | BCP-47, e.g. `de` |
| `source_text`  | TEXT        | NOT NULL, user input |
| `target_text`  | TEXT        | NOT NULL, translated/edited |
| `audio_path`   | TEXT        | relative path under `data/audio/`, nullable if generation failed |
| `audio_voice`  | TEXT        | voice name used (e.g. `de-DE-Wavenet-B`) |
| `audio_provider`| TEXT       | which TTS provider produced the audio |
| `sort_order`   | INTEGER     | display order (lower = higher in list), default 0 |
| `audio_stale`  | BOOLEAN     | true if target_text changed after last TTS |
| `created_at`   | DATETIME    | UTC |
| `updated_at`   | DATETIME    | UTC |

**Table: `settings`** (single row, `id=1`)

| Column        | Type   | Notes |
|---------------|--------|-------|
| `id`          | INT PK | always 1 |
| `source_lang` | TEXT   | default `en` |
| `target_lang` | TEXT   | default `de` |
| `tts_voice`   | TEXT   | default null → server picks default for `target_lang` |

**Table: `backupschedule`** (single row, `id=1`)

| Column           | Type        | Notes |
|------------------|-------------|-------|
| `id`             | INT PK      | always 1 |
| `enabled`        | BOOLEAN     | default false |
| `cron_expr`      | TEXT        | cron expression, default `0 2 * * *` (daily 2 AM) |
| `destination_dir`| TEXT        | absolute path; empty = `<data_dir>/backups` |
| `max_backups`    | INTEGER     | rotate: keep last N backups, default 7 |
| `last_run_at`    | DATETIME    | UTC, nullable |
| `last_status`    | TEXT        | `ok: <filename>` or `error: <message>` |

### 6.2 Database Migrations

The schema evolves over time without losing user data. Migrations live in `backend/app/migrations/` as numbered Python modules.

#### How it works

1. A `_migration` table in SQLite tracks which versions have been applied.
2. On startup, `init_db()` calls `SQLModel.metadata.create_all()` (creates any new tables) and then `run_migrations()` which discovers all `backend/app/migrations/NNN_*.py` files, skips already-applied versions, and runs the rest in order.
3. Each migration module exposes:
   - `VERSION: int` — unique ascending integer matching the file prefix.
   - `def up(conn: sqlite3.Connection) -> None` — applies the change.
4. Migrations are idempotent where possible (e.g. check column existence before `ALTER TABLE`).

#### Adding a new migration

1. Create `backend/app/migrations/<next_number>_<description>.py`.
2. Define `VERSION = <next_number>` and `def up(conn):`.
3. Update `models.py` to match (SQLModel `create_all` handles new tables; migrations handle altering existing tables).
4. Update the data model tables in this SPEC (§6.1) to reflect the new columns/tables.
5. Test: delete `data/myglot.db`, restart — fresh DB gets the column via `create_all` and the migration is recorded. Or keep the old DB — the migration adds the column.

#### Rules

- Never modify or renumber an existing migration that has been released.
- Migrations must not import application code (models, services) — use raw SQL only. This avoids breakage when models change in later versions.
- Each migration runs inside its own transaction (committed after success).
- The `_migration` table schema:

| Column    | Type        | Notes |
|-----------|-------------|-------|
| `version` | INTEGER PK  | migration version number |
| `name`    | TEXT        | module name (e.g. `001_add_sort_order`) |
| `applied` | TEXT        | UTC timestamp of when it was applied |

### 6.3 Filesystem layout
```
data/
  myglot.db
  audio/
    <item-uuid>.mp3     # generated TTS output
```

Audio filename uses a UUID (not the item id) so regeneration can atomically write a new file, then update the DB, then delete the old file.

### 6.4 Language codes
- Translate API uses ISO-639-1 (e.g., `en`, `de`, `tr`).
- TTS/STT use BCP-47 (e.g., `en-US`, `de-DE`, `tr-TR`).
- Settings stores **both** fields per lang, or a small lookup table maps `en → en-US`. For simplicity, store the BCP-47 form and derive the 2-letter code for Translate by splitting on `-`.

### 6.5 Similarity scoring
- Normalize both strings: lowercase, strip punctuation, collapse whitespace, Unicode NFC.
- Compute two numbers:
  - **Char-level ratio:** `difflib.SequenceMatcher(None, a, b).ratio()` → handles minor typos/accents.
  - **Word-level F1** over tokenized words.
- Final score = `round(100 * max(char_ratio, word_f1))`.
- Also return a word-diff (`[{word, status: "match"|"missing"|"extra"|"wrong"}]`) for UI highlighting.

---

## 7. REST API

Base path: `/api`. All JSON unless noted.

| Method | Path                         | Body / Query                                                | Response |
|--------|------------------------------|-------------------------------------------------------------|----------|
| GET    | `/api/health`                | —                                                           | `{status:"ok"}` |
| GET    | `/api/settings`              | —                                                           | Settings |
| PUT    | `/api/settings`              | `{source_lang, target_lang, tts_voice?}`                    | Settings |
| GET    | `/api/voices?lang=de-DE`     | —                                                           | `[{name, gender, natural_sample_rate}]` |
| GET    | `/api/categories`            | —                                                           | `[{id, name, item_count}]` |
| POST   | `/api/categories`            | `{name}`                                                    | `201` + `Category` |
| PATCH  | `/api/categories/{id}`       | `{name}`                                                    | `Category` |
| DELETE | `/api/categories/{id}`       | —                                                           | `204` (items become uncategorized) |
| GET    | `/api/items?q=&category_id=&category_ids=&limit=&offset=` | `category_ids`: comma-separated IDs for multi-filter | `{items:[Item], total}` |
| POST   | `/api/items/reorder`         | `{item_ids:[int]}`                                          | `204` (no body) |
| GET    | `/api/backup`                | —                                                           | `application/x-sqlite3` (attachment) |
| POST   | `/api/restore`               | multipart: `file` (.db)                                     | `{status:"ok", message:"..."}` |
| GET    | `/api/backup-schedule`       | —                                                           | `BackupSchedule` |
| PUT    | `/api/backup-schedule`       | `{enabled?, cron_expr?, destination_dir?, max_backups?}`    | `BackupSchedule` |
| POST   | `/api/translate`             | `{source_text}`                                             | `{target_text}` |
| POST   | `/api/translate-back`        | `{target_text}`                                             | `{source_text}` — reverse translation (target→source) |
| POST   | `/api/tts/preview`           | `{text}`                                                    | `audio/mpeg` (inline binary) |
| POST   | `/api/items`                 | `{source_text, target_text?, category_id?, category_name?}` — if `target_text` provided, translation is skipped | `201` + `Item` (with `target_text`, `audio_url`) |
| GET    | `/api/items/{id}`            | —                                                           | `Item` |
| PATCH  | `/api/items/{id}`            | `{target_text?, category_id?}`                              | `Item` (sets `audio_stale=true` if `target_text` changed) |
| POST   | `/api/items/{id}/regenerate-audio` | —                                                     | `Item` (fresh `audio_url`, `audio_stale=false`) |
| DELETE | `/api/items/{id}`            | —                                                           | `204` |
| GET    | `/api/items/{id}/audio`      | —                                                           | `audio/mpeg` (inline) |
| GET    | `/api/items/{id}/audio?download=1` | —                                                     | `audio/mpeg` (attachment) |
| POST   | `/api/items/{id}/practice`   | multipart: `audio` (webm/ogg/wav)                           | `{transcript, score, diff:[...]}` |

### Item DTO
```json
{
  "id": 42,
  "source_lang": "en",
  "target_lang": "de-DE",
  "source_text": "Good morning",
  "target_text": "Guten Morgen",
  "audio_url": "/api/items/42/audio",
  "audio_voice": "de-DE-Wavenet-B",
  "audio_provider": "google",
  "audio_stale": false,
  "category": {"id": 3, "name": "Greetings"},
  "created_at": "2026-04-17T10:00:00Z",
  "updated_at": "2026-04-17T10:00:02Z"
}
```

### Errors
Uniform envelope:
```json
{ "error": { "code": "GOOGLE_API_ERROR", "message": "..." } }
```
Common codes: `VALIDATION_ERROR`, `NOT_FOUND`, `PROVIDER_API_ERROR`, `PROVIDER_NOT_CONFIGURED`, `AUDIO_MISSING`.

---

## 8. Backend Module Layout

```
backend/
  app/
    main.py                 # FastAPI app + static mount for frontend
    config.py               # env + settings
    db.py                   # SQLModel engine, session
    migrate.py              # versioned migration runner
    models.py               # Item, Settings, Category, BackupSchedule
    schemas.py              # Pydantic DTOs
    errors.py               # Uniform error classes (AppError, NotFoundError, etc.)
    scheduler.py            # Background task: automatic backup runner (croniter)
    routes/
      items.py
      categories.py
      settings.py
      voices.py
      health.py             # includes /backup, /restore, /backup-schedule routes
    migrations/             # numbered migration scripts (see §6.2)
      __init__.py
      001_add_sort_order.py
      002_add_backup_schedule.py
    providers/              # pluggable external services (see §8.1)
      __init__.py
      base.py               # abstract interfaces (ABC) + DTOs
      registry.py           # factory functions get_translator(), get_tts(), get_stt() cached with @lru_cache
      google/
        translate.py         # Uses Google Translate v2 (not v3)
        tts.py
        stt.py
      fake/                 # in-memory stubs for tests / offline dev
        translate.py
        tts.py
        stt.py
    services/
      similarity.py         # scoring + diff (pure, no provider)
      audio_store.py        # paths, atomic replace, delete
  tests/                    # (not yet created)
  pyproject.toml
  requirements.txt
  Dockerfile
```

### 8.1 Provider abstraction

Translation, TTS, and STT are each defined as an **abstract interface** (Python `Protocol` / ABC). Route handlers depend only on these interfaces, resolved via FastAPI dependency injection. Concrete implementations live under `app/providers/<vendor>/` and are selected at startup from config.

```python
# app/providers/base.py
from abc import ABC, abstractmethod

class Translator(ABC):
    name: str
    @abstractmethod
    def translate(self, text: str, source_lang: str, target_lang: str) -> str: ...

class Voice(BaseModel):
    id: str                 # provider-specific voice id, opaque to the app
    display_name: str
    gender: Literal["male", "female", "neutral", "unknown"] = "unknown"
    lang: str               # BCP-47
    provider: str

class TTSResult(BaseModel):
    audio_bytes: bytes
    mime: str               # e.g. "audio/mpeg"
    voice_id: str           # what was actually used (after defaulting)

class TTS(ABC):
    name: str
    @abstractmethod
    def synthesize(self, text: str, lang: str, voice_id: str | None) -> TTSResult: ...
    @abstractmethod
    def list_voices(self, lang: str) -> list[Voice]: ...

class STTResult(BaseModel):
    transcript: str
    confidence: float | None = None

class STT(ABC):
    name: str
    # mime examples: "audio/webm;codecs=opus", "audio/wav"
    @abstractmethod
    def transcribe(self, audio_bytes: bytes, mime: str, lang: str) -> STTResult: ...

class ProviderError(Exception): ...        # wraps vendor SDK errors uniformly
class ProviderNotConfigured(ProviderError): ...
```

Rules for implementations:
- Each concrete class (`GoogleTranslator`, `GoogleTTS`, `GoogleSTT`, `FakeTranslator`, …) does all I/O internally — no globals (except a lazy-init module-level `_client` singleton per Google provider module, see §16.2).
- They must raise `ProviderError` (with a human message) on failure; never leak vendor-specific exception types to routes. Routes catch `ProviderError` and convert to `ProviderAPIError` (HTTP 503, code `PROVIDER_API_ERROR`).
- They must normalize language codes: accept BCP-47 (`de-DE`) and internally convert to whatever the vendor wants (e.g. Google Translate v2 uses `de`, Deepgram would use `de-DE`).
- **Google Translate:** uses the **v2** API (`google.cloud.translate_v2.Client`), not v3. The `google-cloud-translate` pip package includes both; v2 was chosen for simplicity.
- Voice IDs are treated as **opaque strings** by the app. `Voice.id` from one provider is not expected to work with another. When the user switches providers, the voice dropdown repopulates and the stored `tts_voice` is cleared if it's no longer valid.
- The filesystem audio layer (`audio_store`) is provider-agnostic; it just persists the `audio_bytes` returned by any TTS provider (extension inferred from `mime`).

### 8.2 Provider registry & factory

```python
# app/providers/registry.py (simplified)
_REGISTRY = {
    "translator": {
        "google":   lambda cfg: GoogleTranslator(),
        "fake":     lambda cfg: FakeTranslator(),
    },
    "tts": {
        "google":   lambda cfg: GoogleTTS(),
        "fake":     lambda cfg: FakeTTS(),
    },
    "stt": {
        "google":   lambda cfg: GoogleSTT(),
        "fake":     lambda cfg: FakeSTT(),
    },
}

def get_translator() -> Translator: ...   # @lru_cache
def get_tts() -> TTS: ...                 # @lru_cache
def get_stt() -> STT: ...                 # @lru_cache
```

> **Note:** OpenAI and Deepgram providers are not yet implemented. The registry uses if/elif dispatch rather than a dict. Adding a new provider means adding a new branch in the `_build_*` functions and the corresponding module under `app/providers/<vendor>/`.

FastAPI wires these as cached dependencies:
```python
@lru_cache
def get_translator() -> Translator: return build_translator(load_config())
# used in routes as:  translator: Translator = Depends(get_translator)
```

Swapping a provider = change env var + restart. Adding a new provider = add a new file under `app/providers/<vendor>/`, add a branch in `registry.py`'s `_build_*` functions; no route changes.

### 8.3 Selecting providers via config

Extend `.env` (see §10.2) with **per-capability** selectors so you can mix vendors (e.g., Google TTS + fake STT for offline dev):

```dotenv
# Currently implemented: google | fake
MYGLOT_TRANSLATE_PROVIDER=google
MYGLOT_TTS_PROVIDER=google
MYGLOT_STT_PROVIDER=google

# Vendor credentials — only set the ones your selected providers need.
GOOGLE_APPLICATION_CREDENTIALS=./secrets/gcp.json
# Planned (not yet implemented):
# OPENAI_API_KEY=
# DEEPGRAM_API_KEY=
```

Validation at startup: for each selected provider, the registry checks it is a known name (`google` or `fake`). Unknown names raise `ProviderNotConfigured`. For Google providers, the Google SDK reads credentials from `GOOGLE_APPLICATION_CREDENTIALS` automatically.

`GET /api/health/providers` returns per-capability status:
```json
{
  "translator": {"provider":"google","ok":true},
  "tts":        {"provider":"google","ok":true},
  "stt":        {"provider":"fake","ok":true}
}
```
Each capability reports `ok: false` with an `error` string if the provider cannot be instantiated.

### 8.4 Impact on the data model

- `item.audio_voice` already stores an opaque voice id — no schema change needed, but add `item.audio_provider TEXT` so we know which TTS vendor produced the stored MP3. Regenerate-audio will overwrite both fields.

### 8.5 Testing

- All route tests should use the `fake` providers (deterministic, zero network): `FakeTranslator` returns `f"[{target_lang}] {text}"`, `FakeTTS` returns a fixed minimal MP3 frame, `FakeSTT` returns a preset transcript (configurable via constructor).
- Contract tests per provider would live in `tests/test_providers_<vendor>.py`, marked with `@pytest.mark.network` and skipped by default.
- **Note:** The `backend/tests/` directory does not yet exist. Tests are planned but not implemented.

### Key service contracts (Python) — pure services

```python
# services/similarity.py
def score(expected: str, actual: str) -> ScoreResult:  # {score: float, diff: [...]}

# services/audio_store.py
def save(audio_bytes: bytes, mime: str) -> str:   # returns relative path
def delete(path: str) -> None: ...
```

---

## 9. Frontend Layout

```
frontend/
  index.html          # shell + tabs: Home | Practice | Settings
  styles.css
  js/
    api.js            # fetch wrappers
    home.js           # add + list items
    practice.js       # play/record/score
    settings.js       # languages + voice
    recorder.js       # MediaRecorder helper
    util.js           # debounce, diff render
```

Served by FastAPI as static files at `/` so everything is one origin (no CORS).

### UI pages
1. **Home** — input box + "Translate & Save" button; list of items below with edit + delete (regenerate audio lives in the edit modal).
2. **Practice** — same list but emphasizes play + record + score; a "hide target" toggle.
3. **Settings** — source lang, target lang (with BCP-47 examples), voice dropdown (populated via `/api/voices`).

### Mic recording
- `navigator.mediaDevices.getUserMedia({ audio: true })`.
- `MediaRecorder` → `audio/webm;codecs=opus` (widely supported).
- POST as multipart; backend passes to Google STT with `encoding=WEBM_OPUS` and `sample_rate_hertz=48000` (standard for opus/webm).

---

## 10. Configuration & Secrets

There are two distinct layers of configuration, kept intentionally separate:

| Layer | What it holds | Where it lives | How it's changed | When it's read |
|-------|---------------|----------------|------------------|----------------|
| **Environment / secrets** | Google credentials, data dir, host/port | `.env` file + process env | Manually edited by the user; requires server restart | At startup |
| **App settings** | Source lang, target lang, TTS voice | `settings` row in SQLite | Edited in the **Settings** page (UI) or via `PUT /api/settings`; takes effect immediately | On every relevant request |

This split keeps secrets out of the database and the UI, and keeps day-to-day preferences (which you'll change often) out of files you have to edit by hand.

### 10.1 One-time setup (Google Cloud)

> Full step-by-step walkthrough (Console + `gcloud` CLI, with verification and troubleshooting) lives in **[docs/GOOGLE_CLOUD_SETUP.md](docs/GOOGLE_CLOUD_SETUP.md)**. The summary below lists just the outcomes.

The user does this once, outside the app:

1. Create (or reuse) a Google Cloud project at <https://console.cloud.google.com>.
2. Enable these three APIs in that project:
   - **Cloud Translation API**
   - **Cloud Text-to-Speech API**
   - **Cloud Speech-to-Text API**
3. Create a **service account** (IAM & Admin → Service Accounts → Create).
   - Grant roles: `Cloud Translation API User`, `Cloud Speech Client` (covers TTS + STT). For a personal project, the broader `Editor` role also works but is not recommended.
4. Create a **JSON key** for that service account and download it.
5. Save the key into the project at `./secrets/gcp.json` (the folder is gitignored).
6. Make sure **billing** is enabled on the project — all three APIs require it, even within their free tiers.

The app never asks for or stores the key itself; it only reads the path from `GOOGLE_APPLICATION_CREDENTIALS`.

### 10.2 `.env` file (env-layer config)

Copy `.env.example` to `.env` and edit. Supported keys:

```dotenv
# Required — absolute or project-relative path to the service-account JSON
GOOGLE_APPLICATION_CREDENTIALS=./secrets/gcp.json

# Optional — where SQLite DB and audio files live (default: ./data)
MYGLOT_DATA_DIR=./data

# Optional — bind address (default: 127.0.0.1, i.e. localhost-only)
MYGLOT_HOST=127.0.0.1
MYGLOT_PORT=8000

# Optional — initial defaults used ONLY on first run to seed the settings row.
# After first run, change these via the Settings UI instead; edits here are ignored.
MYGLOT_DEFAULT_SOURCE_LANG=en-US
MYGLOT_DEFAULT_TARGET_LANG=de-DE
MYGLOT_DEFAULT_TTS_VOICE=           # empty = let server pick a default for target lang

# Provider selection (see §8.3). Each capability is independent.
MYGLOT_TRANSLATE_PROVIDER=google    # google | fake
MYGLOT_TTS_PROVIDER=google          # google | fake
MYGLOT_STT_PROVIDER=google          # google | fake

# Vendor credentials — only set the ones your selected providers need.
# GOOGLE_APPLICATION_CREDENTIALS is already set above for Google providers.
OPENAI_API_KEY=                      # (not yet implemented)
DEEPGRAM_API_KEY=                    # (not yet implemented)

# Optional — limits
MYGLOT_MAX_SOURCE_CHARS=2000
MYGLOT_MAX_AUDIO_UPLOAD_MB=10
```

`secrets/`, `data/`, and `.env` are all gitignored. `.env.example` is committed with safe defaults and no secrets.

On startup the backend:
1. Loads `.env` via `python-dotenv`.
2. Validates that `GOOGLE_APPLICATION_CREDENTIALS` points to a readable file; if missing, it still starts but marks Google-dependent endpoints as **degraded** (they return `503 GOOGLE_NOT_CONFIGURED` with a clear message in the UI).
3. Ensures `MYGLOT_DATA_DIR` and `MYGLOT_DATA_DIR/audio/` exist.
4. Creates `myglot.db` and runs migrations (SQLModel `create_all`) if the file is new.
5. If the `settings` row does not exist yet, inserts it using the `MYGLOT_DEFAULT_*` values.

### 10.3 App settings (DB-layer config, edited via UI)

The **Settings** page in the UI is the normal way to change these. It reads `GET /api/settings` and writes `PUT /api/settings`.

| Field | Type | UI control | Validation |
|-------|------|-----------|------------|
| `source_lang` | BCP-47 string (e.g. `en-US`) | Dropdown of common langs + free-text override | Must match `^[a-z]{2}(-[A-Z]{2})?$` |
| `target_lang` | BCP-47 string | Same | Same; changing it repopulates the voice dropdown |
| `tts_voice` | string or empty | Dropdown populated from `GET /api/voices?lang=<target_lang>` | Must be a voice returned by Google for that lang, or empty (= server default) |

Behaviour rules:
- Changing `target_lang` or `tts_voice` **does not** retroactively regenerate audio for existing items. Each item keeps the `audio_voice` it was created with. If you want items to use the new voice, open them and click **Regenerate audio** — that's the only re-TTS trigger.
- Changing `source_lang` only affects **new** items; existing items keep their original `source_lang`.
- Settings changes are saved immediately on the server (no "unsaved changes" state) and are picked up on the very next API call — no restart needed.
- There is also a **"Test Providers"** button on the Settings page that calls `GET /api/health/providers`, which checks that each configured provider (translator, TTS, STT) can be instantiated. Reports OK / error per capability with green/red status dots. Useful for verifying your `.env` is wired up correctly.

### 10.4 Changing credentials later

If you rotate the service-account key or switch Google projects:
1. Replace `secrets/gcp.json` (same path) **or** update `GOOGLE_APPLICATION_CREDENTIALS` in `.env` to a new path.
2. Restart the server (Ctrl-C, re-run `uvicorn`).
3. Click **Test Providers** in Settings to confirm.

Existing DB rows and audio files are unaffected.

### 10.5 Resetting the app

- **Wipe settings to defaults:** delete the `settings` row (or the whole `myglot.db`) and restart — it will be reseeded from `.env`.
- **Wipe everything:** delete `data/` (DB + audio). Next start creates a fresh DB.
- Secrets in `.env` / `secrets/` are never touched by the app.

---

## 11. Security & Privacy
- Bind to `127.0.0.1` by default.
- No auth in v1 (single local user). Document clearly that exposing to the internet requires adding auth.
- Validate/limit input size (e.g., source text ≤ 2,000 chars; uploaded audio ≤ 10 MB, ≤ 30 s).
- Sanitize filenames (never derived from user input).
- CSRF is N/A for local same-origin JSON; still use `SameSite=Lax` session cookie if any are added later.

---

## 12. Testing Strategy
- **Unit:** similarity scoring, audio path handling, DTO validation.
- **API:** FastAPI `TestClient` with providers set to `fake` (no network).
- **Manual smoke:** add item, edit, regenerate, play, record, download — a short checklist in `README.md`.

> **Current status:** The `backend/tests/` directory does not yet exist. The `task test` command is configured to run `pytest -v` in the backend directory. Tests should use the `fake` providers (see §8.5).

---

## 13. Deployment (Docker)

The primary way to run MyGlot locally is via **Docker Compose**. It keeps the environment reproducible and avoids polluting the host with Python dependencies. All persistent data lives on the host filesystem via bind-mounted volumes so nothing is lost when containers are rebuilt.

### 13.1 Containers

| Container | Base image | Role | Exposed port |
|-----------|-----------|------|-------------|
| `myglot-backend` | `python:3.11-slim` | FastAPI + Uvicorn, serves API **and** the static frontend files | `8000` (mapped to host) |

> A single container is sufficient for v1 — the frontend is plain static files served by FastAPI's `StaticFiles` mount. No separate Nginx or Node container needed. If the frontend grows to need a build step, add a second container then.

### 13.2 Project-level file layout

```
myglot/
  backend/
    Dockerfile
    app/
      ...
  frontend/
    ...
  docker-compose.yml
  .env                  # user-created, gitignored
  .env.example          # committed
  secrets/
    gcp.json            # user-created, gitignored
  data/                 # created at first run, gitignored
    myglot.db
    audio/
```

### 13.3 `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install deps first (layer cache)
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/app ./app

# Copy frontend
COPY frontend ./frontend

# Create mount points
RUN mkdir -p /app/data/audio /app/secrets

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Notes:
- `--host 0.0.0.0` inside the container so Docker port mapping works. The *host-side* mapping in `docker-compose.yml` binds to `127.0.0.1` for security.
- No `GOOGLE_APPLICATION_CREDENTIALS` baked in — it's passed via environment at runtime.

### 13.4 `docker-compose.yml`

```yaml
services:
  myglot:
    build:
      context: .
      dockerfile: backend/Dockerfile
    container_name: myglot
    ports:
      - "127.0.0.1:8000:8000"          # only on localhost
    env_file:
      - .env
    environment:
      # Override paths to match container mount points
      GOOGLE_APPLICATION_CREDENTIALS: /app/secrets/gcp.json
      MYGLOT_DATA_DIR: /app/data
      MYGLOT_HOST: "0.0.0.0"
      MYGLOT_PORT: "8000"
    volumes:
      # Persistent data — DB + audio files survive container rebuilds
      - ./data:/app/data
      # Google credentials (read-only inside container)
      - ./secrets:/app/secrets:ro
    restart: unless-stopped
```

### 13.5 Volume mounts explained

| Host path | Container path | Purpose | Mode |
|-----------|---------------|---------|------|
| `./data` | `/app/data` | SQLite DB (`myglot.db`) + `audio/` folder | read-write |
| `./secrets` | `/app/secrets` | `gcp.json` service-account key | **read-only** |

Because these are **bind mounts** (not named Docker volumes), the files live directly in your project directory. You can:
- Browse `data/audio/*.mp3` from Finder / your file manager.
- Back up `data/` with normal file tools.
- Inspect / edit `data/myglot.db` with `sqlite3` or any DB browser.
- Delete `data/` to wipe everything and start fresh.

The `.env` file is read by Docker Compose via `env_file` and passed as environment variables to the container. It is **not** bind-mounted as a file.

### 13.6 Running

```bash
# First time — build and start
docker compose up --build

# Subsequent starts (no rebuild needed unless code changed)
docker compose up

# Run in background
docker compose up -d

# View logs
docker compose logs -f myglot

# Stop
docker compose down

# Rebuild after code changes
docker compose up --build

# Full reset (wipe data)
docker compose down
rm -rf data/
docker compose up --build
```

Open <http://localhost:8000> in your browser.

### 13.7 Development mode (without Docker)

For faster iteration you can still run without Docker:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The `.env` at the project root is loaded by `python-dotenv`. `task dev` runs uvicorn from the `backend/` directory (set via Taskfile `dir` key), and the `.env` is loaded via the Taskfile `dotenv` directive which loads `../.env` (the project root). Paths like `./data` in `.env` resolve relative to the project root when running via Docker, but relative to `backend/` when using `task dev` — so `MYGLOT_DATA_DIR` is typically set as an absolute path or the default `./data` works because the config resolves it relative to the project root.

### 13.8 `.dockerignore`

```
data/
secrets/
.env
__pycache__/
*.pyc
.git/
.venv/
venv/
.idea/
.vscode/
*.md
```

Keeps secrets, data, and caches out of the build context (faster builds, no credential leaks into image layers).

---

## 14. Delivery Plan (milestones)

1. **M0 — Scaffolding:** repo layout, `Dockerfile`, `docker-compose.yml`, FastAPI hello, SQLite init, static frontend shell, `.env.example`, `.dockerignore`, `.gitignore`, README with setup.
2. **M1 — Add & list items:** Translate + TTS + DB + list UI + play audio + categories CRUD.
3. **M2 — Edit & regenerate:** PATCH target text, regenerate-audio endpoint, stale flag in UI.
4. **M3 — Practice & STT:** mic recording, STT, similarity scoring, diff UI.
5. **M4 — Polish:** voices dropdown, search, delete, download button, tests, README.

---

## 15. Resolved Decisions

| # | Question | Decision |
|---|----------|----------|
| 1 | Languages to start with | Source: `en-US`, Target: `de-DE` |
| 2 | Hide target text in practice? | Yes — hidden by default, revealed on button press |
| 3 | Keep `attempt` history table? | No — score is shown ephemerally after each STT attempt, not persisted |
| 4 | Preferred voice type | Neural2 if available → WaveNet → Standard (cascading fallback) |
| 5 | Frontend framework | Vanilla JS (no framework) |

---

## 16. Implementation Notes (low-level decisions made during coding)

These details supplement the spec and were decided during implementation.

### 16.1 Provider abstraction — ABC vs Protocol
Used `abc.ABC` with `@abstractmethod` (not `typing.Protocol`) for `Translator`, `TTS`, and `STT`. This gives clearer error messages when a subclass forgets to implement a method. The concrete classes are:
- `providers/google/{translate,tts,stt}.py`
- `providers/fake/{translate,tts,stt}.py` (for tests / offline dev)
- `providers/registry.py` — factory functions `get_translator()`, `get_tts()`, `get_stt()` cached with `@lru_cache`. Uses if/elif dispatch (not a dict registry) to select providers by name.
- `providers/base.py` — abstract interfaces + DTO models (Voice, TTSResult, STTResult, ProviderError, ProviderNotConfigured).

### 16.2 Google client singletons
Each Google provider module uses a module-level `_client = None` with a `_get_client()` lazy initializer. This avoids re-creating the gRPC client on every request. The `@lru_cache` on the registry factory ensures one provider instance per process.

### 16.3 Frontend static file serving
FastAPI `StaticFiles(directory=..., html=True)` is mounted at `/` **after** all `/api` routes. The frontend path is resolved at startup with a priority list:
1. `../../frontend` relative to `app/main.py` (local dev)
2. `/app/frontend` (Docker)

### 16.4 Item creation inline category
`POST /api/items` accepts an optional `category_name` field (in addition to `category_id`). If provided and no category with that name exists, it's created on the fly. This avoids a separate round-trip in the UI.

### 16.5 Edit modal
The Home tab uses a modal dialog for editing items (target text + category). This avoids inline-editing complexity and keeps the list view clean.

### 16.6 Practice — reveal toggle
In the Practice tab, each item's target text has `filter: blur(5px)` by default. The "Reveal" button toggles the blur on/off per-item and changes its label to "Hide".

### 16.7 Recording flow
The Record button is a toggle: click once to start recording, click again to stop. While recording, the button pulses (CSS animation) and shows "⏹ Stop". On stop, the blob is immediately sent to `POST /api/items/{id}/practice`.

### 16.8 `docker-compose.yml` — no `version` key
Modern Docker Compose (v2+) no longer requires the `version` field. Omitted for simplicity.

### 16.8b Route file organization
Backup, restore, and backup-schedule endpoints all live in `routes/health.py` alongside the health checks. This keeps all "infrastructure" endpoints together. The items, categories, settings, and voices routes each have their own file.

### 16.9 Category deletion — manual SET NULL
SQLite `ON DELETE SET NULL` may not fire through SQLModel's cascade config, so `DELETE /api/categories/{id}` manually nullifies `item.category_id` before deleting the category row.

### 16.10 Settings seeding
`Settings` row (id=1) is seeded both in `main.py` startup and lazily in `routes/settings.py._ensure_settings()`. The double-check ensures it exists regardless of startup order or test setup.

### 16.11 Table layout for Home & Practice
Both the Home and Practice tabs use an HTML `<table>` layout with columns: source text, target translation, category, and action buttons. The Home tab also has a drag-handle column for reordering. This replaced the earlier card-based layout for a cleaner, more compact view.

### 16.12 Multi-category filter with sticky selection
Category filters on Home and Practice are `<select multiple>` elements. Selections are persisted to `localStorage` (keys `myglot_home-category-filter` and `myglot_practice-category-filter`) and restored on page load. The backend accepts `category_ids` as comma-separated integers.

### 16.13 Regenerate audio always visible
The **Regenerate audio** action is always available from the **Edit** modal (not only when `audio_stale` is true). This allows re-generating audio after changing the TTS voice in Settings.

### 16.13b New item sort order
When a new item is created, its `sort_order` is set to `min(existing_sort_orders) - 1` so it appears at the top of the list. If no items exist, `sort_order` defaults to 0.

### 16.14 Database backup & restore
- **Backup** (`GET /api/backup`): uses SQLite's Online Backup API to create a consistent, lock-free copy of the database, served as a timestamped `.db` file download (`myglot_backup_YYYYMMDD_HHMMSS.db`).
- **Restore** (`POST /api/restore`): accepts a `.db` file upload, validates it contains the expected tables (`item`, `settings`), creates a safety copy of the current DB (`myglot_pre_restore_YYYYMMDD_HHMMSS.db` in the `data/` directory), disposes the SQLAlchemy engine, swaps the file, and reinitializes the engine + runs migrations. The frontend reloads after restore.
- **Automatic backups** (`scheduler.py`): a background asyncio task runs every 60 seconds, reads the `BackupSchedule` row, checks `croniter` to see if a backup is due, and creates a timestamped snapshot using SQLite Online Backup API. Old backups beyond `max_backups` are automatically deleted. Uses the `croniter` library for cron expression parsing.

### 16.15 File layout (actual)
```
myglot/
  SPEC.md
  README.md
  Taskfile.yml
  .env.example
  .gitignore
  .dockerignore
  docker-compose.yml
  .github/
    copilot-instructions.md
  docs/
    GOOGLE_CLOUD_SETUP.md
  backend/
    Dockerfile
    requirements.txt
    pyproject.toml
    app/
      __init__.py
      main.py
      config.py
      db.py
      migrate.py
      models.py
      schemas.py
      errors.py
      scheduler.py
      migrations/
        __init__.py
        001_add_sort_order.py
        002_add_backup_schedule.py
      routes/
        __init__.py
        health.py
        settings.py
        voices.py
        categories.py
        items.py
      providers/
        __init__.py
        base.py
        registry.py
        google/
          __init__.py
          translate.py
          tts.py
          stt.py
        fake/
          __init__.py
          translate.py
          tts.py
          stt.py
      services/
        __init__.py
        audio_store.py
        similarity.py
  frontend/
    index.html
    styles.css
    biome.json
    package.json
    js/
      api.js
      util.js
      recorder.js
      home.js
      practice.js
      settings.js
      app.js
  data/                     # gitignored; created at first run
    myglot.db
    audio/
  secrets/                  # gitignored
    gcp.json
```

---

*End of spec.*
