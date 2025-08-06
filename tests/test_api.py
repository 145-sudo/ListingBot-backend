import pytest
from fastapi.testclient import TestClient
from main import app
from database import engine, SessionLocal
from models import Base
from seeder import seed_user

def get_test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def test_client():
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope="module")
def test_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def test_user(test_db):
    seed_user()
    user = test_db.query(User).first()
    return user

def test_create_token(test_client, test_user):
    response = test_client.post(
        "/token",
        data={"username": "admin@example.com", "password": "admin123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()

def test_get_products(test_client, test_user):
    response = test_client.get("/products")
    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data

def test_get_product(test_client, test_user):
    # First create a product
    product_data = {
        "name": "Test Product",
        "description": "Test Description",
        "price": 100.00,
        "supplier": "Test Supplier"
    }
    response = test_client.post(
        "/products",
        json=product_data,
        headers={"Authorization": f"Bearer {get_token(test_client)}"}
    )
    assert response.status_code == 200
    product_id = response.json()["id"]

    # Now get the product
    response = test_client.get(f"/products/{product_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Product"
    assert data["supplier"] == "Test Supplier"

def get_token(client):
    response = client.post(
        "/token",
        data={"username": "admin@example.com", "password": "admin123"}
    )
    return response.json()["access_token"]
