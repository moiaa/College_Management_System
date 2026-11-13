"""Константы модуля «Кабинет студента»: статусы, каталог справок, лимиты.

Значения совпадают с разделами 4.1 и 5.2 ТЗ
(docs/modules/student_portal/specification-backend.md).
"""
from enum import Enum


class DayOfWeek(str, Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


DAY_ORDER = {day.value: index for index, day in enumerate(DayOfWeek)}


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    LATE = "late"
    ABSENT = "absent"
    EXCUSED = "excused"


class CourseStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    DEBT = "debt"
    PASSED = "passed"


class CertificateStatus(str, Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class StaffCertificateStatus(str, Enum):
    """Статусы, в которые деканат может перевести заявку."""

    IN_PROGRESS = "in_progress"
    READY = "ready"
    REJECTED = "rejected"


ACTIVE_CERTIFICATE_STATUSES = (CertificateStatus.CREATED.value, CertificateStatus.IN_PROGRESS.value)

CERTIFICATE_TRANSITIONS = {
    CertificateStatus.CREATED.value: {
        CertificateStatus.IN_PROGRESS.value,
        CertificateStatus.REJECTED.value,
    },
    CertificateStatus.IN_PROGRESS.value: {
        CertificateStatus.READY.value,
        CertificateStatus.REJECTED.value,
    },
}


class Delivery(str, Enum):
    PDF = "pdf"
    PAPER = "paper"


CERTIFICATE_TYPES = {
    "study": {
        "name": "Справка об обучении",
        "description": "Подтверждает, что студент обучается в колледже",
        "delivery_options": [Delivery.PDF.value, Delivery.PAPER.value],
        "max_copies": 5,
    },
    "tax_deduction": {
        "name": "Справка для налогового вычета",
        "description": "Для получения социального налогового вычета за обучение",
        "delivery_options": [Delivery.PAPER.value],
        "max_copies": 2,
    },
    "grades_transcript": {
        "name": "Выписка оценок",
        "description": "Перечень дисциплин с итоговыми оценками",
        "delivery_options": [Delivery.PDF.value, Delivery.PAPER.value],
        "max_copies": 3,
    },
}


class WorkType(str, Enum):
    COURSEWORK = "coursework"
    LAB = "lab"
    OTHER = "other"


class SubmissionStatus(str, Enum):
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REVISION = "revision"


class ReviewStatus(str, Enum):
    """Статусы, которые преподаватель ставит при проверке работы."""

    ACCEPTED = "accepted"
    REVISION = "revision"


PASSING_GRADE = 3.0
TOKEN_EXPIRE_MINUTES = 30
LATEST_ANNOUNCEMENTS_LIMIT = 3

MB = 1024 * 1024
SUBMISSION_MAX_BYTES = 20 * MB
CERTIFICATE_FILE_MAX_BYTES = 5 * MB

PDF_CONTENT_TYPE = "application/pdf"
DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

# расширение -> (MIME-тип, сигнатура начала файла)
SUBMISSION_FILE_TYPES = {
    ".pdf": (PDF_CONTENT_TYPE, b"%PDF"),
    ".docx": (DOCX_CONTENT_TYPE, b"PK\x03\x04"),
}
CERTIFICATE_FILE_TYPES = {
    ".pdf": (PDF_CONTENT_TYPE, b"%PDF"),
}
