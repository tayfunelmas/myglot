from datetime import UTC, datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    items: List["Item"] = Relationship(back_populates="category")


class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")
    source_lang: str
    target_lang: str
    source_text: str
    target_text: str
    audio_path: Optional[str] = None
    audio_voice: Optional[str] = None
    audio_provider: Optional[str] = None
    audio_stale: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    category: Optional[Category] = Relationship(back_populates="items")


class Settings(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)
    source_lang: str = "en-US"
    target_lang: str = "de-DE"
    tts_voice: str = ""
