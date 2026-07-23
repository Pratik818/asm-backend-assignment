from app.db.session import get_db
from app.main import app


def test_health_check_reports_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"


def test_health_check_reports_503_when_database_unreachable(test_client):
    class _BrokenSession:
        def execute(self, *args, **kwargs):
            raise RuntimeError("database is down")

    def override_get_db():
        yield _BrokenSession()

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = test_client.get("/health")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "error"
    assert body["database"] == "unreachable"
