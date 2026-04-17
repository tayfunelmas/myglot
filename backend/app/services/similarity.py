from __future__ import annotations

import difflib
import re
import unicodedata

from pydantic import BaseModel


class ScoreResult(BaseModel):
    score: int
    diff: list[dict]


def _normalize(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace, Unicode NFC."""
    text = unicodedata.normalize("NFC", text)
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _word_f1(expected_words: list[str], actual_words: list[str]) -> float:
    """Compute word-level F1 score."""
    if not expected_words and not actual_words:
        return 1.0
    if not expected_words or not actual_words:
        return 0.0

    expected_set: dict[str, int] = {}
    for w in expected_words:
        expected_set[w] = expected_set.get(w, 0) + 1

    actual_set: dict[str, int] = {}
    for w in actual_words:
        actual_set[w] = actual_set.get(w, 0) + 1

    tp = 0
    for w, count in expected_set.items():
        tp += min(count, actual_set.get(w, 0))

    precision = tp / len(actual_words) if actual_words else 0
    recall = tp / len(expected_words) if expected_words else 0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def _word_diff(expected: str, actual: str) -> list[dict]:
    """Generate word-level diff for UI highlighting."""
    expected_words = expected.split()
    actual_words = actual.split()

    matcher = difflib.SequenceMatcher(None, expected_words, actual_words)
    diff = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for w in expected_words[i1:i2]:
                diff.append({"word": w, "status": "match"})
        elif tag == "delete":
            for w in expected_words[i1:i2]:
                diff.append({"word": w, "status": "missing"})
        elif tag == "insert":
            for w in actual_words[j1:j2]:
                diff.append({"word": w, "status": "extra"})
        elif tag == "replace":
            for w in expected_words[i1:i2]:
                diff.append({"word": w, "status": "missing"})
            for w in actual_words[j1:j2]:
                diff.append({"word": w, "status": "extra"})

    return diff


def score(expected: str, actual: str) -> ScoreResult:
    """Compare expected target text with STT transcript. Returns 0-100 score and diff."""
    norm_expected = _normalize(expected)
    norm_actual = _normalize(actual)

    char_ratio = difflib.SequenceMatcher(None, norm_expected, norm_actual).ratio()

    expected_words = norm_expected.split()
    actual_words = norm_actual.split()
    word_f1 = _word_f1(expected_words, actual_words)

    final_score = round(100 * max(char_ratio, word_f1))

    diff = _word_diff(norm_expected, norm_actual)

    return ScoreResult(score=final_score, diff=diff)
