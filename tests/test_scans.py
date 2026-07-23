import uuid

from app.models.enums import ScanStatus

from .conftest import auth_headers, create_domain, create_scan


def test_trigger_scan_as_analyst_succeeds(client, analyst_user, admin_user, db_session):
    domain = create_domain(db_session, admin_user.id)

    response = client.post(f"/domains/{domain.id}/scan", headers=auth_headers(analyst_user))

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "PENDING"
    assert uuid.UUID(body["scan_id"])


def test_trigger_scan_as_viewer_is_forbidden(client, viewer_user, admin_user, db_session):
    domain = create_domain(db_session, admin_user.id)

    response = client.post(f"/domains/{domain.id}/scan", headers=auth_headers(viewer_user))

    assert response.status_code == 403
    assert response.json()["error_code"] == "FORBIDDEN"


def test_trigger_scan_returns_404_when_domain_missing(client, admin_user):
    response = client.post(f"/domains/{uuid.uuid4()}/scan", headers=auth_headers(admin_user))

    assert response.status_code == 404
    assert response.json()["error_code"] == "DOMAIN_NOT_FOUND"


def test_trigger_scan_conflicts_when_already_running(client, admin_user, db_session):
    domain = create_domain(db_session, admin_user.id)
    create_scan(db_session, domain.id, status=ScanStatus.RUNNING)

    response = client.post(f"/domains/{domain.id}/scan", headers=auth_headers(admin_user))

    assert response.status_code == 409
    assert response.json()["error_code"] == "SCAN_ALREADY_RUNNING"


def test_list_scans_returns_pagination_metadata(client, admin_user, db_session):
    domain = create_domain(db_session, admin_user.id)
    create_scan(db_session, domain.id, status=ScanStatus.COMPLETED)
    create_scan(db_session, domain.id, status=ScanStatus.COMPLETED)

    response = client.get(
        f"/domains/{domain.id}/scans?page=1&limit=1", headers=auth_headers(admin_user)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["limit"] == 1
    assert body["total"] >= 2
    assert len(body["items"]) == 1


def test_list_scans_returns_404_when_domain_missing(client, admin_user):
    response = client.get(f"/domains/{uuid.uuid4()}/scans", headers=auth_headers(admin_user))

    assert response.status_code == 404
    assert response.json()["error_code"] == "DOMAIN_NOT_FOUND"
