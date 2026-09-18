"""FastAPI-приложение верхнего уровня.

Здесь регистрируются роутеры модулей. У каждого модуля свой APIRouter
(например modules/<ваш_модуль>/router.py) с префиксом /api/v1/<модуль>,
использующий core.database.get_db и свои модели/схемы. Backend-команда
подключает свой роутер сюда одной строкой:

    from modules.<ваш_модуль>.router import router as <ваш_модуль>_router
    app.include_router(<ваш_модуль>_router)

Полный образец такого модуля (не один из 7 реальных, просто шаблон
паттерна) — в docs/examples/example_module/, читайте README.md рядом.

Фронтенд (обычный HTML/CSS/JS, без сборки) раздаётся этим же
приложением из папки frontend/ — см. frontend/README.md. CORS включён
на всякий случай (например, если кто-то откроет страницу напрямую как
файл или через отдельный dev-сервер), но в норме страницы обращаются к
API с того же origin (http://127.0.0.1:8000/...), так что CORS даже не
понадобится.
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from docs.examples.example_module.router import router as example_router

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="College Management System", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(example_router)


@app.get("/health", tags=["system"])
def health_check():
    """Проверка, что сервис поднялся."""
    return {"status": "ok"}


# Раздаём frontend/ как статику. html=True — значит, что
# /frontend/<модуль>/ автоматически отдаёт index.html из этой папки.
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
