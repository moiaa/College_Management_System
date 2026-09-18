"""Игрушечная модель для примера модуля (см. README.md рядом)."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from core.database import Base


class ExampleItem(Base):
    """Демонстрационная сущность — не часть реальной доменной модели."""

    __tablename__ = "example_items"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
