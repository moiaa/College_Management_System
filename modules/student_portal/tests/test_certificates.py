"""Заказ справок студентом и обработка заявок деканатом."""
import pytest

from core.models import UserRole

from .conftest import API, PDF_BYTES, Factory


def order(client, headers, **overrides):
    payload = {"type": "study", "copies": 2, "delivery": "paper", **overrides}
    return client.post(f"{API}/certificates", json=payload, headers=headers)


def upload_pdf(client, headers, request_id, content=PDF_BYTES, name="spravka.pdf"):
    return client.post(
        f"{API}/staff/certificates/{request_id}/file",
        files={"file": (name, content, "application/pdf")},
        headers=headers,
    )


def test_certificate_types_catalog(client, auth):
    body = client.get(f"{API}/certificate-types", headers=auth).json()

    assert body["total"] == 3
    study = next(item for item in body["items"] if item["code"] == "study")
    assert study["name"] == "Справка об обучении"
    assert study["delivery_options"] == ["pdf", "paper"]
    assert study["max_copies"] == 5


def test_create_certificate_request(client, auth):
    response = order(client, auth, comment="  Для работы родителей  ")

    assert response.status_code == 201
    body = response.json()
    assert body["type"] == "study"
    assert body["type_name"] == "Справка об обучении"
    assert body["copies"] == 2
    assert body["comment"] == "Для работы родителей"
    assert body["status"] == "created"
    assert body["has_file"] is False
    assert "." not in body["created_at"]

    listed = client.get(f"{API}/certificates", headers=auth).json()
    assert listed["total"] == 1
    assert listed["items"][0]["id"] == body["id"]


def test_second_active_request_of_same_type_conflicts(client, auth):
    assert order(client, auth).status_code == 201

    response = order(client, auth)

    assert response.status_code == 409
    assert response.json() == {"detail": "У вас уже есть активная заявка на эту справку"}
    assert order(client, auth, type="grades_transcript").status_code == 201


@pytest.mark.parametrize("overrides", [
    {"type": "passport"},
    {"copies": 0},
    {"copies": 6},
    {"type": "tax_deduction", "delivery": "pdf"},
    {"delivery": "email"},
    {"comment": "x" * 501},
])
def test_invalid_certificate_request_returns_422(client, auth, overrides):
    assert order(client, auth, **overrides).status_code == 422


def test_student_sees_only_own_requests(client, factory, auth):
    classmate = factory.user(UserRole.STUDENT)
    foreign = order(client, Factory.headers(classmate)).json()

    assert client.get(f"{API}/certificates", headers=auth).json()["total"] == 0
    response = client.get(f"{API}/certificates/{foreign['id']}", headers=auth)
    assert response.status_code == 404
    assert response.json() == {"detail": "Заявка не найдена"}


def test_cancel_only_before_processing(client, admin, auth):
    first = order(client, auth).json()
    cancelled = client.post(f"{API}/certificates/{first['id']}/cancel", headers=auth)
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"

    second = order(client, auth).json()
    client.patch(
        f"{API}/staff/certificates/{second['id']}",
        json={"status": "in_progress"},
        headers=Factory.headers(admin),
    )
    response = client.post(f"{API}/certificates/{second['id']}/cancel", headers=auth)
    assert response.status_code == 409
    assert response.json() == {"detail": "Заявку можно отменить только до начала обработки"}


def test_full_pdf_certificate_flow(client, student, admin, auth):
    staff = Factory.headers(admin)
    request = order(client, auth, delivery="pdf").json()
    url = f"{API}/staff/certificates/{request['id']}"

    queue = client.get(f"{API}/staff/certificates", params={"status": "created"}, headers=staff)
    assert queue.json()["items"][0]["student"] == {
        "id": student.id, "full_name": "Иванов Иван Иванович",
    }
    not_ready = client.get(f"{API}/certificates/{request['id']}/file", headers=auth)
    assert not_ready.status_code == 409

    assert client.patch(url, json={"status": "in_progress"}, headers=staff).status_code == 200
    without_file = client.patch(url, json={"status": "ready"}, headers=staff)
    assert without_file.status_code == 409
    assert without_file.json() == {"detail": "Сначала приложите PDF справки"}

    uploaded = upload_pdf(client, staff, request["id"])
    assert uploaded.status_code == 200
    assert uploaded.json()["has_file"] is True
    assert upload_pdf(client, staff, request["id"]).status_code == 200  # замена файла

    ready = client.patch(url, json={"status": "ready"}, headers=staff)
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"

    download = client.get(f"{API}/certificates/{request['id']}/file", headers=auth)
    assert download.status_code == 200
    assert download.content == PDF_BYTES
    assert download.headers["content-type"] == "application/pdf"
    assert f"spravka-{request['id']}.pdf" in download.headers["content-disposition"]


def test_status_transitions_are_checked(client, admin, auth):
    staff = Factory.headers(admin)
    request = order(client, auth).json()
    url = f"{API}/staff/certificates/{request['id']}"

    skip = client.patch(url, json={"status": "ready"}, headers=staff)
    assert skip.status_code == 409
    assert skip.json() == {"detail": "Недопустимый переход статуса: created → ready"}

    no_reason = client.patch(url, json={"status": "rejected"}, headers=staff)
    assert no_reason.status_code == 422
    assert client.patch(url, json={"status": "cancelled"}, headers=staff).status_code == 422

    rejected = client.patch(
        url, json={"status": "rejected", "status_comment": "Нет оснований"}, headers=staff
    )
    assert rejected.status_code == 200
    assert rejected.json()["status_comment"] == "Нет оснований"
    assert client.patch(url, json={"status": "in_progress"}, headers=staff).status_code == 409

    missing = client.patch(f"{API}/staff/certificates/999", json={"status": "in_progress"},
                           headers=staff)
    assert missing.status_code == 404


def test_paper_certificate_becomes_ready_without_file(client, admin, auth):
    staff = Factory.headers(admin)
    request = order(client, auth).json()
    url = f"{API}/staff/certificates/{request['id']}"

    client.patch(url, json={"status": "in_progress"}, headers=staff)

    assert client.patch(url, json={"status": "ready"}, headers=staff).status_code == 200


def test_certificate_file_upload_checks(client, admin, auth):
    staff = Factory.headers(admin)
    request = order(client, auth, delivery="pdf").json()

    assert upload_pdf(client, staff, request["id"]).status_code == 409  # ещё не в работе
    client.patch(f"{API}/staff/certificates/{request['id']}", json={"status": "in_progress"},
                 headers=staff)

    not_pdf = upload_pdf(client, staff, request["id"], content=b"hello", name="spravka.pdf")
    assert not_pdf.status_code == 415
    assert not_pdf.json() == {"detail": "Допустим только файл PDF"}
    docx = upload_pdf(client, staff, request["id"], name="spravka.docx")
    assert docx.status_code == 415
    assert upload_pdf(client, staff, 999).status_code == 404


def test_staff_filters_and_roles(client, factory, teacher, admin, auth):
    staff = Factory.headers(admin)
    order(client, auth)
    order(client, auth, type="grades_transcript")

    by_type = client.get(f"{API}/staff/certificates", params={"type": "study"}, headers=staff)
    assert by_type.json()["total"] == 1
    unknown = client.get(f"{API}/staff/certificates", params={"type": "x"}, headers=staff)
    assert unknown.status_code == 422
    as_teacher = client.get(f"{API}/staff/certificates", headers=Factory.headers(teacher))
    assert as_teacher.status_code == 403
