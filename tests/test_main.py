from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import Asset, Employee
from datetime import date, datetime, timedelta, timezone

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"

def test_checkout_and_summary_flow():
    # Setup test database data
    db = TestingSessionLocal()
    
    asset = Asset(asset_tag="TEST-CAM-1", name="Test Camera", category="CAMERA", status="AVAILABLE", purchase_date=date(2026, 1, 1))
    employee = Employee(employee_code="TEST-EMP-1", full_name="Test User", email="test@example.com", is_active=True)
    
    db.add(asset)
    db.add(employee)
    db.commit()
    db.close()

    # 1. Test Successful Checkout
    future_date = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    response = client.post("/api/v1/checkouts/", json={
        "asset_tag": "TEST-CAM-1",
        "employee_code": "TEST-EMP-1",
        "due_at": future_date
    })
    assert response.status_code == 201

    # 2. Test Employee Summary Endpoint
    summary_response = client.get("/api/v1/employees/TEST-EMP-1/summary/")
    assert summary_response.status_code == 200
    data = summary_response.json()
    assert data["employee_code"] == "TEST-EMP-1"
    assert data["currently_held"] == 1
    assert data["lifetime_count"] == 1