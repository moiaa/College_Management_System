# Архитектура системы

## Слои

1. **Core Layer** (`core/`) — общее для всех модулей: подключение к БД
   (`database.py`), базовые ORM-модели (`models.py`), аутентификация
   (`auth.py`), конфиг (`config.py`).
2. **Module Layer** (`modules/<название>/`) — код конкретного модуля
   (Gradebook, Curriculum, Schedule, Reports, Student Portal, Teacher
   Portal, Admin Panel): свои ORM-модели, Pydantic-схемы и роутер.
3. **API Layer** (`core/api.py`) — общее FastAPI-приложение. Каждый
   модуль подключает свой роутер сюда одной строкой:

   ```python
   from modules.<название>.router import router as <название>_router
   app.include_router(<название>_router)
   ```

## Как модуль подключается к системе

Полный рабочий пример такого подключения (модель + схемы + роутер +
тесты) лежит в `docs/examples/example_module/` — это не один из 7
реальных модулей, а шаблон-образец, который можно скопировать в
`modules/<ваш_модуль>/` и адаптировать под свою сущность. Подробности —
в README.md рядом с примером.

Если модуль определяет собственную ORM-модель, `core/database.init_db()`
подхватит её автоматически при следующем `python main.py init` — при
условии, что роутер модуля уже подключён в `core/api.py` (импорт
роутера тянет за собой импорт модели).

## Запуск

```bash
python main.py init   # создать БД и таблицы всех подключённых модулей
python main.py run    # поднять API на http://127.0.0.1:8000
```
