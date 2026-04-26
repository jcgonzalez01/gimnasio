"""Tests del flujo de autenticación y permisos."""
def test_login_unauthenticated_blocked(client, admin_user):
    """Endpoints protegidos deben rechazar peticiones sin token."""
    r = client.get("/api/members")
    assert r.status_code == 401


def test_login_wrong_password(client, admin_user):
    r = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401


def test_login_success_returns_token(client, admin_user):
    r = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["user"]["username"] == "admin"
    assert body["user"]["role"] == "admin"


def test_me_endpoint(client, admin_headers):
    r = client.get("/api/auth/me", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["username"] == "admin"


def test_cashier_cannot_access_admin_endpoints(client, cashier_headers):
    r = client.get("/api/auth/users", headers=cashier_headers)
    assert r.status_code == 403


def test_admin_can_list_users(client, admin_headers):
    r = client.get("/api/auth/users", headers=admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_admin_can_create_user(client, admin_headers):
    r = client.post("/api/auth/users",
                    headers=admin_headers,
                    json={"username": "nuevo", "password": "secret123",
                          "role": "cashier", "is_active": True})
    assert r.status_code == 201
    assert r.json()["username"] == "nuevo"


def test_inactive_user_cannot_login(client, db_session):
    from app.models.user import User, UserRole
    from app.core.security import hash_password
    u = User(username="inact", role=UserRole.CASHIER, is_active=False,
             hashed_password=hash_password("x123456"))
    db_session.add(u)
    db_session.commit()
    r = client.post("/api/auth/login", json={"username": "inact", "password": "x123456"})
    assert r.status_code == 403


def test_health_endpoint_is_public(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
