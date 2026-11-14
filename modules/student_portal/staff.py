"""Служебные эндпоинты кабинета студента (раздел 4.1.9 ТЗ).

Деканат (роль admin) обрабатывает заявки на справки, преподаватель
(роль teacher) проверяет работы по своим курсам. Подключаются в
router.py с префиксом /api/v1/student_portal/staff.
"""
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from sqlalchemy.orm import Session, joinedload

from core.database import get_db
from core.models import Course, User

from . import services
from .constants import (
    CERTIFICATE_FILE_MAX_BYTES, CERTIFICATE_FILE_TYPES, CERTIFICATE_TRANSITIONS,
    CERTIFICATE_TYPES, CertificateStatus, Delivery, SubmissionStatus,
)
from .dependencies import Pagination, get_current_admin, get_current_teacher, validation_error
from .models import CertificateRequest, StudentSubmission, utcnow
from .schemas import (
    CertificateStatusUpdate, Page, StaffCertificateOut, StaffSubmissionOut, SubmissionReview,
)
from .storage import delete_file, file_response, store_upload

staff_router = APIRouter(prefix="/staff")


# --- Заявки на справки (деканат) ----------------------------------------------------


def get_certificate_or_404(db: Session, request_id: int) -> CertificateRequest:
    request = db.get(CertificateRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    return request


@staff_router.get("/certificates", response_model=Page[StaffCertificateOut])
def list_certificate_requests(
    status: Optional[CertificateStatus] = None,
    cert_type: Optional[str] = Query(None, alias="type"),
    pagination: Pagination = Depends(),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if cert_type is not None and cert_type not in CERTIFICATE_TYPES:
        raise validation_error(("query", "type"), "Неизвестный тип справки")
    query = db.query(CertificateRequest)
    if status is not None:
        query = query.filter(CertificateRequest.status == status.value)
    if cert_type is not None:
        query = query.filter(CertificateRequest.cert_type == cert_type)
    total = query.count()
    requests = (
        query.options(joinedload(CertificateRequest.student))
        .order_by(CertificateRequest.created_at, CertificateRequest.id)
        .offset(pagination.offset)
        .limit(pagination.page_size)
        .all()
    )
    items = [services.certificate_to_dict(item, with_student=True) for item in requests]
    return pagination.wrap(items, total)


@staff_router.patch("/certificates/{request_id}", response_model=StaffCertificateOut)
def update_certificate_status(
    request_id: int,
    payload: CertificateStatusUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    request = get_certificate_or_404(db, request_id)
    target = payload.status.value
    if target not in CERTIFICATE_TRANSITIONS.get(request.status, set()):
        raise HTTPException(
            status_code=409, detail=f"Недопустимый переход статуса: {request.status} → {target}"
        )
    needs_file = request.delivery == Delivery.PDF.value and target == CertificateStatus.READY.value
    if needs_file and not request.file_path:
        raise HTTPException(status_code=409, detail="Сначала приложите PDF справки")
    request.status = target
    if payload.status_comment is not None:
        request.status_comment = payload.status_comment
    request.processed_by = admin.id
    request.updated_at = utcnow()
    db.commit()
    db.refresh(request)
    return services.certificate_to_dict(request, with_student=True)


@staff_router.post("/certificates/{request_id}/file", response_model=StaffCertificateOut)
def upload_certificate_file(
    request_id: int,
    file: UploadFile = File(...),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    request = get_certificate_or_404(db, request_id)
    if request.status != CertificateStatus.IN_PROGRESS.value:
        raise HTTPException(
            status_code=409, detail="Файл можно приложить только к заявке в работе"
        )
    file_path, _, _ = store_upload(
        file,
        "certificates",
        CERTIFICATE_FILE_TYPES,
        CERTIFICATE_FILE_MAX_BYTES,
        "Допустим только файл PDF",
    )
    old_path = request.file_path
    request.file_path = file_path
    request.processed_by = admin.id
    request.updated_at = utcnow()
    try:
        db.commit()
    except Exception:
        db.rollback()
        delete_file(file_path)
        raise
    delete_file(old_path)
    db.refresh(request)
    return services.certificate_to_dict(request, with_student=True)


# --- Проверка работ (преподаватель) -------------------------------------------------


def get_teacher_submission(db: Session, submission_id: int, teacher: User) -> StudentSubmission:
    submission = db.get(StudentSubmission, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Работа не найдена")
    if submission.course.teacher_id != teacher.id:
        raise HTTPException(
            status_code=403, detail="Работа относится к курсу другого преподавателя"
        )
    return submission


@staff_router.get("/submissions", response_model=Page[StaffSubmissionOut])
def list_submissions_for_review(
    course_id: Optional[int] = None,
    status: Optional[SubmissionStatus] = SubmissionStatus.SUBMITTED,
    pagination: Pagination = Depends(),
    teacher: User = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    query = (
        db.query(StudentSubmission)
        .join(Course, Course.id == StudentSubmission.course_id)
        .filter(Course.teacher_id == teacher.id)
    )
    if course_id is not None:
        query = query.filter(StudentSubmission.course_id == course_id)
    if status is not None:
        query = query.filter(StudentSubmission.status == status.value)
    total = query.count()
    submissions = (
        query.options(
            joinedload(StudentSubmission.course), joinedload(StudentSubmission.student)
        )
        .order_by(StudentSubmission.created_at, StudentSubmission.id)
        .offset(pagination.offset)
        .limit(pagination.page_size)
        .all()
    )
    items = [services.submission_to_dict(item, with_student=True) for item in submissions]
    return pagination.wrap(items, total)


@staff_router.get(
    "/submissions/{submission_id}/file",
    response_class=Response,
    responses={200: {"description": "Файл работы"}},
)
def download_submission_for_review(
    submission_id: int,
    teacher: User = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    submission = get_teacher_submission(db, submission_id, teacher)
    return file_response(submission.file_path, submission.content_type, submission.file_name)


@staff_router.patch("/submissions/{submission_id}", response_model=StaffSubmissionOut)
def review_submission(
    submission_id: int,
    payload: SubmissionReview,
    teacher: User = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    submission = get_teacher_submission(db, submission_id, teacher)
    if submission.status != SubmissionStatus.SUBMITTED.value:
        raise HTTPException(status_code=409, detail="Работа уже проверена")
    submission.status = payload.status.value
    submission.teacher_comment = payload.teacher_comment
    submission.reviewed_by = teacher.id
    submission.reviewed_at = utcnow()
    db.commit()
    db.refresh(submission)
    return services.submission_to_dict(submission, with_student=True)
