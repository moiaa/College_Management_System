"""Конфигурация приложения"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "college.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
