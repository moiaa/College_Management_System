"""Скрипт инициализации БД"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.database import init_db  # noqa: E402

if __name__ == "__main__":
    init_db()
