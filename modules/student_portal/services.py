"""Чтение данных и расчёты для кабинета студента.

Оценки, посещаемость и расписание (таблицы core/) модуль только читает.
Группа студента (users.group_id, student_groups — Admin Panel) и
объявления (announcements — Teacher Portal) читаются, только если эти
таблицы уже есть в БД: пока модулей-владельцев нет, кабинет просто
отдаёт пустые значения.
"""
from datetime import date, datetime, time, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, inspect, text
from sqlalchemy.orm import Session, joinedload

from core.models import Attendance, Course, Grade, Schedule, User
from core.utils import calculate_gpa

from .constants import (
    ACTIVE_CERTIFICATE_STATUSES, CERTIFICATE_TYPES, DAY_ORDER, LATEST_ANNOUNCEMENTS_LIMIT,
    PASSING_GRADE, AttendanceStatus, CourseStatus, DayOfWeek, SubmissionStatus,
)
from .models import CertificateRequest, StudentCourse, StudentSubmission


# --- Таблицы других модулей ---------------------------------------------------


def _has_table(db: Session, table: str) -> bool:
    return inspect(db.connection()).has_table(table)


def _has_column(db: Session, table: str, column: str) -> bool:
    inspector = inspect(db.connection())
    if not inspector.has_table(table):
        return False
    return any(info["name"] == column for info in inspector.get_columns(table))


def get_group(db: Session, user: User) -> Tuple[Optional[int], Optional[str]]:
    """Группа студента: (group_id, group_name) или (None, None)."""
    if not _has_column(db, "users", "group_id"):
        return None, None
    group_id = db.execute(
        text("SELECT group_id FROM users WHERE id = :user_id"), {"user_id": user.id}
    ).scalar()
    if group_id is None:
        return None, None
    group_name = None
    if _has_table(db, "student_groups"):
        group_name = db.execute(
            text("SELECT name FROM student_groups WHERE id = :group_id"), {"group_id": group_id}
        ).scalar()
    return group_id, group_name


def get_announcements(
    db: Session, group_id: Optional[int], limit: int, offset: int = 0
) -> Tuple[List[dict], int]:
    """Объявления группы от новых к старым и их общее число."""
    if group_id is None or not _has_table(db, "announcements"):
        return [], 0
    params = {"group_id": group_id, "limit": limit, "offset": offset}
    total = db.execute(
        text("SELECT COUNT(*) FROM announcements WHERE group_id = :group_id"), params
    ).scalar()
    rows = db.execute(
        text(
            "SELECT a.id, a.title, a.text, a.created_at, a.updated_at, "
            "u.full_name AS teacher_name "
            "FROM announcements a LEFT JOIN users u ON u.id = a.teacher_id "
            "WHERE a.group_id = :group_id "
            "ORDER BY a.created_at DESC, a.id DESC LIMIT :limit OFFSET :offset"
        ),
        params,
    ).mappings().all()
    return [dict(row) for row in rows], total


def profile_to_dict(db: Session, user: User) -> dict:
    group_id, group_name = get_group(db, user)
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "group_id": group_id,
        "group_name": group_name,
        "created_at": user.created_at,
    }


# --- Курсы и расписание --------------------------------------------------------


def is_enrolled(db: Session, student_id: int, course_id: int) -> bool:
    return db.query(StudentCourse.id).filter(
        StudentCourse.student_id == student_id, StudentCourse.course_id == course_id
    ).first() is not None


def list_courses(
    db: Session, student_id: int, semester: Optional[str] = None, course_id: Optional[int] = None
) -> List[Course]:
    query = (
        db.query(Course)
        .join(StudentCourse, StudentCourse.course_id == Course.id)
        .filter(StudentCourse.student_id == student_id)
        .options(joinedload(Course.teacher))
    )
    if semester:
        query = query.filter(Course.semester == semester)
    if course_id is not None:
        query = query.filter(Course.id == course_id)
    return query.order_by(Course.title, Course.id).all()


def _teacher_name(course: Course) -> Optional[str]:
    return course.teacher.full_name if course.teacher else None


def course_to_dict(course: Course) -> dict:
    teacher = course.teacher
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "semester": course.semester,
        "credits": course.credits,
        "teacher": {"id": teacher.id, "full_name": teacher.full_name} if teacher else None,
    }


def list_lessons(db: Session, student_id: int, day: Optional[str] = None) -> List[dict]:
    query = (
        db.query(Schedule)
        .join(StudentCourse, StudentCourse.course_id == Schedule.course_id)
        .filter(StudentCourse.student_id == student_id)
        .options(joinedload(Schedule.course).joinedload(Course.teacher))
    )
    if day:
        query = query.filter(func.lower(Schedule.day_of_week) == day)
    lessons = query.all()
    lessons.sort(
        key=lambda lesson: (
            DAY_ORDER.get(lesson.day_of_week.lower(), len(DAY_ORDER)),
            lesson.time_start,
            lesson.id,
        )
    )
    return [
        {
            "id": lesson.id,
            "day_of_week": lesson.day_of_week.lower(),
            "time_start": lesson.time_start,
            "time_end": lesson.time_end,
            "room": lesson.room,
            "building": lesson.building,
            "course_id": lesson.course_id,
            "course_title": lesson.course.title,
            "teacher_name": _teacher_name(lesson.course),
        }
        for lesson in lessons
    ]


# --- Оценки ------------------------------------------------------------------------


def course_status(average: Optional[float]) -> CourseStatus:
    if average is None:
        return CourseStatus.IN_PROGRESS
    if average < PASSING_GRADE:
        return CourseStatus.DEBT
    return CourseStatus.PASSED


def grades_report(
    db: Session, student_id: int, semester: Optional[str] = None, course_id: Optional[int] = None
) -> dict:
    courses = list_courses(db, student_id, semester, course_id)
    grades_by_course: Dict[int, List[Grade]] = {course.id: [] for course in courses}
    if courses:
        grades = (
            db.query(Grade)
            .filter(Grade.student_id == student_id, Grade.course_id.in_(list(grades_by_course)))
            .order_by(Grade.graded_at, Grade.id)
            .all()
        )
        for grade in grades:
            grades_by_course[grade.course_id].append(grade)

    items = []
    all_values: List[float] = []
    debts_count = 0
    for course in courses:
        course_grades = grades_by_course[course.id]
        values = [grade.grade for grade in course_grades]
        all_values.extend(values)
        average = calculate_gpa(values) if values else None
        status = course_status(average)
        if status == CourseStatus.DEBT:
            debts_count += 1
        items.append({
            "course_id": course.id,
            "course_title": course.title,
            "semester": course.semester,
            "credits": course.credits,
            "teacher_name": _teacher_name(course),
            "grades": [
                {
                    "id": grade.id,
                    "grade": grade.grade,
                    "comment": grade.comment,
                    "graded_at": grade.graded_at,
                }
                for grade in course_grades
            ],
            "average": average,
            "status": status,
        })
    return {
        "items": items,
        "total": len(items),
        "average": calculate_gpa(all_values) if all_values else None,
        "debts_count": debts_count,
    }


# --- Посещаемость ------------------------------------------------------------------


def _period_filters(date_from: Optional[date], date_to: Optional[date]) -> list:
    filters = []
    if date_from is not None:
        filters.append(Attendance.date >= datetime.combine(date_from, time.min))
    if date_to is not None:
        filters.append(Attendance.date < datetime.combine(date_to + timedelta(days=1), time.min))
    return filters


def _counters(counts: Dict[str, int]) -> dict:
    total = sum(counts.values())
    present = counts.get(AttendanceStatus.PRESENT.value, 0)
    late = counts.get(AttendanceStatus.LATE.value, 0)
    return {
        "total": total,
        "present": present,
        "late": late,
        "absent": counts.get(AttendanceStatus.ABSENT.value, 0),
        "excused": counts.get(AttendanceStatus.EXCUSED.value, 0),
        "attendance_percent": round((present + late) / total * 100, 1) if total else None,
    }


def attendance_report(
    db: Session,
    student_id: int,
    semester: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> dict:
    courses = list_courses(db, student_id, semester)
    counts_by_course: Dict[int, Dict[str, int]] = {course.id: {} for course in courses}
    if courses:
        status_lower = func.lower(Attendance.status)
        rows = (
            db.query(Attendance.course_id, status_lower, func.count(Attendance.id))
            .filter(
                Attendance.student_id == student_id,
                Attendance.course_id.in_(list(counts_by_course)),
                *_period_filters(date_from, date_to),
            )
            .group_by(Attendance.course_id, status_lower)
            .all()
        )
        for course_id, status, count in rows:
            counts_by_course[course_id][status] = count

    overall: Dict[str, int] = {}
    items = []
    for course in courses:
        counts = counts_by_course[course.id]
        for status, count in counts.items():
            overall[status] = overall.get(status, 0) + count
        items.append({"course_id": course.id, "course_title": course.title, **_counters(counts)})
    return {"items": items, "total": len(items), "overall": _counters(overall)}


def attendance_records(
    db: Session,
    student_id: int,
    offset: int,
    limit: int,
    course_id: Optional[int] = None,
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> Tuple[List[dict], int]:
    query = (
        db.query(Attendance, Course.title)
        .join(Course, Course.id == Attendance.course_id)
        .join(
            StudentCourse,
            (StudentCourse.course_id == Attendance.course_id)
            & (StudentCourse.student_id == student_id),
        )
        .filter(Attendance.student_id == student_id, *_period_filters(date_from, date_to))
    )
    if course_id is not None:
        query = query.filter(Attendance.course_id == course_id)
    if status is not None:
        query = query.filter(func.lower(Attendance.status) == status)
    total = query.count()
    rows = (
        query.order_by(Attendance.date.desc(), Attendance.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    items = [
        {
            "id": record.id,
            "date": record.date.date(),
            "course_id": record.course_id,
            "course_title": course_title,
            "status": record.status.lower(),
            "comment": record.comment,
        }
        for record, course_title in rows
    ]
    return items, total


# --- Справки и работы --------------------------------------------------------------


def certificate_to_dict(request: CertificateRequest, with_student: bool = False) -> dict:
    data = {
        "id": request.id,
        "type": request.cert_type,
        "type_name": CERTIFICATE_TYPES.get(request.cert_type, {}).get("name", request.cert_type),
        "copies": request.copies,
        "delivery": request.delivery,
        "comment": request.comment,
        "status": request.status,
        "status_comment": request.status_comment,
        "has_file": bool(request.file_path),
        "created_at": request.created_at,
        "updated_at": request.updated_at,
    }
    if with_student:
        data["student"] = {"id": request.student.id, "full_name": request.student.full_name}
    return data


def submission_to_dict(submission: StudentSubmission, with_student: bool = False) -> dict:
    data = {
        "id": submission.id,
        "course_id": submission.course_id,
        "course_title": submission.course.title,
        "work_type": submission.work_type,
        "title": submission.title,
        "version": submission.version,
        "file_name": submission.file_name,
        "file_size": submission.file_size,
        "status": submission.status,
        "teacher_comment": submission.teacher_comment,
        "reviewed_at": submission.reviewed_at,
        "created_at": submission.created_at,
    }
    if with_student:
        data["student"] = {"id": submission.student.id, "full_name": submission.student.full_name}
    return data


def work_key(title: str) -> str:
    """Название работы для сравнения версий: без пробелов по краям и регистра."""
    return title.strip().casefold()


def latest_versions(db: Session, student_id: int) -> List[StudentSubmission]:
    """Последняя версия каждой работы студента (работа = курс + название)."""
    latest: Dict[Tuple[int, str], StudentSubmission] = {}
    submissions = db.query(StudentSubmission).filter(
        StudentSubmission.student_id == student_id
    ).all()
    for submission in submissions:
        key = (submission.course_id, work_key(submission.title))
        if key not in latest or submission.version > latest[key].version:
            latest[key] = submission
    return list(latest.values())


# --- Главная страница --------------------------------------------------------------


def dashboard(db: Session, student: User, today: date) -> dict:
    day = list(DayOfWeek)[today.weekday()].value
    grades = grades_report(db, student.id)
    attendance = attendance_report(db, student.id)
    active_requests = db.query(func.count(CertificateRequest.id)).filter(
        CertificateRequest.student_id == student.id,
        CertificateRequest.status.in_(ACTIVE_CERTIFICATE_STATUSES),
    ).scalar()
    latest = latest_versions(db, student.id)
    group_id, _ = get_group(db, student)
    announcements, _ = get_announcements(db, group_id, LATEST_ANNOUNCEMENTS_LIMIT)
    return {
        "date": today,
        "day_of_week": day,
        "today_lessons": list_lessons(db, student.id, day),
        "average_grade": grades["average"],
        "debts_count": grades["debts_count"],
        "attendance_percent": attendance["overall"]["attendance_percent"],
        "active_certificate_requests": active_requests,
        "submissions_on_review": sum(
            1 for item in latest if item.status == SubmissionStatus.SUBMITTED.value
        ),
        "submissions_need_revision": sum(
            1 for item in latest if item.status == SubmissionStatus.REVISION.value
        ),
        "latest_announcements": announcements,
    }
