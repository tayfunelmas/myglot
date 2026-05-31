from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlmodel import Session, col, select

from ..db import get_session
from ..errors import NotFoundError, ProviderAPIError, ValidationError
from ..models import GeneratedText, Settings
from ..providers.base import ProviderError
from ..providers.registry import get_text_generator, get_tts
from ..schemas import GeneratedTextCreate, GeneratedTextOut
from ..services import audio_store

router = APIRouter(tags=["texts"])


def _get_settings(session: Session) -> Settings:
    from ..routes.settings import _ensure_settings

    return _ensure_settings(session)


def _text_to_out(text: GeneratedText) -> GeneratedTextOut:
    return GeneratedTextOut(
        id=text.id,  # type: ignore[arg-type]
        title=text.title,
        body=text.body,
        vocabulary_md=text.vocabulary_md,
        source_lang=text.source_lang,
        target_lang=text.target_lang,
        audio_url=f"/api/texts/{text.id}/audio" if text.audio_path else None,
        audio_voice=text.audio_voice,
        audio_provider=text.audio_provider,
        created_at=text.created_at,
        updated_at=text.updated_at,
    )


@router.get("/texts", response_model=list[GeneratedTextOut])
def list_texts(session: Session = Depends(get_session)):
    stmt = select(GeneratedText).order_by(col(GeneratedText.created_at).desc())
    texts = session.exec(stmt).all()
    return [_text_to_out(t) for t in texts]


@router.post("/texts", response_model=GeneratedTextOut, status_code=201)
def create_text(data: GeneratedTextCreate, session: Session = Depends(get_session)):
    instructions = data.instructions.strip()
    if not instructions:
        raise ValidationError("Instructions cannot be empty")

    settings = _get_settings(session)
    source_lang = settings.source_lang
    target_lang = settings.target_lang

    # Generate text using the text generator provider
    try:
        generator = get_text_generator()
        result = generator.generate(instructions, source_lang, target_lang)
    except ProviderError as e:
        raise ProviderAPIError("text_generator", str(e)) from e

    # Generate audio for the body text
    audio_path = None
    audio_voice = None
    audio_provider = None
    try:
        tts = get_tts()
        voice_id = settings.tts_voice or None
        tts_result = tts.synthesize(result.body, target_lang, voice_id)
        audio_path = audio_store.save(tts_result.audio_bytes, tts_result.mime)
        audio_voice = tts_result.voice_id
        audio_provider = tts.name
    except ProviderError:
        pass  # Audio generation is best-effort

    text = GeneratedText(
        title=result.title,
        body=result.body,
        vocabulary_md=result.vocabulary_md,
        source_lang=source_lang,
        target_lang=target_lang,
        audio_path=audio_path,
        audio_voice=audio_voice,
        audio_provider=audio_provider,
    )
    session.add(text)
    session.commit()
    session.refresh(text)
    return _text_to_out(text)


@router.get("/texts/{text_id}", response_model=GeneratedTextOut)
def get_text(text_id: int, session: Session = Depends(get_session)):
    text = session.get(GeneratedText, text_id)
    if not text:
        raise NotFoundError("GeneratedText", text_id)
    return _text_to_out(text)


@router.delete("/texts/{text_id}", status_code=204)
def delete_text(text_id: int, session: Session = Depends(get_session)):
    text = session.get(GeneratedText, text_id)
    if not text:
        raise NotFoundError("GeneratedText", text_id)
    if text.audio_path:
        audio_store.delete(text.audio_path)
    session.delete(text)
    session.commit()


@router.post("/texts/{text_id}/regenerate-audio", response_model=GeneratedTextOut)
def regenerate_text_audio(text_id: int, session: Session = Depends(get_session)):
    text = session.get(GeneratedText, text_id)
    if not text:
        raise NotFoundError("GeneratedText", text_id)

    settings = _get_settings(session)
    try:
        tts = get_tts()
        voice_id = settings.tts_voice or None
        tts_result = tts.synthesize(text.body, text.target_lang, voice_id)
    except ProviderError as e:
        raise ProviderAPIError("tts", str(e)) from e

    # Delete old audio
    if text.audio_path:
        audio_store.delete(text.audio_path)

    text.audio_path = audio_store.save(tts_result.audio_bytes, tts_result.mime)
    text.audio_voice = tts_result.voice_id
    text.audio_provider = tts.name
    session.add(text)
    session.commit()
    session.refresh(text)
    return _text_to_out(text)


@router.get("/texts/{text_id}/audio")
def get_text_audio(text_id: int, session: Session = Depends(get_session)):
    text = session.get(GeneratedText, text_id)
    if not text:
        raise NotFoundError("GeneratedText", text_id)
    if not text.audio_path:
        from ..errors import AudioMissingError

        raise AudioMissingError(text_id)
    path = audio_store.get_absolute_path(text.audio_path)
    if not path.exists():
        from ..errors import AudioMissingError

        raise AudioMissingError(text_id)
    return FileResponse(path, media_type="audio/mpeg")
