from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..db import get_session
from ..models import Settings
from ..schemas import SettingsOut, SettingsUpdate
from ..config import get_config

router = APIRouter(tags=["settings"])


def _ensure_settings(session: Session) -> Settings:
    """Get or create the singleton settings row."""
    settings = session.get(Settings, 1)
    if settings is None:
        cfg = get_config()
        settings = Settings(
            id=1,
            source_lang=cfg.default_source_lang,
            target_lang=cfg.default_target_lang,
            tts_voice=cfg.default_tts_voice,
        )
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return settings


@router.get("/settings", response_model=SettingsOut)
def get_settings(session: Session = Depends(get_session)):
    settings = _ensure_settings(session)
    return SettingsOut(
        source_lang=settings.source_lang,
        target_lang=settings.target_lang,
        tts_voice=settings.tts_voice,
    )


@router.put("/settings", response_model=SettingsOut)
def update_settings(data: SettingsUpdate, session: Session = Depends(get_session)):
    settings = _ensure_settings(session)
    if data.source_lang is not None:
        settings.source_lang = data.source_lang
    if data.target_lang is not None:
        settings.target_lang = data.target_lang
    if data.tts_voice is not None:
        settings.tts_voice = data.tts_voice
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return SettingsOut(
        source_lang=settings.source_lang,
        target_lang=settings.target_lang,
        tts_voice=settings.tts_voice,
    )
