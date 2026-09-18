"""API-роутер примера модуля.

Показывает общий паттерн для любого реального модуля:
1. APIRouter с префиксом /api/v1/<модуль>.
2. Сессия БД через Depends(get_db).
3. Модель из models.py этого модуля + общий core.database.Base/engine.
4. Схемы запроса/ответа из schemas.py.
5. HTTPException для ошибок (404 и т.п.).

Подробности и инструкция по копированию — в README.md рядом.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db

from .models import ExampleItem
from .schemas import ExampleItemCreate, ExampleItemOut

router = APIRouter(prefix="/api/v1/example", tags=["example"])


@router.get("/items", response_model=List[ExampleItemOut])
def list_items(db: Session = Depends(get_db)):
    return db.query(ExampleItem).all()


@router.get("/items/{item_id}", response_model=ExampleItemOut)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(ExampleItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Не найдено")
    return item


@router.post("/items", response_model=ExampleItemOut, status_code=201)
def create_item(payload: ExampleItemCreate, db: Session = Depends(get_db)):
    item = ExampleItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
