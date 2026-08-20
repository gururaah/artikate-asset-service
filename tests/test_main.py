from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.tasks import flag_overdue_checkouts
from app.database import SessionLocal

from app.main import app
from app.database import Base, get_db
from app.models import Asset, Employee, CheckOut, OverdueNotice
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

def test_flag_overdue_checkouts_idempotency():
    db = TestingSessionLocal()
    
    # Setup test data using correct model attributes
    asset = Asset(asset_tag="OVERDUE-CAM", name="Overdue Cam", category="CAMERA", status="CHECKED_OUT", purchase_date=date(2026, 1, 1))
    emp = Employee(employee_code="EMP-TEST", full_name="Task User", email="task@example.com", is_active=True)
    db.add(asset)
    db.add(emp)
    db.commit()
    
    db.refresh(asset)
    db.refresh(emp)

    # Past due date (Overdue)
    past_due = datetime.utcnow() - timedelta(days=2)
    checkout = CheckOut(
        asset_id=asset.id,
        employee_id=emp.id,
        checked_out_at=past_due - timedelta(days=5),
        due_at=past_due,
        returned_at=None
    )
    db.add(checkout)
    db.commit()
    checkout_id = checkout.id

    # 1. Run task first time using the test db session -> Should create 1 notice
    created_first = flag_overdue_checkouts(db)
    assert created_first >= 1

    # 2. Run task second time immediately -> Should create 0 new notices (Idempotency)
    created_second = flag_overdue_checkouts(db)
    assert created_second == 0

    # Verify total notice count in DB for this checkout is exactly 1
    notices_count = db.query(OverdueNotice).filter(OverdueNotice.checkout_id == checkout_id).count()
    db.close()
    
    assert notices_count == 1