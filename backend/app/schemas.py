from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


# --- Categories ---
class CategoryCreate(BaseModel):
    name: str


class CategoryUpdate(BaseModel):
    name: str


class CategoryOut(BaseModel):
    id: int
    name: str
    item_count: int = 0
    created_at: datetime


class CategoryRef(BaseModel):
    id: int
    name: str


# --- Translate ---
class TranslateRequest(BaseModel):
    source_text: str


class TranslateResponse(BaseModel):
    target_text: str
    explanation: str | None = None


class TranslateBackRequest(BaseModel):
    target_text: str


class TranslateBackResponse(BaseModel):
    source_text: str
    explanation: str | None = None


class TtsPreviewRequest(BaseModel):
    text: str
    voice: str | None = None


# --- Items ---
class ItemCreate(BaseModel):
    source_text: str
    target_text: str | None = None  # if provided, skip translation
    explanation: str | None = None
    category_id: int | None = None
    category_name: str | None = None  # create-inline: provide name to auto-create


class ItemUpdate(BaseModel):
    target_text: str | None = None
    explanation: str | None = None
    category_id: int | None = None


class ItemOut(BaseModel):
    id: int
    source_lang: str
    target_lang: str
    source_text: str
    target_text: str
    explanation: str | None = None
    audio_url: str | None = None
    audio_voice: str | None = None
    audio_provider: str | None = None
    audio_stale: bool = False
    category: CategoryRef | None = None
    created_at: datetime
    updated_at: datetime


class ItemListOut(BaseModel):
    items: list[ItemOut]
    total: int


# --- Settings ---
class SettingsOut(BaseModel):
    source_lang: str
    target_lang: str
    tts_voice: str


class SettingsUpdate(BaseModel):
    source_lang: str | None = None
    target_lang: str | None = None
    tts_voice: str | None = None


# --- Notes ---
class NoteCreate(BaseModel):
    title: str
    body: str = ""


class NoteUpdate(BaseModel):
    title: str | None = None
    body: str | None = None


class NoteOut(BaseModel):
    id: int
    title: str
    body: str
    created_at: datetime
    updated_at: datetime


# --- Practice ---
class PracticeResult(BaseModel):
    transcript: str
    score: int
    diff: list[dict]


class ReorderRequest(BaseModel):
    item_ids: list[int]


# --- Health ---
class ProviderStatus(BaseModel):
    provider: str
    ok: bool
    error: str | None = None


class HealthProviders(BaseModel):
    translator: ProviderStatus
    tts: ProviderStatus
    stt: ProviderStatus


# --- Errors ---
class ErrorDetail(BaseModel):
    code: str
    message: str


# --- Backup Schedule ---
class BackupScheduleOut(BaseModel):
    enabled: bool
    cron_expr: str
    destination_dir: str
    max_backups: int
    last_run_at: datetime | None = None
    last_status: str


class BackupScheduleUpdate(BaseModel):
    enabled: bool | None = None
    cron_expr: str | None = None
    destination_dir: str | None = None
    max_backups: int | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
