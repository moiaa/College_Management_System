"""Pydantic-схемы для примера модуля (см. README.md рядом)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ExampleItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    created_at: datetime


class ExampleItemCreate(BaseModel):
    text: str
