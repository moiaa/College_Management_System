"""Демо-данные для кабинета студента.

Запуск (после python main.py init и python scripts/seed_data.py):

    python -m modules.student_portal.seed

Записывает пользователя student1 на три курса преподавателя teacher1 и
добавляет расписание, оценки, посещаемость и одну заявку на справку.
Пока модули Gradebook и Schedule не готовы, это позволяет frontend-команде
видеть на страницах реальные ответы API. Повторный запуск ничего не меняет.
"""
from datetime import datetime, timedelta

from core.database import SessionLocal, init_db
from core.models import Attendance, Course, Grade, Schedule, User

from .models import CertificateRequest, StudentCourse

COURSES = [
    ("Разработка программных модулей", "Проектирование и разработка модулей ИС", 4),
    ("Компьютерные сети", "Модель OSI, адресация, маршрутизация", 3),
    ("Иностранный язык в профессиональной деятельности", "Английский для IT", 2),
]
LESSONS = [
    (0, "monday", "09:00", "10:30", "305"),
    (0, "wednesday", "10:40", "12:10", "305"),
    (1, "tuesday", "09:00", "10:30", "214"),
    (1, "thursday", "12:30", "14:00", "214"),
    (2, "friday", "10:40", "12:10", "118"),
]
GRADES = {0: [5, 4, 5], 1: [3, 2, 2], 2: []}
ATTENDANCE = ["present", "present", "late", "absent", "present", "excused"]


def seed() -> None:
    init_db()
    db = SessionLocal()
    try:
        student = db.query(User).filter(User.username == "student1").first()
        teacher = db.query(User).filter(User.username == "teacher1").first()
        if student is None or teacher is None:
            print("Сначала выполните: python scripts/seed_data.py")
            return
        if db.query(StudentCourse).filter(StudentCourse.student_id == student.id).first():
            print("Демо-данные кабинета студента уже есть")
            return

        courses = [
            Course(title=title, description=description, teacher_id=teacher.id,
                   semester="2026-1", credits=credits)
            for title, description, credits in COURSES
        ]
        db.add_all(courses)
        db.flush()
        db.add_all(StudentCourse(student_id=student.id, course_id=course.id) for course in courses)
        db.add_all(
            Schedule(course_id=courses[index].id, day_of_week=day, time_start=start,
                     time_end=end, room=room, building="Главный корпус")
            for index, day, start, end, room in LESSONS
        )
        start_day = datetime(2026, 9, 7, 9, 0)
        for index, values in GRADES.items():
            db.add_all(
                Grade(student_id=student.id, course_id=courses[index].id, grade=value,
                      graded_at=start_day + timedelta(days=7 * number), graded_by=teacher.id)
                for number, value in enumerate(values)
            )
        for index in GRADES:
            db.add_all(
                Attendance(student_id=student.id, course_id=courses[index].id,
                           date=start_day + timedelta(days=7 * number), status=status)
                for number, status in enumerate(ATTENDANCE)
            )
        db.add(CertificateRequest(student_id=student.id, cert_type="study", copies=1,
                                  delivery="paper", status="in_progress"))
        db.commit()
        print("✅ Демо-данные кабинета студента добавлены (логин student1 / student123)")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
