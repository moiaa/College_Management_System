# Модуль: Кабинет студента (Student Portal) — backend

REST API личного кабинета студента: `/api/v1/student_portal/...`.
Контракт (пути, параметры, примеры JSON, ошибки) — раздел 4.1 ТЗ
`docs/modules/student_portal/specification-backend.md`.

## Структура

| Файл | Что внутри |
|---|---|
| `constants.py` | Статусы, каталог справок, лимиты файлов |
| `models.py` | Таблицы модуля: `student_courses`, `certificate_requests`, `student_submissions` |
| `schemas.py` | Pydantic-схемы запросов и ответов |
| `dependencies.py` | Текущий пользователь по JWT, проверка роли, пагинация |
| `services.py` | Чтение оценок, посещаемости, расписания, группы и объявлений; расчёты |
| `storage.py` | Сохранение и выдача загруженных файлов |
| `router.py` | Эндпоинты кабинета студента (роль `student`) |
| `staff.py` | Служебные эндпоинты: деканат (`admin`) и проверка работ (`teacher`) |
| `seed.py` | Демо-данные для ручной проверки |
| `tests/` | Тесты на `TestClient` с in-memory SQLite |

Оценки, посещаемость и расписание модуль только читает из таблиц `core/`.
Группа студента (`users.group_id`, `student_groups`) и объявления
(`announcements`) читаются, только если эти таблицы уже созданы модулями
Admin Panel и Teacher Portal; до этого API отдаёт `null` и пустые списки.

## Запуск

```bash
pip install -r requirements.txt
python main.py init
python scripts/seed_data.py               # пользователи admin / teacher1 / student1
python -m modules.student_portal.seed     # курсы, расписание, оценки, посещаемость
python main.py run
```

Swagger UI: `http://127.0.0.1:8000/docs`. Чтобы вызвать эндпоинты оттуда,
получите токен через `POST /api/v1/student_portal/auth/login`
(`student1` / `student123`) и вставьте его в кнопку **Authorize**.

Файлы работ и справок сохраняются в `uploads/student_portal/` (папка в
`.gitignore`); путь можно поменять переменной окружения
`STUDENT_PORTAL_UPLOAD_DIR`.

## Тесты

```bash
pytest modules/student_portal/tests
flake8 modules/student_portal
```
