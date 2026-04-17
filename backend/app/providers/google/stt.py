from __future__ import annotations

from ..base import STT, ProviderError, STTResult

_client = None


def _get_client():
    global _client
    if _client is None:
        from google.cloud import speech

        _client = speech.SpeechClient()
    return _client


# Map browser MIME types to Google Speech encoding
_ENCODING_MAP = {
    "audio/webm": "WEBM_OPUS",
    "audio/webm;codecs=opus": "WEBM_OPUS",
    "audio/ogg": "OGG_OPUS",
    "audio/ogg;codecs=opus": "OGG_OPUS",
    "audio/wav": "LINEAR16",
    "audio/x-wav": "LINEAR16",
    "audio/flac": "FLAC",
}


class GoogleSTT(STT):
    name = "google"

    def transcribe(self, audio_bytes: bytes, mime: str, lang: str) -> STTResult:
        try:
            from google.cloud import speech

            client = _get_client()

            encoding_name = _ENCODING_MAP.get(mime.lower().split(";")[0])
            if mime.lower() in _ENCODING_MAP:
                encoding_name = _ENCODING_MAP[mime.lower()]
            elif mime.lower().split(";")[0] in _ENCODING_MAP:
                encoding_name = _ENCODING_MAP[mime.lower().split(";")[0]]

            encoding = (
                getattr(speech.RecognitionConfig.AudioEncoding, encoding_name)
                if encoding_name
                else speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED
            )

            config = speech.RecognitionConfig(
                encoding=encoding,
                language_code=lang,
                enable_automatic_punctuation=True,
            )
            # For WEBM_OPUS sample rate is detected automatically
            if encoding_name == "LINEAR16":
                config.sample_rate_hertz = 48000

            audio = speech.RecognitionAudio(content=audio_bytes)
            response = client.recognize(config=config, audio=audio)

            transcript = ""
            confidence = None
            for result in response.results:
                if result.alternatives:
                    transcript += result.alternatives[0].transcript
                    if confidence is None:
                        confidence = result.alternatives[0].confidence

            return STTResult(transcript=transcript, confidence=confidence)
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(f"Google STT error: {e}") from e
