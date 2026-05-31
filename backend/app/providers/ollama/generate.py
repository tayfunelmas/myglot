from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from ..base import ProviderError, TextGenerateResult, TextGenerator

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


def _build_prompt(instructions: str, source_lang: str, target_lang: str) -> str:
    src = _lang_name(source_lang)
    tgt = _lang_name(target_lang)
    return f"""You are a language learning assistant. The user wants to learn {tgt}.

**User's request (in {src}):** {instructions}

Generate the following:

1. A short descriptive title in {src} (2-5 words summarizing the topic).
2. A simple text, paragraph, or dialog in {tgt} appropriate for language learners. Use basic vocabulary and short sentences. The text should be 3-8 sentences long.
3. A vocabulary table in Markdown listing the key words/phrases from the generated text, with columns for the {tgt} word and the {src} translation.

Respond in EXACTLY this format (keep the markers on their own lines):

---TITLE_START---
<put ONLY the title here in {src}, nothing else>
---TITLE_END---

---TEXT_START---
<put ONLY the generated text/dialog here in {tgt}, nothing else>
---TEXT_END---

---VOCABULARY_START---
<put a Markdown table here with columns: {tgt} | {src}>
---VOCABULARY_END---

Example vocabulary table format:
| {tgt} | {src} |
|---|---|
| word1 | translation1 |
| word2 | translation2 |"""


def _parse_response(raw: str) -> tuple[str, str, str]:
    """Extract title, body text, and vocabulary from the model response."""
    # Extract title
    m = re.search(
        r"---TITLE_START---\s*\n(.*?)\n\s*---TITLE_END---",
        raw,
        re.DOTALL,
    )
    title = m.group(1).strip() if m else "Generated Text"

    # Extract body text
    m2 = re.search(
        r"---TEXT_START---\s*\n(.*?)\n\s*---TEXT_END---",
        raw,
        re.DOTALL,
    )
    body = m2.group(1).strip() if m2 else raw.strip()

    # Extract vocabulary
    m3 = re.search(
        r"---VOCABULARY_START---\s*\n(.*?)\n\s*---VOCABULARY_END---",
        raw,
        re.DOTALL,
    )
    vocabulary_md = m3.group(1).strip() if m3 else ""

    return title, body, vocabulary_md


class OllamaTextGenerator(TextGenerator):
    name = "ollama"

    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    def generate(self, instructions: str, source_lang: str, target_lang: str) -> TextGenerateResult:
        prompt = _build_prompt(instructions, source_lang, target_lang)
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
            with urllib.request.urlopen(req, timeout=180) as resp:
                resp_body = json.loads(resp.read().decode())
        except urllib.error.URLError as e:
            raise ProviderError(
                f"Ollama connection error ({self._base_url}): {e}. "
                "Is the Ollama server running? Start it with: ollama serve"
            ) from e
        except Exception as e:
            raise ProviderError(f"Ollama error: {e}") from e

        raw_response = resp_body.get("response", "")
        if not raw_response.strip():
            raise ProviderError("Ollama returned an empty response")

        title, body, vocabulary_md = _parse_response(raw_response)
        return TextGenerateResult(title=title, body=body, vocabulary_md=vocabulary_md)
