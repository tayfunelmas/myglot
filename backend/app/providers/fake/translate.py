from __future__ import annotations

from ..base import TranslateResult, Translator


class FakeTranslator(Translator):
    name = "fake"

    def translate(self, text: str, source_lang: str, target_lang: str) -> TranslateResult:
        return TranslateResult(text=f"[{target_lang}] {text}")
