from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from ..base import ProviderError, TranslateResult, Translator

# Language name mapping for common BCP-47 codes
_LANG_NAMES: dict[str, str] = {
    "en": "English",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "pl": "Polish",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "ar": "Arabic",
    "tr": "Turkish",
    "sv": "Swedish",
    "da": "Danish",
    "fi": "Finnish",
    "no": "Norwegian",
    "cs": "Czech",
    "el": "Greek",
    "he": "Hebrew",
    "hi": "Hindi",
    "th": "Thai",
    "vi": "Vietnamese",
    "uk": "Ukrainian",
    "ro": "Romanian",
    "hu": "Hungarian",
}


def _lang_name(code: str) -> str:
    short = code.split("-")[0].lower()
    return _LANG_NAMES.get(short, code)


def _build_prompt(text: str, source_lang: str, target_lang: str) -> str:
    src = _lang_name(source_lang)
    tgt = _lang_name(target_lang)
    return f"""Translate the following text from {src} to {tgt}.

**Text to translate:** {text}

Respond in EXACTLY this format (keep the markers on their own lines):

---TRANSLATION_START---
<put ONLY the translated text here, nothing else>
---TRANSLATION_END---

---EXPLANATION_START---
<put a word-by-word / phrase-by-phrase explanation here in Markdown>
---EXPLANATION_END---

In the explanation section, break down the translation word by word or phrase by phrase.
For each word/phrase, show the {tgt} word, its {src} meaning, and any grammar notes (gender, case, conjugation, etc.).
Use a Markdown table or bullet list. Be concise but helpful."""


def _parse_response(raw: str) -> tuple[str, str | None]:
    """Extract translation and explanation from the model response."""
    # Extract translation
    m = re.search(
        r"---TRANSLATION_START---\s*\n(.*?)\n\s*---TRANSLATION_END---",
        raw,
        re.DOTALL,
    )
    if m:
        translation = m.group(1).strip()
    else:
        # Fallback: use the first non-empty line as translation
        lines = [ln.strip() for ln in raw.strip().splitlines() if ln.strip()]
        translation = lines[0] if lines else raw.strip()

    # Extract explanation
    m2 = re.search(
        r"---EXPLANATION_START---\s*\n(.*?)\n\s*---EXPLANATION_END---",
        raw,
        re.DOTALL,
    )
    explanation = m2.group(1).strip() if m2 else None

    return translation, explanation


class OllamaTranslator(Translator):
    name = "ollama"

    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    def translate(self, text: str, source_lang: str, target_lang: str) -> TranslateResult:
        prompt = _build_prompt(text, source_lang, target_lang)
        try:
            payload = json.dumps(
                {
                    "model": self._model,
                    "prompt": prompt,
                    "stream": False,
                }
            ).encode()
            req = urllib.request.Request(
                f"{self._base_url}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode())
        except urllib.error.URLError as e:
            raise ProviderError(
                f"Ollama connection error ({self._base_url}): {e}. "
                "Is the Ollama server running? Start it with: ollama serve"
            ) from e
        except Exception as e:
            raise ProviderError(f"Ollama error: {e}") from e

        raw_response = body.get("response", "")
        if not raw_response.strip():
            raise ProviderError("Ollama returned an empty response")

        translation, explanation = _parse_response(raw_response)
        return TranslateResult(text=translation, explanation=explanation)
