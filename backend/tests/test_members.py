"""Tests del flujo de miembros y planes."""
def test_create_and_list_member(client, admin_headers):
    r = client.post("/api/members", headers=admin_headers, json={
        "first_name": "Juan",
        "last_name": "Pérez",
        "email": "juan@example.com",
    })
    assert r.status_code == 201
    body = r.json()
    assert body["first_name"] == "Juan"
    assert body["member_number"].startswith("GYM")

    r = client.get("/api/members", headers=admin_headers)
    assert r.status_code == 200
    members = r.json()
    assert len(members) == 1


def test_duplicate_email_rejected(client, admin_headers):
    payload = {"first_name": "A", "last_name": "B", "email": "x@y.com"}
    r1 = client.post("/api/members", headers=admin_headers, json=payload)
    assert r1.status_code == 201
    r2 = client.post("/api/members", headers=admin_headers,
                     json={**payload, "first_name": "C"})
    assert r2.status_code == 409


def test_cashier_cannot_delete_member(client, admin_headers, cashier_headers):
    r = client.post("/api/members", headers=admin_headers,
                    json={"first_name": "X", "last_name": "Y"})
    member_id = r.json()["id"]
    r = client.delete(f"/api/members/{member_id}", headers=cashier_headers)
    assert r.status_code == 403


def test_create_plan(client, admin_headers):
    r = client.post("/api/members/plans", headers=admin_headers, json={
        "name": "Plan Test",
        "duration_days": 30,
        "price": 500.0,
    })
    assert r.status_code == 201
    assert r.json()["name"] == "Plan Test"
