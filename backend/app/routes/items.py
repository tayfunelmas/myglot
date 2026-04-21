from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse, Response
from sqlmodel import Session, col, func, select

from ..config import get_config
from ..db import get_session
from ..errors import (
    AudioMissingError,
    NotFoundError,
    ProviderAPIError,
    ValidationError,
)
from ..models import Category, Item, Settings
from ..providers.base import ProviderError
from ..providers.registry import get_stt, get_translator, get_tts
from ..schemas import (
    CategoryRef,
    ItemCreate,
    ItemListOut,
    ItemOut,
    ItemUpdate,
    PracticeResult,
    ReorderRequest,
    TranslateBackRequest,
    TranslateBackResponse,
    TranslateRequest,
    TranslateResponse,
    TtsPreviewRequest,
)
from ..services import audio_store, similarity

router = APIRouter(tags=["items"])


def _item_to_out(item: Item) -> ItemOut:
    cat_ref = None
    if item.category:
        cat_ref = CategoryRef(id=item.category.id, name=item.category.name)  # type: ignore[arg-type]
    return ItemOut(
        id=item.id,  # type: ignore[arg-type]
        source_lang=item.source_lang,
        target_lang=item.target_lang,
        source_text=item.source_text,
        target_text=item.target_text,
        audio_url=f"/api/items/{item.id}/audio" if item.audio_path else None,
        audio_voice=item.audio_voice,
        audio_provider=item.audio_provider,
        audio_stale=item.audio_stale,
        category=cat_ref,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _get_settings(session: Session) -> Settings:
    from ..routes.settings import _ensure_settings

    return _ensure_settings(session)


@router.get("/items", response_model=ItemListOut)
def list_items(
    q: str | None = None,
    category_id: int | None = None,
    category_ids: str | None = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    session: Session = Depends(get_session),
):
    stmt = select(Item)
    count_stmt = select(func.count(Item.id))  # type: ignore[arg-type]

    # Support multi-category filter (comma-separated) or single category_id
    if category_ids:
        ids = [int(x) for x in category_ids.split(",") if x.strip().isdigit()]
        if ids:
            stmt = stmt.where(col(Item.category_id).in_(ids))
            count_stmt = count_stmt.where(col(Item.category_id).in_(ids))
    elif category_id is not None:
        stmt = stmt.where(Item.category_id == category_id)
        count_stmt = count_stmt.where(Item.category_id == category_id)

    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            col(Item.source_text).ilike(pattern) | col(Item.target_text).ilike(pattern)
        )
        count_stmt = count_stmt.where(
            col(Item.source_text).ilike(pattern) | col(Item.target_text).ilike(pattern)
        )

    total = session.exec(count_stmt).one()
    items = session.exec(
        stmt.order_by(col(Item.sort_order).asc(), col(Item.created_at).desc())
        .offset(offset)
        .limit(limit)
    ).all()

    return ItemListOut(items=[_item_to_out(item) for item in items], total=total)


@router.post("/translate", response_model=TranslateResponse)
def translate_text(data: TranslateRequest, session: Session = Depends(get_session)):
    source_text = data.source_text.strip()
    if not source_text:
        raise ValidationError("source_text cannot be empty")
    settings = _get_settings(session)
    try:
        translator = get_translator()
        target_text = translator.translate(source_text, settings.source_lang, settings.target_lang)
    except ProviderError as e:
        raise ProviderAPIError("translator", str(e)) from e
    return TranslateResponse(target_text=target_text)


@router.post("/translate-back", response_model=TranslateBackResponse)
def translate_back(data: TranslateBackRequest, session: Session = Depends(get_session)):
    target_text = data.target_text.strip()
    if not target_text:
        raise ValidationError("target_text cannot be empty")
    settings = _get_settings(session)
    try:
        translator = get_translator()
        source_text = translator.translate(target_text, settings.target_lang, settings.source_lang)
    except ProviderError as e:
        raise ProviderAPIError("translator", str(e)) from e
    return TranslateBackResponse(source_text=source_text)


@router.post("/tts/preview")
def tts_preview(data: TtsPreviewRequest, session: Session = Depends(get_session)):
    text = data.text.strip()
    if not text:
        raise ValidationError("text cannot be empty")
    settings = _get_settings(session)
    try:
        tts = get_tts()
        voice_id = settings.tts_voice or None
        result = tts.synthesize(text, settings.target_lang, voice_id)
    except ProviderError as e:
        raise ProviderAPIError("tts", str(e)) from e
    return Response(content=result.audio_bytes, media_type=result.mime)


@router.post("/items/reorder", status_code=204)
def reorder_items(data: ReorderRequest, session: Session = Depends(get_session)):
    for idx, item_id in enumerate(data.item_ids):
        item = session.get(Item, item_id)
        if item:
            item.sort_order = idx
            session.add(item)
    session.commit()


@router.post("/items", response_model=ItemOut, status_code=201)
def create_item(data: ItemCreate, session: Session = Depends(get_session)):
    cfg = get_config()

    source_text = data.source_text.strip()
    if not source_text:
        raise ValidationError("source_text cannot be empty")
    if len(source_text) > cfg.max_source_chars:
        raise ValidationError(f"source_text exceeds {cfg.max_source_chars} characters")

    settings = _get_settings(session)

    # Resolve category
    category_id = data.category_id
    if data.category_name and not category_id:
        name = data.category_name.strip()
        if name:
            existing = session.exec(select(Category).where(Category.name == name)).first()
            if existing:
                category_id = existing.id
            else:
                cat = Category(name=name)
                session.add(cat)
                session.commit()
                session.refresh(cat)
                category_id = cat.id

    # Translate (skip if target_text already provided)
    if data.target_text:
        target_text = data.target_text.strip()
        if not target_text:
            raise ValidationError("target_text cannot be empty")
    else:
        try:
            translator = get_translator()
            target_text = translator.translate(
                source_text, settings.source_lang, settings.target_lang
            )
        except ProviderError as e:
            raise ProviderAPIError("translator", str(e)) from e

    # TTS
    audio_path = None
    audio_voice = None
    audio_provider = None
    try:
        tts = get_tts()
        voice_id = settings.tts_voice or None
        result = tts.synthesize(target_text, settings.target_lang, voice_id)
        audio_path = audio_store.save(result.audio_bytes, result.mime)
        audio_voice = result.voice_id
        audio_provider = tts.name
    except ProviderError:
        pass  # item created without audio; user can regenerate later

    # Assign sort_order: new items go to the top (lowest value)
    min_order = session.exec(select(func.min(Item.sort_order))).one()  # type: ignore[arg-type]
    new_order = (min_order or 0) - 1

    item = Item(
        category_id=category_id,
        source_lang=settings.source_lang,
        target_lang=settings.target_lang,
        source_text=source_text,
        target_text=target_text,
        sort_order=new_order,
        audio_path=audio_path,
        audio_voice=audio_voice,
        audio_provider=audio_provider,
        audio_stale=False,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return _item_to_out(item)


@router.get("/items/{item_id}", response_model=ItemOut)
def get_item(item_id: int, session: Session = Depends(get_session)):
    item = session.get(Item, item_id)
    if not item:
        raise NotFoundError("Item", item_id)
    return _item_to_out(item)


@router.patch("/items/{item_id}", response_model=ItemOut)
def update_item(item_id: int, data: ItemUpdate, session: Session = Depends(get_session)):
    item = session.get(Item, item_id)
    if not item:
        raise NotFoundError("Item", item_id)

    if data.target_text is not None:
        new_text = data.target_text.strip()
        if not new_text:
            raise ValidationError("target_text cannot be empty")
        if new_text != item.target_text:
            item.target_text = new_text
            item.audio_stale = True

    if data.category_id is not None:
        # Allow setting to 0 or null to uncategorize
        if data.category_id == 0:
            item.category_id = None
        else:
            cat = session.get(Category, data.category_id)
            if not cat:
                raise NotFoundError("Category", data.category_id)
            item.category_id = data.category_id

    item.updated_at = datetime.now(UTC)
    session.add(item)
    session.commit()
    session.refresh(item)
    return _item_to_out(item)


@router.post("/items/{item_id}/regenerate-audio", response_model=ItemOut)
def regenerate_audio(item_id: int, session: Session = Depends(get_session)):
    item = session.get(Item, item_id)
    if not item:
        raise NotFoundError("Item", item_id)

    # Delete old audio
    if item.audio_path:
        audio_store.delete(item.audio_path)

    try:
        tts = get_tts()
        settings = _get_settings(session)
        voice_id = settings.tts_voice or None
        result = tts.synthesize(item.target_text, item.target_lang, voice_id)
        item.audio_path = audio_store.save(result.audio_bytes, result.mime)
        item.audio_voice = result.voice_id
        item.audio_provider = tts.name
        item.audio_stale = False
    except ProviderError as e:
        raise ProviderAPIError("tts", str(e)) from e

    item.updated_at = datetime.now(UTC)
    session.add(item)
    session.commit()
    session.refresh(item)
    return _item_to_out(item)


@router.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int, session: Session = Depends(get_session)):
    item = session.get(Item, item_id)
    if not item:
        raise NotFoundError("Item", item_id)
    if item.audio_path:
        audio_store.delete(item.audio_path)
    session.delete(item)
    session.commit()


@router.get("/items/{item_id}/audio")
def get_audio(item_id: int, download: int = 0, session: Session = Depends(get_session)):
    item = session.get(Item, item_id)
    if not item:
        raise NotFoundError("Item", item_id)
    if not item.audio_path:
        raise AudioMissingError(item_id)

    path = audio_store.get_absolute_path(item.audio_path)
    if not path.exists():
        raise AudioMissingError(item_id)

    filename = f"myglot-{item_id}.mp3"
    if download:
        return FileResponse(
            path,
            media_type="audio/mpeg",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    return FileResponse(path, media_type="audio/mpeg")


@router.post("/items/{item_id}/practice", response_model=PracticeResult)
async def practice(
    item_id: int, audio: UploadFile = File(...), session: Session = Depends(get_session)
):
    item = session.get(Item, item_id)
    if not item:
        raise NotFoundError("Item", item_id)

    cfg = get_config()
    audio_bytes = await audio.read()
    if len(audio_bytes) > cfg.max_audio_upload_bytes:
        raise ValidationError(
            f"Audio file too large (max {cfg.max_audio_upload_bytes // (1024 * 1024)} MB)"
        )

    mime = audio.content_type or "audio/webm"

    try:
        stt = get_stt()
        stt_result = stt.transcribe(audio_bytes, mime, item.target_lang)
    except ProviderError as e:
        raise ProviderAPIError("stt", str(e)) from e

    score_result = similarity.score(item.target_text, stt_result.transcript)

    return PracticeResult(
        transcript=stt_result.transcript,
        score=score_result.score,
        diff=score_result.diff,
    )
