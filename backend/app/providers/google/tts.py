from __future__ import annotations

from ..base import TTS, TTSResult, Voice, ProviderError

_client = None


def _get_client():
    global _client
    if _client is None:
        from google.cloud import texttospeech
        _client = texttospeech.TextToSpeechClient()
    return _client


def _pick_best_voice(voices: list, lang: str) -> str | None:
    """Pick Neural2 > WaveNet > Standard from available voices."""
    ranked: dict[str, list] = {"Neural2": [], "Wavenet": [], "Standard": []}
    for v in voices:
        for tier in ranked:
            if tier.lower() in v.name.lower():
                ranked[tier].append(v.name)
                break
    for tier in ("Neural2", "Wavenet", "Standard"):
        if ranked[tier]:
            return ranked[tier][0]
    return voices[0].name if voices else None


class GoogleTTS(TTS):
    name = "google"

    def synthesize(self, text: str, lang: str, voice_id: str | None = None) -> TTSResult:
        try:
            from google.cloud import texttospeech
            client = _get_client()

            if not voice_id:
                voices_resp = client.list_voices(language_code=lang)
                voice_id = _pick_best_voice(voices_resp.voices, lang)

            voice_params = texttospeech.VoiceSelectionParams(
                language_code=lang,
                name=voice_id if voice_id else None,
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
            )
            response = client.synthesize_speech(
                input=texttospeech.SynthesisInput(text=text),
                voice=voice_params,
                audio_config=audio_config,
            )
            return TTSResult(
                audio_bytes=response.audio_content,
                mime="audio/mpeg",
                voice_id=voice_id or lang,
            )
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(f"Google TTS error: {e}") from e

    def list_voices(self, lang: str) -> list[Voice]:
        try:
            from google.cloud import texttospeech
            client = _get_client()
            response = client.list_voices(language_code=lang)
            results = []
            for v in response.voices:
                gender_map = {
                    texttospeech.SsmlVoiceGender.MALE: "male",
                    texttospeech.SsmlVoiceGender.FEMALE: "female",
                    texttospeech.SsmlVoiceGender.NEUTRAL: "neutral",
                }
                results.append(Voice(
                    id=v.name,
                    display_name=v.name,
                    gender=gender_map.get(v.ssml_gender, "unknown"),
                    lang=lang,
                    provider="google",
                ))
            return results
        except Exception as e:
            raise ProviderError(f"Google TTS list_voices error: {e}") from e
