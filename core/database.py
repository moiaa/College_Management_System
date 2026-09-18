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
    # Импортируем core.api — он подтягивает роутеры всех подключённых
    # модулей, а вместе с ними и их models.py. Модель обязана
    # зарегистрироваться в Base.metadata до вызова create_all, иначе её
    # таблица не создастся. Если добавляете новый модуль со своей
    # моделью — подключите его роутер в core/api.py, и он попадёт сюда
    # автоматически.
    import core.api  # noqa: F401
    from .models import User, Course, Schedule, Grade, Attendance  # noqa: F401
    Base.metadata.create_all(bind=engine)
    print("✅ База данных инициализирована!")
