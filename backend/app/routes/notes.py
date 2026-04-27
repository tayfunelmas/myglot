from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlmodel import Session, col, select

from ..db import get_session
from ..errors import NotFoundError, ValidationError
from ..models import Note
from ..schemas import NoteCreate, NoteOut, NoteUpdate

router = APIRouter(tags=["notes"])


@router.get("/notes", response_model=list[NoteOut])
def list_notes(session: Session = Depends(get_session)):
    stmt = select(Note).order_by(col(Note.created_at).desc())
    notes = session.exec(stmt).all()
    return notes


@router.post("/notes", response_model=NoteOut, status_code=201)
def create_note(data: NoteCreate, session: Session = Depends(get_session)):
    title = data.title.strip()
    if not title:
        raise ValidationError("Note title cannot be empty")
    note = Note(title=title, body=data.body)
    session.add(note)
    session.commit()
    session.refresh(note)
    return note


@router.get("/notes/{note_id}", response_model=NoteOut)
def get_note(note_id: int, session: Session = Depends(get_session)):
    note = session.get(Note, note_id)
    if not note:
        raise NotFoundError("Note", note_id)
    return note


@router.patch("/notes/{note_id}", response_model=NoteOut)
def update_note(note_id: int, data: NoteUpdate, session: Session = Depends(get_session)):
    note = session.get(Note, note_id)
    if not note:
        raise NotFoundError("Note", note_id)
    if data.title is not None:
        title = data.title.strip()
        if not title:
            raise ValidationError("Note title cannot be empty")
        note.title = title
    if data.body is not None:
        note.body = data.body
    note.updated_at = datetime.now(UTC)
    session.add(note)
    session.commit()
    session.refresh(note)
    return note


@router.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int, session: Session = Depends(get_session)):
    note = session.get(Note, note_id)
    if not note:
        raise NotFoundError("Note", note_id)
    session.delete(note)
    session.commit()
