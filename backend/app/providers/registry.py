from __future__ import annotations

from functools import lru_cache

from ..config import Config, get_config
from .base import STT, TTS, ProviderNotConfigured, Translator


def _build_translator(cfg: Config) -> Translator:
    name = cfg.translate_provider
    if name == "google":
        from .google.translate import GoogleTranslator

        return GoogleTranslator()
    elif name == "fake":
        from .fake.translate import FakeTranslator

        return FakeTranslator()
    else:
        raise ProviderNotConfigured(f"Unknown translate provider: {name}")


def _build_tts(cfg: Config) -> TTS:
    name = cfg.tts_provider
    if name == "google":
        from .google.tts import GoogleTTS

        return GoogleTTS()
    elif name == "fake":
        from .fake.tts import FakeTTS

        return FakeTTS()
    else:
        raise ProviderNotConfigured(f"Unknown TTS provider: {name}")


def _build_stt(cfg: Config) -> STT:
    name = cfg.stt_provider
    if name == "google":
        from .google.stt import GoogleSTT

        return GoogleSTT()
    elif name == "fake":
        from .fake.stt import FakeSTT

        return FakeSTT()
    else:
        raise ProviderNotConfigured(f"Unknown STT provider: {name}")


@lru_cache
def get_translator() -> Translator:
    return _build_translator(get_config())


@lru_cache
def get_tts() -> TTS:
    return _build_tts(get_config())


@lru_cache
def get_stt() -> STT:
    return _build_stt(get_config())
