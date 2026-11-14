"""Хранение загруженных файлов на диске (раздел 5.3 ТЗ).

Файлы лежат в STUDENT_PORTAL_UPLOAD_DIR (по умолчанию uploads/student_portal
в корне проекта) под сгенерированными именами. В БД хранится путь
относительно этой папки, наружу файлы отдаются только через API.
"""
import os
import uuid
from pathlib import Path
from typing import Dict, Tuple

from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse

from core.config import BASE_DIR

from .dependencies import validation_error

CHUNK_SIZE = 1024 * 1024
MB = 1024 * 1024


class UnsupportedFileType(Exception):
    pass


class FileTooLarge(Exception):
    pass


class EmptyFile(Exception):
    pass


def get_upload_dir() -> Path:
    default = BASE_DIR / "uploads" / "student_portal"
    return Path(os.getenv("STUDENT_PORTAL_UPLOAD_DIR") or default)


def resolve(relative_path: str) -> Path:
    return get_upload_dir() / relative_path


def delete_file(relative_path: str) -> None:
    if relative_path:
        resolve(relative_path).unlink(missing_ok=True)


def save_upload(
    upload: UploadFile,
    subdir: str,
    allowed_types: Dict[str, Tuple[str, bytes]],
    max_bytes: int,
) -> Tuple[str, int, str]:
    """Проверяет и сохраняет файл; возвращает (относительный путь, размер, MIME-тип).

    Тип проверяется по расширению и по сигнатуре в начале файла, а не по
    заголовку Content-Type, который присылает браузер. Файл копируется на
    диск частями; если он превысил лимит, недописанный файл удаляется.
    """
    extension = Path(upload.filename or "").suffix.lower()
    if extension not in allowed_types:
        raise UnsupportedFileType()
    content_type, signature = allowed_types[extension]

    upload.file.seek(0)
    head = upload.file.read(len(signature))
    if not head:
        raise EmptyFile()
    if head != signature:
        raise UnsupportedFileType()
    upload.file.seek(0)

    relative_path = f"{subdir}/{uuid.uuid4().hex}{extension}"
    destination = resolve(relative_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    size = 0
    try:
        with destination.open("wb") as target:
            while True:
                chunk = upload.file.read(CHUNK_SIZE)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    raise FileTooLarge()
                target.write(chunk)
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return relative_path, size, content_type


def store_upload(
    upload: UploadFile,
    subdir: str,
    allowed_types: Dict[str, Tuple[str, bytes]],
    max_bytes: int,
    type_error: str,
) -> Tuple[str, int, str]:
    """save_upload, у которого ошибки уже переведены в HTTP-ответы контракта."""
    try:
        return save_upload(upload, subdir, allowed_types, max_bytes)
    except UnsupportedFileType:
        raise HTTPException(status_code=415, detail=type_error)
    except FileTooLarge:
        raise HTTPException(
            status_code=413, detail=f"Размер файла превышает {max_bytes // MB} МБ"
        )
    except EmptyFile:
        raise validation_error(("body", "file"), "Файл пустой")


def file_response(relative_path: str, media_type: str, filename: str) -> FileResponse:
    path = resolve(relative_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Файл не найден")
    return FileResponse(path, media_type=media_type, filename=filename)
