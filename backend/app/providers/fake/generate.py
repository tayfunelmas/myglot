from __future__ import annotations

from ..base import TextGenerateResult, TextGenerator


class FakeTextGenerator(TextGenerator):
    name = "fake"

    def generate(self, instructions: str, source_lang: str, target_lang: str) -> TextGenerateResult:
        return TextGenerateResult(
            title="Sample Text",
            body="Dies ist ein einfacher Beispieltext. Er wurde für Testzwecke erstellt.",
            vocabulary_md="| Target | Source |\n|---|---|\n| einfach | simple |\n| Beispiel | example |\n| Text | text |",
        )
