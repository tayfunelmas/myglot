from fastapi import APIRouter

from ..providers.registry import get_tts
from ..providers.base import Voice, ProviderError
from ..errors import ProviderAPIError

router = APIRouter(tags=["voices"])


@router.get("/voices", response_model=list[Voice])
def list_voices(lang: str = "de-DE"):
    try:
        tts = get_tts()
        return tts.list_voices(lang)
    except ProviderError as e:
        raise ProviderAPIError("tts", str(e))
