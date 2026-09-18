"""FastAPI-приложение верхнего уровня.

Здесь регистрируются роутеры модулей. У каждого модуля свой APIRouter
(например modules/<ваш_модуль>/router.py) с префиксом /api/v1/<модуль>,
использующий core.database.get_db и свои модели/схемы. Команда,
разрабатывающая модуль, подключает свой роутер сюда одной строкой:

    from modules.<ваш_модуль>.router import router as <ваш_модуль>_router
    app.include_router(<ваш_модуль>_router)

Полный образец такого модуля (не один из 7 реальных, просто шаблон
паттерна) — в docs/examples/example_module/, читайте README.md рядом.
"""
from fastapi import FastAPI

from docs.examples.example_module.router import router as example_router

app = FastAPI(title="College Management System", version="0.1.0")

app.include_router(example_router)


@app.get("/health", tags=["system"])
def health_check():
    """Проверка, что сервис поднялся."""
    return {"status": "ok"}
