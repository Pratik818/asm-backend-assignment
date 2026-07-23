import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.db.session import Base, get_db
from app.main import app
from app.models.asset import Asset
from app.models.domain import Domain
from app.models.enums import AssetType, DomainStatus, ScanStatus, UserRole
from app.models.scan import Scan
from app.models.user import User
from app.workers.celery_app import celery_app

settings = get_settings()

# Run Celery tasks synchronously, in-process — no Redis/worker needed to run
# the suite. Safe here specifically because every task (discover_domain,
# ping) opens its own SessionLocal() rather than reusing the caller's
# session, so it can never see a test's still-uncommitted, soon-to-be-rolled-
# back rows anyway; it just no-ops (see discover_domain's `if scan is None`).
celery_app.conf.update(task_always_eager=True, task_eager_propagates=True)

test_database_url = URL.create(
    drivername="postgresql+psycopg",
    username=settings.POSTGRES_USER,
    password=settings.POSTGRES_PASSWORD,
    host=settings.POSTGRES_HOST,
    port=settings.POSTGRES_PORT,
    database=settings.POSTGRES_TEST_DB,
)


def _ensure_test_database_exists():
    admin_url = test_database_url.set(database="postgres")
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as connection:
        exists = connection.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": settings.POSTGRES_TEST_DB},
        ).scalar()
        if not exists:
            connection.execute(text(f'CREATE DATABASE "{settings.POSTGRES_TEST_DB}"'))
    admin_engine.dispose()


_ensure_test_database_exists()

engine = create_engine(test_database_url)
Base.metadata.create_all(bind=engine)
TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session")
def test_client():
    with TestClient(app) as client:
        yield client


@pytest.fixture
def db_session():
    connection = engine.connect()
    outer_transaction = connection.begin()
    session = TestSessionLocal(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    outer_transaction.rollback()
    connection.close()


@pytest.fixture
def client(test_client, db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield test_client
    app.dependency_overrides.pop(get_db, None)


def create_user(db_session, role: UserRole) -> User:
    user = User(
        email=f"{role.value.lower()}-{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("Str0ngPass!23"),
        full_name=f"{role.value.title()} User",
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_user(db_session):
    return create_user(db_session, UserRole.ADMIN)


@pytest.fixture
def analyst_user(db_session):
    return create_user(db_session, UserRole.ANALYST)


@pytest.fixture
def viewer_user(db_session):
    return create_user(db_session, UserRole.VIEWER)


def create_domain(db_session, created_by: uuid.UUID, name: str | None = None) -> Domain:
    domain = Domain(
        name=name or f"test-{uuid.uuid4().hex[:8]}.example",
        status=DomainStatus.PENDING,
        created_by=created_by,
    )
    db_session.add(domain)
    db_session.commit()
    db_session.refresh(domain)
    return domain


def create_scan(db_session, domain_id: uuid.UUID, status: ScanStatus = ScanStatus.PENDING) -> Scan:
    scan = Scan(domain_id=domain_id, status=status, triggered_by=None)
    db_session.add(scan)
    db_session.commit()
    db_session.refresh(scan)
    return scan


def create_asset(
    db_session, scan_id: uuid.UUID, domain_id: uuid.UUID, type: AssetType, value: str
) -> Asset:
    asset = Asset(scan_id=scan_id, domain_id=domain_id, type=type, value=value)
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset
