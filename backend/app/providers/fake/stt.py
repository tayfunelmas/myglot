from __future__ import annotations

from ..base import STT, STTResult


class FakeSTT(STT):
    name = "fake"

    def __init__(self, preset_transcript: str = ""):
        self._preset = preset_transcript

    def transcribe(self, audio_bytes: bytes, mime: str, lang: str) -> STTResult:
        return STTResult(transcript=self._preset, confidence=1.0)
