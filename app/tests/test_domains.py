import uuid

from sqlalchemy import select

from app.models.enums import EventType
from app.models.event_log import EventLog

from .conftest import auth_headers, create_domain


def test_create_domain_as_analyst_succeeds(client, analyst_user):
    domain_name = f"test-{uuid.uuid4().hex[:8]}.example.org"

    response = client.post(
        "/domains", json={"domain": domain_name}, headers=auth_headers(analyst_user)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == domain_name
    assert body["status"] == "PENDING"


def test_create_domain_as_viewer_is_forbidden(client, viewer_user):
    response = client.post(
        "/domains", json={"domain": "example.org"}, headers=auth_headers(viewer_user)
    )

    assert response.status_code == 403
    assert response.json()["error_code"] == "FORBIDDEN"


def test_create_domain_rejects_duplicate(client, admin_user):
    payload = {"domain": "duplicate-domain.example"}
    first = client.post("/domains", json=payload, headers=auth_headers(admin_user))
    assert first.status_code == 201

    second = client.post("/domains", json=payload, headers=auth_headers(admin_user))
    assert second.status_code == 409
    assert second.json()["error_code"] == "DOMAIN_ALREADY_EXISTS"


def test_create_domain_writes_audit_log(client, admin_user, db_session):
    domain_name = f"test-{uuid.uuid4().hex[:8]}.example.org"
    response = client.post(
        "/domains", json={"domain": domain_name}, headers=auth_headers(admin_user)
    )
    assert response.status_code == 201

    events = db_session.scalars(
        select(EventLog).where(EventLog.event_type == EventType.DOMAIN_CREATED)
    ).all()
    matching = [e for e in events if e.event_metadata.get("domain") == domain_name]
    assert len(matching) == 1
    assert matching[0].user_id == admin_user.id


def test_create_domain_duplicate_does_not_write_audit_log(client, admin_user, db_session):
    payload = {"domain": f"test-{uuid.uuid4().hex[:8]}.example.org"}
    first = client.post("/domains", json=payload, headers=auth_headers(admin_user))
    assert first.status_code == 201

    second = client.post("/domains", json=payload, headers=auth_headers(admin_user))
    assert second.status_code == 409

    events = db_session.scalars(
        select(EventLog).where(EventLog.event_type == EventType.DOMAIN_CREATED)
    ).all()
    matching = [e for e in events if e.event_metadata.get("domain") == payload["domain"]]
    assert len(matching) == 1


def test_delete_domain_writes_audit_log(client, admin_user, db_session):
    domain = create_domain(db_session, admin_user.id)
    domain_name = domain.name

    response = client.delete(f"/domains/{domain.id}", headers=auth_headers(admin_user))
    assert response.status_code == 204

    events = db_session.scalars(
        select(EventLog).where(EventLog.event_type == EventType.DOMAIN_DELETED)
    ).all()
    matching = [e for e in events if e.event_metadata.get("domain") == domain_name]
    assert len(matching) == 1
    assert matching[0].user_id == admin_user.id


def test_create_domain_rejects_invalid_fqdn(client, admin_user):
    response = client.post(
        "/domains", json={"domain": "not a domain"}, headers=auth_headers(admin_user)
    )

    assert response.status_code == 422


def test_list_domains_returns_pagination_metadata(client, admin_user, db_session):
    create_domain(db_session, admin_user.id)
    create_domain(db_session, admin_user.id)

    response = client.get("/domains?page=1&limit=1", headers=auth_headers(admin_user))

    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["limit"] == 1
    assert body["total"] >= 2
    assert len(body["items"]) == 1


def test_list_domains_rejects_limit_above_max(client, admin_user):
    response = client.get("/domains?limit=500", headers=auth_headers(admin_user))

    assert response.status_code == 422


def test_get_domain_by_id(client, admin_user, db_session):
    domain = create_domain(db_session, admin_user.id)

    response = client.get(f"/domains/{domain.id}", headers=auth_headers(admin_user))

    assert response.status_code == 200
    assert response.json()["id"] == str(domain.id)


def test_get_domain_returns_404_when_missing(client, admin_user):
    response = client.get(f"/domains/{uuid.uuid4()}", headers=auth_headers(admin_user))

    assert response.status_code == 404
    assert response.json()["error_code"] == "DOMAIN_NOT_FOUND"


def test_delete_domain_as_admin_succeeds(client, admin_user, db_session):
    domain = create_domain(db_session, admin_user.id)

    response = client.delete(f"/domains/{domain.id}", headers=auth_headers(admin_user))

    assert response.status_code == 204


def test_delete_domain_as_analyst_is_forbidden(client, analyst_user, admin_user, db_session):
    domain = create_domain(db_session, admin_user.id)

    response = client.delete(f"/domains/{domain.id}", headers=auth_headers(analyst_user))

    assert response.status_code == 403
    assert response.json()["error_code"] == "FORBIDDEN"
