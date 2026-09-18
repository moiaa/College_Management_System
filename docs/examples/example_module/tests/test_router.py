"""Тест-образец: как проверять свой роутер, не трогая боевую college.db.

Подменяем зависимость get_db на сессию к in-memory SQLite. StaticPool
обязателен: без него каждая новая сессия к sqlite:///:memory: получает
свою пустую базу.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.api import app
from core.database import Base, get_db

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_create_and_list_item():
    response = client.post("/api/v1/example/items", json={"text": "Первая запись"})
    assert response.status_code == 201
    item_id = response.json()["id"]

    response = client.get(f"/api/v1/example/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["text"] == "Первая запись"

    response = client.get("/api/v1/example/items")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_missing_item_returns_404():
    response = client.get("/api/v1/example/items/999")
    assert response.status_code == 404
