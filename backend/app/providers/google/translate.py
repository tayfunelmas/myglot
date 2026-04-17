from __future__ import annotations

from ..base import ProviderError, Translator

_client = None


def _get_client():
    global _client
    if _client is None:
        from google.cloud import translate_v2

        _client = translate_v2.Client()
    return _client


class GoogleTranslator(Translator):
    name = "google"

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        try:
            client = _get_client()
            # Google Translate v2 uses ISO-639-1 (2-letter) codes
            src = source_lang.split("-")[0]
            tgt = target_lang.split("-")[0]
            result = client.translate(text, source_language=src, target_language=tgt)
            return result["translatedText"]
        except Exception as e:
            raise ProviderError(f"Google Translate error: {e}") from e
