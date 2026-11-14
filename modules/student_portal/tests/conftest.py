"""Общие фикстуры тестов кабинета студента.

Как и в docs/examples/example_module/tests, get_db подменяется сессией к
in-memory SQLite (StaticPool). Подмена ставится в фикстуре и снимается
после теста, чтобы не мешать тестам других модулей. Загруженные файлы
пишутся во временную папку pytest.
"""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.api import app
from core.auth import create_access_token, get_password_hash
from core.database import Base, get_db
from core.models import Attendance, Course, Grade, Schedule, User, UserRole
from modules.student_portal.models import StudentCourse

PASSWORD = "secret123"
API = "/api/v1/student_portal"
PDF_BYTES = b"%PDF-1.4\n% test document\n%%EOF\n"
DOCX_BYTES = b"PK\x03\x04" + b"\x00" * 64

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

EXTRA_TABLES = ("announcements", "student_groups")


@pytest.fixture(scope="session")
def password_hash():
    return get_password_hash(PASSWORD)


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("STUDENT_PORTAL_UPLOAD_DIR", str(tmp_path / "uploads"))
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    with engine.begin() as connection:
        for table in EXTRA_TABLES:
            connection.exec_driver_sql(f"DROP TABLE IF EXISTS {table}")
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    if previous is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous


class Factory:
    """Создаёт тестовые данные прямо в БД."""

    def __init__(self, db, password_hash):
        self.db = db
        self.password_hash = password_hash
        self.counter = 0

    def _save(self, obj):
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def user(self, role=UserRole.STUDENT, username=None, full_name=None, is_active=True):
        self.counter += 1
        username = username or f"{role.value}{self.counter}"
        return self._save(User(
            username=username,
            email=f"{username}@college.test",
            hashed_password=self.password_hash,
            full_name=full_name or f"Пользователь {self.counter}",
            role=role,
            is_active=is_active,
        ))

    def course(self, teacher, title="Курс", semester="2026-1", credits=3):
        return self._save(Course(
            title=title, description=f"Описание: {title}", teacher_id=teacher.id,
            semester=semester, credits=credits,
        ))

    def enroll(self, student, *courses):
        for course in courses:
            self._save(StudentCourse(student_id=student.id, course_id=course.id))

    def lesson(self, course, day, start, end, room="101", building=None):
        return self._save(Schedule(
            course_id=course.id, day_of_week=day, time_start=start, time_end=end,
            room=room, building=building,
        ))

    def grade(self, student, course, value, graded_at=None, comment=None):
        return self._save(Grade(
            student_id=student.id, course_id=course.id, grade=value, comment=comment,
            graded_at=graded_at or datetime(2026, 10, 1, 12, 0) + timedelta(minutes=self.counter),
        ))

    def attendance(self, student, course, when, status, comment=None):
        self.counter += 1
        return self._save(Attendance(
            student_id=student.id, course_id=course.id, date=when, status=status,
            comment=comment,
        ))

    @staticmethod
    def headers(user, expires_delta=None):
        token = create_access_token(
            {"sub": str(user.id), "role": user.role.value}, expires_delta=expires_delta
        )
        return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def factory(db, password_hash):
    return Factory(db, password_hash)


@pytest.fixture
def teacher(factory):
    return factory.user(UserRole.TEACHER, full_name="Петров Пётр Петрович")


@pytest.fixture
def admin(factory):
    return factory.user(UserRole.ADMIN, full_name="Сотрудник деканата")


@pytest.fixture
def student(factory):
    return factory.user(UserRole.STUDENT, username="student1", full_name="Иванов Иван Иванович")


@pytest.fixture
def auth(student):
    return Factory.headers(student)
