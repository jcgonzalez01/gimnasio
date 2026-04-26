"""Tests del flujo POS y generación de recibos."""
def _create_category(client, headers):
    r = client.post("/api/pos/categories", headers=headers,
                    json={"name": "Cat Test"})
    assert r.status_code == 201
    return r.json()["id"]


def _create_product(client, headers, category_id):
    r = client.post("/api/pos/products", headers=headers, json={
        "name": "Producto Test",
        "price": 100.0,
        "stock": 10,
        "category_id": category_id,
    })
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_create_sale(client, admin_headers):
    cat_id = _create_category(client, admin_headers)
    prod_id = _create_product(client, admin_headers, cat_id)

    r = client.post("/api/pos/sales", headers=admin_headers, json={
        "payment_method": "cash",
        "items": [{
            "product_id": prod_id,
            "product_name": "Producto Test",
            "quantity": 2,
            "unit_price": 100.0,
        }],
    })
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["total"] == 200.0
    assert body["sale_number"].startswith("V")


def test_receipt_pdf_endpoint(client, admin_headers):
    cat_id = _create_category(client, admin_headers)
    prod_id = _create_product(client, admin_headers, cat_id)
    r = client.post("/api/pos/sales", headers=admin_headers, json={
        "payment_method": "cash",
        "items": [{"product_id": prod_id, "product_name": "X", "quantity": 1, "unit_price": 50.0}],
    })
    sale_id = r.json()["id"]

    r = client.get(f"/api/pos/sales/{sale_id}/receipt", headers=admin_headers)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"


def test_cashier_cannot_create_product(client, cashier_headers, admin_headers):
    cat_id = _create_category(client, admin_headers)
    r = client.post("/api/pos/products", headers=cashier_headers, json={
        "name": "Bloqueado", "price": 1.0, "category_id": cat_id,
    })
    assert r.status_code == 403
