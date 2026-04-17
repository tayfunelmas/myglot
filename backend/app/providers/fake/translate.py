from __future__ import annotations

from ..base import Translator


class FakeTranslator(Translator):
    name = "fake"

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        return f"[{target_lang}] {text}"
