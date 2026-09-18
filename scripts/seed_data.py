"""Скрипт наполнения БД тестовыми данными"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.database import SessionLocal, engine, Base  # noqa: E402
from core.models import User, UserRole  # noqa: E402
from core.auth import get_password_hash  # noqa: E402


def seed_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        users = [
            User(username="admin", email="admin@college.edu",
                 hashed_password=get_password_hash("admin123"),
                 full_name="Администратор", role=UserRole.ADMIN),
            User(username="teacher1", email="teacher@college.edu",
                 hashed_password=get_password_hash("teacher123"),
                 full_name="Преподаватель", role=UserRole.TEACHER),
            User(username="student1", email="student@college.edu",
                 hashed_password=get_password_hash("student123"),
                 full_name="Студент", role=UserRole.STUDENT),
        ]
        db.add_all(users)
        db.commit()
        print("✅ Тестовые данные добавлены!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
