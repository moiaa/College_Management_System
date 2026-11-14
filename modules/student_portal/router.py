"""API модуля «Кабинет студента»: /api/v1/student_portal/...

Контракт описан в разделе 4.1 ТЗ
(docs/modules/student_portal/specification-backend.md). Служебные
эндпоинты для деканата и преподавателей — в staff.py.
"""
from datetime import date, timedelta
from pathlib import PurePath
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile
from sqlalchemy.orm import Session, joinedload

from core.auth import create_access_token, verify_password
from core.database import get_db
from core.models import Course, User, UserRole

from . import services
from .constants import (
    ACTIVE_CERTIFICATE_STATUSES, CERTIFICATE_TYPES, PDF_CONTENT_TYPE, SUBMISSION_FILE_TYPES,
    SUBMISSION_MAX_BYTES, TOKEN_EXPIRE_MINUTES, AttendanceStatus, CertificateStatus, DayOfWeek,
    SubmissionStatus, WorkType,
)
from .dependencies import Pagination, get_current_student, validation_error
from .models import CertificateRequest, StudentSubmission, utcnow
from .schemas import (
    AnnouncementOut, AttendanceRecordOut, AttendanceReport, CertificateCreate, CertificateOut,
    CertificateTypeOut, CourseOut, DashboardOut, GradesReport, ItemList, LessonOut, LoginRequest,
    LoginResponse, Page, ProfileOut, SubmissionOut,
)
from .staff import staff_router
from .storage import delete_file, file_response, store_upload

router = APIRouter(prefix="/api/v1/student_portal", tags=["student_portal"])


def check_period(date_from: Optional[date], date_to: Optional[date]) -> None:
    if date_from and date_to and date_from > date_to:
        raise validation_error(("query", "date_from"), "date_from не может быть позже date_to")


# --- Вход и профиль -----------------------------------------------------------


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Учётная запись заблокирована")
    if user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Вход в кабинет доступен только студентам")
    token = create_access_token(
        {"sub": str(user.id), "role": user.role.value},
        expires_delta=timedelta(minutes=TOKEN_EXPIRE_MINUTES),
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": TOKEN_EXPIRE_MINUTES * 60,
        "user": services.profile_to_dict(db, user),
    }


@router.get("/me", response_model=ProfileOut)
def get_profile(student: User = Depends(get_current_student), db: Session = Depends(get_db)):
    return services.profile_to_dict(db, student)


@router.get("/dashboard", response_model=DashboardOut)
def get_dashboard(student: User = Depends(get_current_student), db: Session = Depends(get_db)):
    return services.dashboard(db, student, date.today())


# --- Курсы и расписание ---------------------------------------------------------


@router.get("/courses", response_model=ItemList[CourseOut])
def list_courses(
    semester: Optional[str] = Query(None, max_length=20),
    student: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    courses = services.list_courses(db, student.id, semester)
    return {"items": [services.course_to_dict(course) for course in courses], "total": len(courses)}


@router.get("/schedule", response_model=ItemList[LessonOut])
def get_schedule(
    day_of_week: Optional[DayOfWeek] = None,
    student: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    lessons = services.list_lessons(db, student.id, day_of_week.value if day_of_week else None)
    return {"items": lessons, "total": len(lessons)}


# --- Оценки и посещаемость -------------------------------------------------------


@router.get("/grades", response_model=GradesReport)
def get_grades(
    semester: Optional[str] = Query(None, max_length=20),
    course_id: Optional[int] = None,
    student: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    return services.grades_report(db, student.id, semester, course_id)


@router.get("/attendance", response_model=AttendanceReport)
def get_attendance(
    semester: Optional[str] = Query(None, max_length=20),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    student: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    check_period(date_from, date_to)
    return services.attendance_report(db, student.id, semester, date_from, date_to)


@router.get("/attendance/records", response_model=Page[AttendanceRecordOut])
def get_attendance_records(
    course_id: Optional[int] = None,
    status: Optional[AttendanceStatus] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    pagination: Pagination = Depends(),
    student: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    check_period(date_from, date_to)
    items, total = services.attendance_records(
        db,
        student.id,
        offset=pagination.offset,
        limit=pagination.page_size,
        course_id=course_id,
        status=status.value if status else None,
        date_from=date_from,
        date_to=date_to,
    )
    return pagination.wrap(items, total)


# --- Объявления -------------------------------------------------------------------


@router.get("/announcements", response_model=Page[AnnouncementOut])
def get_announcements(
    pagination: Pagination = Depends(),
    student: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    group_id, _ = services.get_group(db, student)
    items, total = services.get_announcements(
        db, group_id, limit=pagination.page_size, offset=pagination.offset
    )
    return pagination.wrap(items, total)


# --- Справки ------------------------------------------------------------------------


def get_own_certificate(db: Session, request_id: int, student: User) -> CertificateRequest:
    request = db.get(CertificateRequest, request_id)
    if request is None or request.student_id != student.id:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    return request


@router.get(
    "/certificate-types",
    response_model=ItemList[CertificateTypeOut],
    dependencies=[Depends(get_current_student)],
)
def list_certificate_types():
    items = [{"code": code, **info} for code, info in CERTIFICATE_TYPES.items()]
    return {"items": items, "total": len(items)}


@router.get("/certificates", response_model=Page[CertificateOut])
def list_certificates(
    status: Optional[CertificateStatus] = None,
    pagination: Pagination = Depends(),
    student: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    query = db.query(CertificateRequest).filter(CertificateRequest.student_id == student.id)
    if status is not None:
        query = query.filter(CertificateRequest.status == status.value)
    total = query.count()
    requests = (
        query.order_by(CertificateRequest.created_at.desc(), CertificateRequest.id.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
        .all()
    )
    return pagination.wrap([services.certificate_to_dict(item) for item in requests], total)


@router.post("/certificates", response_model=CertificateOut, status_code=201)
def create_certificate(
    payload: CertificateCreate,
    student: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    duplicate = db.query(CertificateRequest.id).filter(
        CertificateRequest.student_id == student.id,
        CertificateRequest.cert_type == payload.type,
        CertificateRequest.status.in_(ACTIVE_CERTIFICATE_STATUSES),
    ).first()
    if duplicate is not None:
        raise HTTPException(
            status_code=409, detail="У вас уже есть активная заявка на эту справку"
        )
    comment = payload.comment.strip() if payload.comment else None
    request = CertificateRequest(
        student_id=student.id,
        cert_type=payload.type,
        copies=payload.copies,
        delivery=payload.delivery.value,
        comment=comment or None,
        status=CertificateStatus.CREATED.value,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return services.certificate_to_dict(request)


@router.get("/certificates/{request_id}", response_model=CertificateOut)
def get_certificate(
    request_id: int,
    student: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    return services.certificate_to_dict(get_own_certificate(db, request_id, student))


@router.post("/certificates/{request_id}/cancel", response_model=CertificateOut)
def cancel_certificate(
    request_id: int,
    student: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    request = get_own_certificate(db, request_id, student)
    if request.status != CertificateStatus.CREATED.value:
        raise HTTPException(
            status_code=409, detail="Заявку можно отменить только до начала обработки"
        )
    request.status = CertificateStatus.CANCELLED.value
    request.updated_at = utcnow()
    db.commit()
    db.refresh(request)
    return services.certificate_to_dict(request)


@router.get(
    "/certificates/{request_id}/file",
    response_class=Response,
    responses={200: {"content": {PDF_CONTENT_TYPE: {}}, "description": "PDF справки"}},
)
def download_certificate(
    request_id: int,
    student: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    request = get_own_certificate(db, request_id, student)
    if request.status != CertificateStatus.READY.value or not request.file_path:
        raise HTTPException(status_code=409, detail="Файл справки ещё не готов")
    return file_response(request.file_path, PDF_CONTENT_TYPE, f"spravka-{request.id}.pdf")


# --- Учебные работы -----------------------------------------------------------------


def get_own_submission(db: Session, submission_id: int, student: User) -> StudentSubmission:
    submission = db.get(StudentSubmission, submission_id)
    if submission is None or submission.student_id != student.id:
        raise HTTPException(status_code=404, detail="Работа не найдена")
    return submission


@router.get("/submissions", response_model=Page[SubmissionOut])
def list_submissions(
    course_id: Optional[int] = None,
    status: Optional[SubmissionStatus] = None,
    work_type: Optional[WorkType] = None,
    pagination: Pagination = Depends(),
    student: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    query = db.query(StudentSubmission).filter(StudentSubmission.student_id == student.id)
    if course_id is not None:
        query = query.filter(StudentSubmission.course_id == course_id)
    if status is not None:
        query = query.filter(StudentSubmission.status == status.value)
    if work_type is not None:
        query = query.filter(StudentSubmission.work_type == work_type.value)
    total = query.count()
    submissions = (
        query.options(joinedload(StudentSubmission.course))
        .order_by(StudentSubmission.created_at.desc(), StudentSubmission.id.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
        .all()
    )
    return pagination.wrap([services.submission_to_dict(item) for item in submissions], total)


@router.post("/submissions", response_model=SubmissionOut, status_code=201)
def create_submission(
    course_id: int = Form(...),
    work_type: WorkType = Form(...),
    title: str = Form(..., max_length=200),
    file: UploadFile = File(...),
    student: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    title = title.strip()
    if not title:
        raise validation_error(("body", "title"), "Название работы не может быть пустым")
    if db.get(Course, course_id) is None:
        raise HTTPException(status_code=404, detail="Курс не найден")
    if not services.is_enrolled(db, student.id, course_id):
        raise HTTPException(status_code=403, detail="Вы не записаны на этот курс")

    versions = [
        item
        for item in db.query(StudentSubmission).filter(
            StudentSubmission.student_id == student.id,
            StudentSubmission.course_id == course_id,
        )
        if services.work_key(item.title) == services.work_key(title)
    ]
    previous = max(versions, key=lambda item: item.version) if versions else None
    if previous is not None and previous.status == SubmissionStatus.SUBMITTED.value:
        raise HTTPException(status_code=409, detail="Предыдущая версия работы ещё на проверке")
    if previous is not None and previous.status == SubmissionStatus.ACCEPTED.value:
        raise HTTPException(status_code=409, detail="Работа уже принята преподавателем")

    file_path, file_size, content_type = store_upload(
        file,
        f"submissions/{student.id}",
        SUBMISSION_FILE_TYPES,
        SUBMISSION_MAX_BYTES,
        "Допустимы только файлы PDF и DOCX",
    )
    submission = StudentSubmission(
        student_id=student.id,
        course_id=course_id,
        work_type=work_type.value,
        title=previous.title if previous else title,
        version=previous.version + 1 if previous else 1,
        file_name=PurePath(file.filename.replace("\\", "/")).name[:255],
        file_path=file_path,
        file_size=file_size,
        content_type=content_type,
        status=SubmissionStatus.SUBMITTED.value,
    )
    db.add(submission)
    try:
        db.commit()
    except Exception:
        db.rollback()
        delete_file(file_path)
        raise
    db.refresh(submission)
    return services.submission_to_dict(submission)


@router.get("/submissions/{submission_id}", response_model=SubmissionOut)
def get_submission(
    submission_id: int,
    student: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    return services.submission_to_dict(get_own_submission(db, submission_id, student))


@router.get(
    "/submissions/{submission_id}/file",
    response_class=Response,
    responses={200: {"description": "Файл работы"}},
)
def download_submission(
    submission_id: int,
    student: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    submission = get_own_submission(db, submission_id, student)
    return file_response(submission.file_path, submission.content_type, submission.file_name)


@router.delete("/submissions/{submission_id}", status_code=204, response_class=Response)
def delete_submission(
    submission_id: int,
    student: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    submission = get_own_submission(db, submission_id, student)
    if submission.status != SubmissionStatus.SUBMITTED.value:
        raise HTTPException(status_code=409, detail="Проверенную работу удалить нельзя")
    file_path = submission.file_path
    db.delete(submission)
    db.commit()
    delete_file(file_path)
    return Response(status_code=204)


router.include_router(staff_router)
