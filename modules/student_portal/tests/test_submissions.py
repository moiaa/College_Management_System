"""Загрузка работ студентом и проверка работ преподавателем."""
import pytest

from core.models import UserRole
from modules.student_portal import router as router_module
from modules.student_portal.storage import get_upload_dir

from .conftest import API, DOCX_BYTES, PDF_BYTES, Factory

DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@pytest.fixture
def course(factory, student, teacher):
    course = factory.course(teacher, "Разработка программных модулей")
    factory.enroll(student, course)
    return course


def upload(client, headers, course_id, title="Лабораторная работа №3", work_type="lab",
           name="lab3.pdf", content=PDF_BYTES, content_type="application/pdf"):
    return client.post(
        f"{API}/submissions",
        data={"course_id": str(course_id), "work_type": work_type, "title": title},
        files={"file": (name, content, content_type)},
        headers=headers,
    )


def review(client, teacher, submission_id, status, comment=None):
    payload = {"status": status}
    if comment is not None:
        payload["teacher_comment"] = comment
    return client.patch(
        f"{API}/staff/submissions/{submission_id}", json=payload, headers=Factory.headers(teacher)
    )


def stored_files():
    return [path for path in get_upload_dir().rglob("*") if path.is_file()]


def test_upload_creates_first_version(client, course, auth):
    response = upload(client, auth, course.id)

    assert response.status_code == 201
    body = response.json()
    assert body["version"] == 1
    assert body["status"] == "submitted"
    assert body["file_name"] == "lab3.pdf"
    assert body["file_size"] == len(PDF_BYTES)
    assert body["course_title"] == "Разработка программных модулей"
    assert body["reviewed_at"] is None
    assert len(stored_files()) == 1

    download = client.get(f"{API}/submissions/{body['id']}/file", headers=auth)
    assert download.status_code == 200
    assert download.content == PDF_BYTES


def test_version_rules(client, course, teacher, auth):
    first = upload(client, auth, course.id).json()

    on_review = upload(client, auth, course.id)
    assert on_review.status_code == 409
    assert on_review.json() == {"detail": "Предыдущая версия работы ещё на проверке"}

    assert review(client, teacher, first["id"], "revision", "Нет выводов").status_code == 200
    second = upload(
        client, auth, course.id, title="  лабораторная работа №3 ", name="lab3_v2.docx",
        content=DOCX_BYTES, content_type=DOCX_TYPE,
    )
    assert second.status_code == 201
    assert second.json()["version"] == 2
    assert second.json()["title"] == "Лабораторная работа №3"

    assert review(client, teacher, second.json()["id"], "accepted").status_code == 200
    accepted = upload(client, auth, course.id)
    assert accepted.status_code == 409
    assert accepted.json() == {"detail": "Работа уже принята преподавателем"}

    history = client.get(f"{API}/submissions", headers=auth).json()
    assert [item["version"] for item in history["items"]] == [2, 1]
    assert history["items"][1]["teacher_comment"] == "Нет выводов"


def test_upload_checks_course(client, factory, teacher, auth):
    foreign = factory.course(teacher, "Чужой курс")

    missing = upload(client, auth, 999)
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Курс не найден"}
    not_enrolled = upload(client, auth, foreign.id)
    assert not_enrolled.status_code == 403
    assert not_enrolled.json() == {"detail": "Вы не записаны на этот курс"}


@pytest.mark.parametrize("name, content", [
    ("lab3.txt", b"plain text"),
    ("lab3.pdf", b"not really a pdf"),
    ("lab3.docx", PDF_BYTES),
])
def test_upload_rejects_wrong_file_type(client, course, auth, name, content):
    response = upload(client, auth, course.id, name=name, content=content)

    assert response.status_code == 415
    assert response.json() == {"detail": "Допустимы только файлы PDF и DOCX"}
    assert stored_files() == []


def test_upload_rejects_too_large_file(client, course, auth, monkeypatch):
    monkeypatch.setattr(router_module, "SUBMISSION_MAX_BYTES", 10)

    response = upload(client, auth, course.id)

    assert response.status_code == 413
    assert stored_files() == []


@pytest.mark.parametrize("overrides", [
    {"content": b""},
    {"work_type": "essay"},
    {"title": "   "},
    {"title": "x" * 201},
])
def test_upload_validation_errors(client, course, auth, overrides):
    assert upload(client, auth, course.id, **overrides).status_code == 422


def test_student_cannot_touch_foreign_submission(client, factory, course, auth):
    classmate = factory.user(UserRole.STUDENT)
    factory.enroll(classmate, course)
    foreign = upload(client, Factory.headers(classmate), course.id).json()

    for method, path in [("get", ""), ("get", "/file"), ("delete", "")]:
        response = getattr(client, method)(f"{API}/submissions/{foreign['id']}{path}", headers=auth)
        assert response.status_code == 404
    assert client.get(f"{API}/submissions", headers=auth).json()["total"] == 0


def test_delete_only_before_review(client, course, teacher, auth):
    first = upload(client, auth, course.id).json()
    deleted = client.delete(f"{API}/submissions/{first['id']}", headers=auth)
    assert deleted.status_code == 204
    assert stored_files() == []

    second = upload(client, auth, course.id).json()
    review(client, teacher, second["id"], "accepted")
    response = client.delete(f"{API}/submissions/{second['id']}", headers=auth)
    assert response.status_code == 409
    assert response.json() == {"detail": "Проверенную работу удалить нельзя"}


def test_list_filters(client, course, auth):
    upload(client, auth, course.id, title="Курсовая", work_type="coursework")
    upload(client, auth, course.id, title="Лаба 1")

    by_type = client.get(f"{API}/submissions", params={"work_type": "coursework"}, headers=auth)
    assert [item["title"] for item in by_type.json()["items"]] == ["Курсовая"]
    by_status = client.get(f"{API}/submissions", params={"status": "accepted"}, headers=auth)
    assert by_status.json()["total"] == 0
    assert client.get(f"{API}/submissions", params={"status": "x"}, headers=auth).status_code == 422


def test_teacher_sees_and_reviews_only_own_courses(client, factory, student, course, teacher,
                                                   auth):
    other_teacher = factory.user(UserRole.TEACHER)
    other_course = factory.course(other_teacher, "Курс другого преподавателя")
    factory.enroll(student, other_course)
    mine = upload(client, auth, course.id).json()
    foreign = upload(client, auth, other_course.id).json()
    headers = Factory.headers(teacher)

    queue = client.get(f"{API}/staff/submissions", headers=headers).json()
    assert [item["id"] for item in queue["items"]] == [mine["id"]]
    assert queue["items"][0]["student"]["full_name"] == "Иванов Иван Иванович"

    file_response = client.get(f"{API}/staff/submissions/{mine['id']}/file", headers=headers)
    assert file_response.content == PDF_BYTES
    forbidden = client.get(f"{API}/staff/submissions/{foreign['id']}/file", headers=headers)
    assert forbidden.status_code == 403
    assert review(client, teacher, foreign["id"], "accepted").status_code == 403
    assert review(client, teacher, 999, "accepted").status_code == 404


def test_review_rules(client, course, teacher, auth):
    submission = upload(client, auth, course.id).json()

    assert review(client, teacher, submission["id"], "revision").status_code == 422
    assert review(client, teacher, submission["id"], "submitted").status_code == 422

    accepted = review(client, teacher, submission["id"], "accepted", "Хорошо")
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"
    assert accepted.json()["reviewed_at"] is not None

    again = review(client, teacher, submission["id"], "revision", "Передумал")
    assert again.status_code == 409
    assert again.json() == {"detail": "Работа уже проверена"}

    reviewed = client.get(
        f"{API}/staff/submissions", params={"status": "accepted"}, headers=Factory.headers(teacher)
    ).json()
    assert reviewed["total"] == 1
    student_view = client.get(f"{API}/submissions/{submission['id']}", headers=auth).json()
    assert student_view["teacher_comment"] == "Хорошо"
