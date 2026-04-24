from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel


class Voice(BaseModel):
    id: str
    display_name: str
    gender: Literal["male", "female", "neutral", "unknown"] = "unknown"
    lang: str
    provider: str


class TTSResult(BaseModel):
    audio_bytes: bytes
    mime: str
    voice_id: str


class TranslateResult(BaseModel):
    text: str
    explanation: str | None = None


class STTResult(BaseModel):
    transcript: str
    confidence: float | None = None


class ProviderError(Exception):
    pass


class ProviderNotConfigured(ProviderError):
    pass


class Translator(ABC):
    name: str

    @abstractmethod
    def translate(self, text: str, source_lang: str, target_lang: str) -> TranslateResult: ...


class TTS(ABC):
    name: str

    @abstractmethod
    def synthesize(self, text: str, lang: str, voice_id: str | None = None) -> TTSResult: ...

    @abstractmethod
    def list_voices(self, lang: str) -> list[Voice]: ...


class STT(ABC):
    name: str

    @abstractmethod
    def transcribe(self, audio_bytes: bytes, mime: str, lang: str) -> STTResult: ...
