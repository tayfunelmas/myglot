from fastapi import APIRouter, Depends
from sqlmodel import Session, func, select

from ..db import get_session
from ..errors import NotFoundError, ValidationError
from ..models import Category, Item
from ..schemas import CategoryCreate, CategoryOut, CategoryUpdate

router = APIRouter(tags=["categories"])


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(session: Session = Depends(get_session)):
    # Get categories with item counts
    stmt = (
        select(Category, func.count(Item.id).label("item_count"))  # type: ignore[arg-type]
        .outerjoin(Item, Item.category_id == Category.id)  # type: ignore[arg-type]
        .group_by(Category.id)  # type: ignore[arg-type]
        .order_by(Category.name)
    )
    results = session.exec(stmt).all()
    return [
        CategoryOut(id=cat.id, name=cat.name, item_count=count, created_at=cat.created_at)  # type: ignore[arg-type]
        for cat, count in results
    ]


@router.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(data: CategoryCreate, session: Session = Depends(get_session)):
    name = data.name.strip()
    if not name:
        raise ValidationError("Category name cannot be empty")

    existing = session.exec(select(Category).where(Category.name == name)).first()
    if existing:
        raise ValidationError(f"Category '{name}' already exists")

    cat = Category(name=name)
    session.add(cat)
    session.commit()
    session.refresh(cat)
    return CategoryOut(id=cat.id, name=cat.name, item_count=0, created_at=cat.created_at)  # type: ignore[arg-type]


@router.patch("/categories/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int, data: CategoryUpdate, session: Session = Depends(get_session)
):
    cat = session.get(Category, category_id)
    if not cat:
        raise NotFoundError("Category", category_id)

    name = data.name.strip()
    if not name:
        raise ValidationError("Category name cannot be empty")

    existing = session.exec(
        select(Category).where(Category.name == name, Category.id != category_id)
    ).first()
    if existing:
        raise ValidationError(f"Category '{name}' already exists")

    cat.name = name
    session.add(cat)
    session.commit()
    session.refresh(cat)

    count = session.exec(select(func.count(Item.id)).where(Item.category_id == category_id)).one()  # type: ignore[arg-type]
    return CategoryOut(id=cat.id, name=cat.name, item_count=count, created_at=cat.created_at)  # type: ignore[arg-type]


@router.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: int, session: Session = Depends(get_session)):
    cat = session.get(Category, category_id)
    if not cat:
        raise NotFoundError("Category", category_id)

    # Items become uncategorized (SQLite ON DELETE SET NULL handles this,
    # but SQLModel doesn't always emit that, so do it manually)
    items = session.exec(select(Item).where(Item.category_id == category_id)).all()
    for item in items:
        item.category_id = None
        session.add(item)

    session.delete(cat)
    session.commit()
