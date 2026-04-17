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


# --- Items ---
class ItemCreate(BaseModel):
    source_text: str
    category_id: int | None = None
    category_name: str | None = None  # create-inline: provide name to auto-create


class ItemUpdate(BaseModel):
    target_text: str | None = None
    category_id: int | None = None


class ItemOut(BaseModel):
    id: int
    source_lang: str
    target_lang: str
    source_text: str
    target_text: str
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


# --- Practice ---
class PracticeResult(BaseModel):
    transcript: str
    score: int
    diff: list[dict]


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


class ErrorResponse(BaseModel):
    error: ErrorDetail
