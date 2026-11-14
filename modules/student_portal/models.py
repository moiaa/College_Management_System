"""ORM-модели модуля «Кабинет студента» (раздел 5.1 ТЗ).

Модулю принадлежат три таблицы. Таблицы users, courses, schedules,
grades и attendances принадлежат core/ — модуль их только читает.
"""
from datetime import datetime

from sqlalchemy import (
    Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from core.database import Base


def utcnow() -> datetime:
    """Текущее время UTC без микросекунд — так даты выглядят как в контракте."""
    return datetime.utcnow().replace(microsecond=0)


class StudentCourse(Base):
    """Запись студента на курс."""

    __tablename__ = "student_courses"
    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_student_course"),)

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    enrolled_at = Column(DateTime, default=utcnow, nullable=False)

    course = relationship("Course")


class CertificateRequest(Base):
    """Заявка студента на справку в деканат."""

    __tablename__ = "certificate_requests"
    __table_args__ = (Index("ix_certificate_requests_student_status", "student_id", "status"),)

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    cert_type = Column(String(30), nullable=False)
    copies = Column(Integer, nullable=False)
    delivery = Column(String(10), nullable=False)
    comment = Column(Text)
    status = Column(String(20), nullable=False)
    status_comment = Column(Text)
    file_path = Column(String(255))
    processed_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, nullable=False)

    student = relationship("User", foreign_keys=[student_id])


class StudentSubmission(Base):
    """Загруженная работа студента; одна строка — одна версия файла."""

    __tablename__ = "student_submissions"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "course_id", "title", "version", name="uq_submission_version"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    work_type = Column(String(20), nullable=False)
    title = Column(String(200), nullable=False)
    version = Column(Integer, nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False)
    teacher_comment = Column(Text)
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    reviewed_at = Column(DateTime)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    student = relationship("User", foreign_keys=[student_id])
    course = relationship("Course")
