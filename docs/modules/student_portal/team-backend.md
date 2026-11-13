# Команда: Student Portal Backend

## 👥 Участники

| ФИО | Роль | GitHub | Email / Telegram |
|-----|------|--------|------------------|
| Чекменев Илья | Team Lead / Backend Developer | [@ggvrednula-ship-it](https://github.com/ggvrednula-ship-it) | — |
| Кондрашов Даниил | Backend Developer | [@danilkond08-hub](https://github.com/danilkond08-hub) | — |

## 🎯 Модуль

**Название:** Student Portal — Кабинет студента

**Часть:** Backend (Python / FastAPI, `modules/student_portal/`)

**Описание:** REST API личного кабинета студента: вход по логину и паролю, профиль, список курсов, расписание на неделю, оценки и задолженности, посещаемость, объявления группы, заказ справок в деканате и загрузка учебных работ на проверку. Оценки, расписание и посещаемость модуль только читает из общих таблиц `core/`; собственные данные модуля — записи студентов на курсы, заявки на справки и загруженные работы.

## 📅 Дедлайны

- **Контрольная точка 1 (Модуль 1):** ТЗ `specification-backend.md` и согласованный с frontend-командой (issue #11) раздел 4.1 API
- **Контрольная точка 2 (Модуль 2):** реализация эндпоинтов из раздела 4.1 в `modules/student_portal/` с тестами, зелёный CI
- **Финальная защита (Модуль 3):** интеграция с `frontend/student_portal/`, защита модуля

Точные даты — по графику учебного курса.

## 📝 Заметки

- Issue команды: #12 (Module: Student Portal — Backend). Frontend-команда модуля: issue #11.
- Ветки: `student-portal-backend/<задача>`, PR — в `main` (см. wiki «Git и GitHub»).
- Раздел 4.1 ТЗ сверяем с `specification-frontend.md` по чек-листу из wiki «API-контракт» до начала Модуля 2.
