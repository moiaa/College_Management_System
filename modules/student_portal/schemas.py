"""Pydantic-схемы запросов и ответов (раздел 4.1 ТЗ)."""
from datetime import date, datetime
from typing import Annotated, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, PlainSerializer, field_validator, model_validator

from .constants import (
    CERTIFICATE_TYPES, CourseStatus, Delivery, ReviewStatus, StaffCertificateStatus,
)

# Дата и время в ответах — ISO 8601 без микросекунд: 2026-10-05T10:00:00
DateTimeOut = Annotated[
    datetime,
    PlainSerializer(lambda value: value.replace(microsecond=0).isoformat(), return_type=str),
]

T = TypeVar("T")


class ItemList(BaseModel, Generic[T]):
    items: List[T]
    total: int


class Page(ItemList[T], Generic[T]):
    page: int
    page_size: int


# --- Вход и профиль -------------------------------------------------------


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class ProfileOut(BaseModel):
    id: int
    username: str
    full_name: str
    email: str
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    created_at: Optional[DateTimeOut] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: ProfileOut


# --- Курсы, расписание, оценки, посещаемость ------------------------------


class PersonShort(BaseModel):
    id: int
    full_name: str


class CourseOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    semester: str
    credits: Optional[int] = None
    teacher: Optional[PersonShort] = None


class LessonOut(BaseModel):
    id: int
    day_of_week: str
    time_start: str
    time_end: str
    room: str
    building: Optional[str] = None
    course_id: int
    course_title: str
    teacher_name: Optional[str] = None


class GradeOut(BaseModel):
    id: int
    grade: float
    comment: Optional[str] = None
    graded_at: Optional[DateTimeOut] = None


class CourseGradesOut(BaseModel):
    course_id: int
    course_title: str
    semester: str
    credits: Optional[int] = None
    teacher_name: Optional[str] = None
    grades: List[GradeOut]
    average: Optional[float] = None
    status: CourseStatus


class GradesReport(ItemList[CourseGradesOut]):
    average: Optional[float] = None
    debts_count: int


class AttendanceCounters(BaseModel):
    total: int
    present: int
    late: int
    absent: int
    excused: int
    attendance_percent: Optional[float] = None


class CourseAttendanceOut(AttendanceCounters):
    course_id: int
    course_title: str


class AttendanceReport(ItemList[CourseAttendanceOut]):
    overall: AttendanceCounters


class AttendanceRecordOut(BaseModel):
    id: int
    date: date
    course_id: int
    course_title: str
    status: str
    comment: Optional[str] = None


class AnnouncementOut(BaseModel):
    id: int
    title: str
    text: str
    teacher_name: Optional[str] = None
    created_at: Optional[DateTimeOut] = None
    updated_at: Optional[DateTimeOut] = None


class DashboardOut(BaseModel):
    date: date
    day_of_week: str
    today_lessons: List[LessonOut]
    average_grade: Optional[float] = None
    debts_count: int
    attendance_percent: Optional[float] = None
    active_certificate_requests: int
    submissions_on_review: int
    submissions_need_revision: int
    latest_announcements: List[AnnouncementOut]


# --- Справки ----------------------------------------------------------------


class CertificateTypeOut(BaseModel):
    code: str
    name: str
    description: str
    delivery_options: List[str]
    max_copies: int


class CertificateCreate(BaseModel):
    type: str
    copies: int = Field(ge=1)
    delivery: Delivery
    comment: Optional[str] = Field(default=None, max_length=500)

    @field_validator("type")
    @classmethod
    def type_must_exist(cls, value: str) -> str:
        if value not in CERTIFICATE_TYPES:
            raise ValueError("Неизвестный тип справки")
        return value

    @model_validator(mode="after")
    def check_type_limits(self):
        cert_type = CERTIFICATE_TYPES[self.type]
        if self.copies > cert_type["max_copies"]:
            raise ValueError(
                f"Для этой справки можно заказать не больше {cert_type['max_copies']} экз."
            )
        if self.delivery.value not in cert_type["delivery_options"]:
            raise ValueError("Этот способ получения недоступен для выбранной справки")
        return self


class CertificateOut(BaseModel):
    id: int
    type: str
    type_name: str
    copies: int
    delivery: str
    comment: Optional[str] = None
    status: str
    status_comment: Optional[str] = None
    has_file: bool
    created_at: DateTimeOut
    updated_at: DateTimeOut


class StaffCertificateOut(CertificateOut):
    student: PersonShort


class CertificateStatusUpdate(BaseModel):
    status: StaffCertificateStatus
    status_comment: Optional[str] = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def comment_required_for_rejection(self):
        if self.status_comment is not None:
            self.status_comment = self.status_comment.strip() or None
        if self.status == StaffCertificateStatus.REJECTED and not self.status_comment:
            raise ValueError("При отклонении заявки укажите причину в status_comment")
        return self


# --- Учебные работы ---------------------------------------------------------


class SubmissionOut(BaseModel):
    id: int
    course_id: int
    course_title: str
    work_type: str
    title: str
    version: int
    file_name: str
    file_size: int
    status: str
    teacher_comment: Optional[str] = None
    reviewed_at: Optional[DateTimeOut] = None
    created_at: DateTimeOut


class StaffSubmissionOut(SubmissionOut):
    student: PersonShort


class SubmissionReview(BaseModel):
    status: ReviewStatus
    teacher_comment: Optional[str] = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def comment_required_for_revision(self):
        if self.teacher_comment is not None:
            self.teacher_comment = self.teacher_comment.strip() or None
        if self.status == ReviewStatus.REVISION and not self.teacher_comment:
            raise ValueError("Чтобы вернуть работу на доработку, напишите комментарий")
        return self
