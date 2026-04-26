"""Fixtures comunes para tests."""
import os
# BD en memoria antes de importar la app
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-with-enough-entropy-for-tests"
os.environ["ENV"] = "development"
os.environ["EMAIL_NOTIFICATIONS_ENABLED"] = "false"
os.environ["BOOTSTRAP_ADMIN_USERNAME"] = "_disabled_seed_"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.core.database as db_module
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.user import User, UserRole


@pytest.fixture(scope="function")
def db_engine(monkeypatch):
    """Engine en memoria. También sustituye el global del módulo para que
    el startup hook de la app trabaje contra la BD de test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    monkeypatch.setattr(db_module, "engine", engine)
    monkeypatch.setattr(db_module, "SessionLocal", TestSessionLocal)

    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db_engine, db_session):
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db_session) -> User:
    u = User(
        username="admin",
        full_name="Admin Test",
        role=UserRole.ADMIN,
        is_active=True,
        hashed_password=hash_password("admin123"),
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture
def cashier_user(db_session) -> User:
    u = User(
        username="caja1",
        full_name="Cajero Test",
        role=UserRole.CASHIER,
        is_active=True,
        hashed_password=hash_password("caja123"),
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture
def admin_token(client, admin_user) -> str:
    r = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture
def cashier_token(client, cashier_user) -> str:
    r = client.post("/api/auth/login", json={"username": "caja1", "password": "caja123"})
    assert r.status_code == 200
    return r.json()["access_token"]


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def cashier_headers(cashier_token):
    return {"Authorization": f"Bearer {cashier_token}"}
