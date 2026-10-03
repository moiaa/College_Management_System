Техническое задание: Backend — Модуль «Отчёты»

1. Описание
API для генерации сводных таблиц успеваемости, статистики посещаемости
и выгрузки данных для администрации и преподавателей.
Стек: Python / FastAPI, PostgreSQL.

2. Модель данных
- `Report`: id, type, status (pending/ready/failed), file_path, created_by, created_at
- `ReportFilter`: id, report_id, params (JSON)

3. API Endpoints (контракт с Frontend, Issue #22)

GET /api/v1/reports
Список отчётов текущего пользователя.
Query: type (performance | attendance), status (ready | generating)

POST /api/v1/reports/generate
Запуск генерации отчёта.
Пример тела запроса:
{"type": "attendance", "filters": {"groupId": 101, "from": "2026-09-01", "to": "2026-09-30"}}
Ответ: 202 Accepted, {"jobId": "...", "status": "generating"}

/api/v1/reports/{reportId}/download
Скачивание готового файла (PDF/Excel).
