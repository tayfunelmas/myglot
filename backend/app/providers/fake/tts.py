from __future__ import annotations

from ..base import TTS, TTSResult, Voice

# Minimal valid MP3 frame (silent) for testing
_SILENT_MP3 = (
    b"\xff\xfb\x90\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
)


class FakeTTS(TTS):
    name = "fake"

    def synthesize(self, text: str, lang: str, voice_id: str | None = None) -> TTSResult:
        return TTSResult(
            audio_bytes=_SILENT_MP3,
            mime="audio/mpeg",
            voice_id=voice_id or f"{lang}-Fake-A",
        )

    def list_voices(self, lang: str) -> list[Voice]:
        return [
            Voice(
                id=f"{lang}-Fake-A",
                display_name="Fake Voice A",
                gender="female",
                lang=lang,
                provider="fake",
            ),
            Voice(
                id=f"{lang}-Fake-B",
                display_name="Fake Voice B",
                gender="male",
                lang=lang,
                provider="fake",
            ),
        ]
