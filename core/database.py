"""Подключение к базе данных"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()

def get_db():
    """Генератор сессии БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Инициализация БД"""
    from .models import User, Course, Schedule, Grade, Attendance
    Base.metadata.create_all(bind=engine)
    print("✅ База данных инициализирована!")
