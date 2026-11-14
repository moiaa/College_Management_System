"""Курсы, расписание, оценки, посещаемость, объявления и главная страница."""
from datetime import date, datetime

from sqlalchemy import text

from core.models import UserRole
from modules.student_portal.constants import DayOfWeek
from modules.student_portal.models import CertificateRequest, StudentSubmission

from .conftest import API


def test_courses_lists_only_enrolled_sorted_by_title(client, factory, student, teacher, auth):
    networks = factory.course(teacher, "Компьютерные сети", semester="2026-1")
    modules = factory.course(teacher, "Разработка программных модулей", semester="2026-1")
    old = factory.course(teacher, "Архитектура ЭВМ", semester="2025-2")
    factory.course(teacher, "Чужой курс")
    factory.enroll(student, modules, networks, old)

    response = client.get(f"{API}/courses", headers=auth)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert [item["title"] for item in body["items"]] == [
        "Архитектура ЭВМ", "Компьютерные сети", "Разработка программных модулей",
    ]
    assert body["items"][1]["teacher"] == {"id": teacher.id, "full_name": "Петров Пётр Петрович"}

    filtered = client.get(f"{API}/courses", params={"semester": "2025-2"}, headers=auth).json()
    assert [item["id"] for item in filtered["items"]] == [old.id]


def test_schedule_is_sorted_and_filtered_by_day(client, factory, student, teacher, auth):
    course = factory.course(teacher, "Разработка программных модулей")
    other = factory.course(teacher, "Не мой курс")
    factory.enroll(student, course)
    factory.lesson(course, "wednesday", "10:40", "12:10")
    factory.lesson(course, "monday", "12:30", "14:00", room="305", building="Главный корпус")
    factory.lesson(course, "monday", "09:00", "10:30")
    factory.lesson(other, "monday", "08:00", "09:30")

    body = client.get(f"{API}/schedule", headers=auth).json()

    assert body["total"] == 3
    assert [(item["day_of_week"], item["time_start"]) for item in body["items"]] == [
        ("monday", "09:00"), ("monday", "12:30"), ("wednesday", "10:40"),
    ]
    lesson = body["items"][1]
    assert lesson["room"] == "305"
    assert lesson["building"] == "Главный корпус"
    assert lesson["course_title"] == "Разработка программных модулей"
    assert lesson["teacher_name"] == "Петров Пётр Петрович"

    monday = client.get(f"{API}/schedule", params={"day_of_week": "monday"}, headers=auth)
    assert monday.json()["total"] == 2

    invalid = client.get(f"{API}/schedule", params={"day_of_week": "funday"}, headers=auth)
    assert invalid.status_code == 422


def test_grades_statuses_averages_and_debts(client, factory, student, teacher, auth):
    passed = factory.course(teacher, "А: сдано")
    debt = factory.course(teacher, "Б: задолженность")
    empty = factory.course(teacher, "В: без оценок", semester="2026-2")
    factory.enroll(student, passed, debt, empty)
    factory.grade(student, passed, 4.0, datetime(2026, 9, 20, 12, 0))
    factory.grade(student, passed, 5.0, datetime(2026, 10, 1, 12, 0), comment="Отлично")
    factory.grade(student, debt, 2.0)
    factory.grade(student, debt, 3.0)
    classmate = factory.user(UserRole.STUDENT)
    factory.enroll(classmate, passed)
    factory.grade(classmate, passed, 2.0)

    body = client.get(f"{API}/grades", headers=auth).json()

    assert body["total"] == 3
    assert body["average"] == 3.5
    assert body["debts_count"] == 1
    by_title = {item["course_title"]: item for item in body["items"]}
    assert by_title["А: сдано"]["average"] == 4.5
    assert by_title["А: сдано"]["status"] == "passed"
    assert [grade["grade"] for grade in by_title["А: сдано"]["grades"]] == [4.0, 5.0]
    assert by_title["А: сдано"]["grades"][1]["comment"] == "Отлично"
    assert by_title["А: сдано"]["grades"][0]["graded_at"] == "2026-09-20T12:00:00"
    assert by_title["Б: задолженность"]["average"] == 2.5
    assert by_title["Б: задолженность"]["status"] == "debt"
    assert by_title["В: без оценок"]["grades"] == []
    assert by_title["В: без оценок"]["average"] is None
    assert by_title["В: без оценок"]["status"] == "in_progress"

    one = client.get(f"{API}/grades", params={"course_id": passed.id}, headers=auth).json()
    assert one["total"] == 1
    assert one["debts_count"] == 0

    semester = client.get(f"{API}/grades", params={"semester": "2026-2"}, headers=auth).json()
    assert semester["total"] == 1
    assert semester["average"] is None


def test_attendance_summary_and_period(client, factory, student, teacher, auth):
    course = factory.course(teacher, "Разработка программных модулей")
    quiet = factory.course(teacher, "Курс без отметок")
    factory.enroll(student, course, quiet)
    for day, status in [(1, "present"), (2, "present"), (3, "present"), (4, "late"),
                        (5, "absent"), (20, "excused")]:
        factory.attendance(student, course, datetime(2026, 10, day, 9, 0), status)

    body = client.get(f"{API}/attendance", headers=auth).json()

    assert body["total"] == 2
    by_title = {item["course_title"]: item for item in body["items"]}
    counters = by_title["Разработка программных модулей"]
    assert counters["total"] == 6
    assert (counters["present"], counters["late"], counters["absent"], counters["excused"]) == (
        3, 1, 1, 1,
    )
    assert counters["attendance_percent"] == 66.7
    assert by_title["Курс без отметок"]["attendance_percent"] is None
    assert body["overall"]["total"] == 6

    period = client.get(
        f"{API}/attendance",
        params={"date_from": "2026-10-01", "date_to": "2026-10-05"},
        headers=auth,
    ).json()
    assert period["overall"]["total"] == 5
    assert period["overall"]["attendance_percent"] == 80.0

    reversed_period = client.get(
        f"{API}/attendance",
        params={"date_from": "2026-10-05", "date_to": "2026-10-01"},
        headers=auth,
    )
    assert reversed_period.status_code == 422
    assert isinstance(reversed_period.json()["detail"], list)


def test_attendance_records_filters_and_pagination(client, factory, student, teacher, auth):
    course = factory.course(teacher, "Разработка программных модулей")
    factory.enroll(student, course)
    for day in range(1, 6):
        factory.attendance(student, course, datetime(2026, 10, day, 9, 0), "absent")
    factory.attendance(student, course, datetime(2026, 10, 6, 9, 0), "present")
    classmate = factory.user(UserRole.STUDENT)
    factory.attendance(classmate, course, datetime(2026, 10, 7, 9, 0), "absent")

    page = client.get(
        f"{API}/attendance/records",
        params={"status": "absent", "page": 2, "page_size": 2},
        headers=auth,
    ).json()

    assert page["total"] == 5
    assert (page["page"], page["page_size"]) == (2, 2)
    assert [item["date"] for item in page["items"]] == ["2026-10-03", "2026-10-02"]
    assert page["items"][0]["course_title"] == "Разработка программных модулей"

    invalid = client.get(f"{API}/attendance/records", params={"status": "sick"}, headers=auth)
    assert invalid.status_code == 422
    too_big = client.get(f"{API}/attendance/records", params={"page_size": 101}, headers=auth)
    assert too_big.status_code == 422


def create_group_tables(db, student, teacher):
    """Таблицы Admin Panel и Teacher Portal в том виде, как они описаны в их ТЗ."""
    db.execute(text("CREATE TABLE student_groups (id INTEGER PRIMARY KEY, name VARCHAR(50))"))
    db.execute(text(
        "CREATE TABLE announcements (id INTEGER PRIMARY KEY, teacher_id INTEGER, "
        "group_id INTEGER, title VARCHAR(150), text TEXT, created_at DATETIME, "
        "updated_at DATETIME)"
    ))
    db.execute(text("ALTER TABLE users ADD COLUMN group_id INTEGER"))
    db.execute(text("INSERT INTO student_groups (id, name) VALUES (1, 'ИС-31'), (2, 'ИС-32')"))
    db.execute(text("UPDATE users SET group_id = 1 WHERE id = :id"), {"id": student.id})
    rows = [
        (1, "Перенос лекции", "2026-10-03 14:30:00"),
        (1, "Консультация", "2026-10-05 09:00:00"),
        (2, "Чужая группа", "2026-10-06 09:00:00"),
    ]
    for group_id, title, created_at in rows:
        db.execute(
            text(
                "INSERT INTO announcements (teacher_id, group_id, title, text, created_at, "
                "updated_at) VALUES (:teacher, :group, :title, 'Текст', :created, :created)"
            ),
            {"teacher": teacher.id, "group": group_id, "title": title, "created": created_at},
        )
    db.commit()


def test_announcements_empty_without_group_tables(client, auth):
    body = client.get(f"{API}/announcements", headers=auth).json()
    assert body == {"items": [], "total": 0, "page": 1, "page_size": 20}


def test_announcements_and_group_from_other_modules(client, db, student, teacher, auth):
    create_group_tables(db, student, teacher)

    body = client.get(f"{API}/announcements", headers=auth).json()

    assert body["total"] == 2
    assert [item["title"] for item in body["items"]] == ["Консультация", "Перенос лекции"]
    assert body["items"][1]["teacher_name"] == "Петров Пётр Петрович"
    assert body["items"][1]["created_at"] == "2026-10-03T14:30:00"

    profile = client.get(f"{API}/me", headers=auth).json()
    assert (profile["group_id"], profile["group_name"]) == (1, "ИС-31")


def test_dashboard_collects_summary(client, db, factory, student, teacher, auth):
    today = date.today()
    weekday = list(DayOfWeek)[today.weekday()].value
    other_day = list(DayOfWeek)[(today.weekday() + 1) % 7].value
    course = factory.course(teacher, "Разработка программных модулей")
    factory.enroll(student, course)
    factory.lesson(course, weekday, "09:00", "10:30")
    factory.lesson(course, other_day, "09:00", "10:30")
    factory.grade(student, course, 2.0)
    factory.attendance(student, course, datetime(2026, 10, 1, 9, 0), "present")
    factory.attendance(student, course, datetime(2026, 10, 2, 9, 0), "absent")
    db.add_all([
        CertificateRequest(student_id=student.id, cert_type="study", copies=1,
                           delivery="pdf", status="in_progress"),
        CertificateRequest(student_id=student.id, cert_type="tax_deduction", copies=1,
                           delivery="paper", status="ready"),
    ])
    common = dict(student_id=student.id, course_id=course.id, work_type="lab", file_name="f.pdf",
                  file_path="x.pdf", file_size=1, content_type="application/pdf")
    db.add_all([
        StudentSubmission(title="Лаба 1", version=1, status="revision", **common),
        StudentSubmission(title="Лаба 1", version=2, status="submitted", **common),
        StudentSubmission(title="Лаба 2", version=1, status="revision", **common),
        StudentSubmission(title="Лаба 3", version=1, status="accepted", **common),
    ])
    db.commit()
    create_group_tables(db, student, teacher)

    body = client.get(f"{API}/dashboard", headers=auth).json()

    assert body["date"] == today.isoformat()
    assert body["day_of_week"] == weekday
    assert len(body["today_lessons"]) == 1
    assert body["today_lessons"][0]["day_of_week"] == weekday
    assert body["average_grade"] == 2.0
    assert body["debts_count"] == 1
    assert body["attendance_percent"] == 50.0
    assert body["active_certificate_requests"] == 1
    assert body["submissions_on_review"] == 1
    assert body["submissions_need_revision"] == 1
    assert [item["title"] for item in body["latest_announcements"]] == [
        "Консультация", "Перенос лекции",
    ]


def test_dashboard_for_new_student_is_empty(client, auth):
    body = client.get(f"{API}/dashboard", headers=auth).json()

    assert body["today_lessons"] == []
    assert body["average_grade"] is None
    assert body["attendance_percent"] is None
    assert body["debts_count"] == 0
    assert body["latest_announcements"] == []
