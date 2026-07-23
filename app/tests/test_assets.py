from app.models.enums import AssetType, ScanStatus

from .conftest import auth_headers, create_asset, create_domain, create_scan


def test_list_assets_returns_pagination_metadata(client, admin_user, db_session):
    domain = create_domain(db_session, admin_user.id)
    scan = create_scan(db_session, domain.id, status=ScanStatus.COMPLETED)
    create_asset(db_session, scan.id, domain.id, AssetType.A, "93.184.216.34")
    create_asset(db_session, scan.id, domain.id, AssetType.MX, "10 mail.example.org")

    response = client.get("/assets?page=1&limit=1", headers=auth_headers(admin_user))

    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["limit"] == 1
    assert body["total"] >= 2
    assert len(body["items"]) == 1


def test_list_assets_filters_by_domain_id(client, admin_user, db_session):
    domain_a = create_domain(db_session, admin_user.id)
    scan_a = create_scan(db_session, domain_a.id, status=ScanStatus.COMPLETED)
    create_asset(db_session, scan_a.id, domain_a.id, AssetType.A, "1.1.1.1")

    domain_b = create_domain(db_session, admin_user.id)
    scan_b = create_scan(db_session, domain_b.id, status=ScanStatus.COMPLETED)
    create_asset(db_session, scan_b.id, domain_b.id, AssetType.A, "2.2.2.2")

    response = client.get(f"/assets?domain_id={domain_a.id}", headers=auth_headers(admin_user))

    assert response.status_code == 200
    body = response.json()
    assert all(item["domain"] == domain_a.name for item in body["items"])
    assert body["total"] == 1


def test_list_assets_filters_by_type(client, admin_user, db_session):
    domain = create_domain(db_session, admin_user.id)
    scan = create_scan(db_session, domain.id, status=ScanStatus.COMPLETED)
    create_asset(db_session, scan.id, domain.id, AssetType.A, "1.1.1.1")
    create_asset(db_session, scan.id, domain.id, AssetType.NS, "ns1.example.org")

    response = client.get("/assets?type=NS", headers=auth_headers(admin_user))

    assert response.status_code == 200
    body = response.json()
    assert all(item["type"] == "NS" for item in body["items"])


def test_list_assets_filters_by_multiple_types(client, admin_user, db_session):
    domain = create_domain(db_session, admin_user.id)
    scan = create_scan(db_session, domain.id, status=ScanStatus.COMPLETED)
    create_asset(db_session, scan.id, domain.id, AssetType.A, "1.1.1.1")
    create_asset(db_session, scan.id, domain.id, AssetType.AAAA, "::1")
    create_asset(db_session, scan.id, domain.id, AssetType.MX, "10 mail.example.org")

    response = client.get(
        f"/assets?domain_id={domain.id}&type=A&type=AAAA", headers=auth_headers(admin_user)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert {item["type"] for item in body["items"]} == {"A", "AAAA"}


def test_list_assets_rejects_limit_above_max(client, admin_user):
    response = client.get("/assets?limit=500", headers=auth_headers(admin_user))

    assert response.status_code == 422
