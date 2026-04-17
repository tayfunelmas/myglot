from fastapi import APIRouter

from ..config import get_config
from ..providers.base import ProviderError
from ..providers.registry import get_stt, get_translator, get_tts
from ..schemas import HealthProviders, ProviderStatus

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/health/providers", response_model=HealthProviders)
def health_providers():
    cfg = get_config()

    def check_translator() -> ProviderStatus:
        try:
            t = get_translator()
            return ProviderStatus(provider=t.name, ok=True)
        except (ProviderError, Exception) as e:
            return ProviderStatus(provider=cfg.translate_provider, ok=False, error=str(e))

    def check_tts() -> ProviderStatus:
        try:
            t = get_tts()
            return ProviderStatus(provider=t.name, ok=True)
        except (ProviderError, Exception) as e:
            return ProviderStatus(provider=cfg.tts_provider, ok=False, error=str(e))

    def check_stt() -> ProviderStatus:
        try:
            s = get_stt()
            return ProviderStatus(provider=s.name, ok=True)
        except (ProviderError, Exception) as e:
            return ProviderStatus(provider=cfg.stt_provider, ok=False, error=str(e))

    return HealthProviders(
        translator=check_translator(),
        tts=check_tts(),
        stt=check_stt(),
    )
