# Пример модуля (образец, не для копирования "как есть")

Это **не восьмой модуль системы** и не задание ни для одной из команд —
это шаблон, показывающий, как модуль должен быть устроен технически,
чтобы подключиться к общему API (см. `core/api.py` и `docs/architecture.md`).

Используется игрушечная сущность `ExampleItem`, не связанная ни с одним
из 7 реальных модулей (Gradebook, Curriculum, Schedule, Reports,
Student Portal, Teacher Portal, Admin Panel), чтобы не выполнять чужую
работу — только показать паттерн.

## Из чего состоит модуль

- `models.py` — SQLAlchemy-модель (своя таблица, использует общий `Base`
  и `engine` из `core.database`).
- `schemas.py` — Pydantic-схемы запросов/ответов.
- `router.py` — `APIRouter` с префиксом `/api/v1/<модуль>`, получает
  сессию БД через `Depends(get_db)`, обрабатывает ошибки через
  `HTTPException`.
- `tests/test_router.py` — тест на FastAPI `TestClient` с подменой
  `get_db` на in-memory SQLite (`StaticPool`), чтобы тесты не трогали
  боевую `college.db`.

## Как использовать как команда

1. Скопируйте `models.py`, `schemas.py`, `router.py` и `tests/` к себе в
   `modules/<ваш_модуль>/`.
2. Замените `ExampleItem` на свою сущность (`Grade`, `ScheduleSlot`,
   и т.д. — как договоритесь в своём ТЗ).
3. Подключите свой роутер в `core/api.py`:
   ```python
   from modules.<ваш_модуль>.router import router as <ваш_модуль>_router
   app.include_router(<ваш_модуль>_router)
   ```
4. Напишите тесты по образцу `tests/test_router.py`.

Пример подключён в `core/api.py`, чтобы `python main.py run` из коробки
показывал рабочий пример. Когда у модулей появятся собственные роутеры,
эту строку подключения можно убрать.
