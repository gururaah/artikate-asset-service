from datetime import date
from app.database import SessionLocal
from app.models import Asset, Employee

db = SessionLocal()

# Check if asset CAM-002 already exists
if not db.query(Asset).filter_by(asset_tag="CAM-002").first():
    asset = Asset(
        asset_tag="CAM-002",
        name="Digital Video Camera",
        category="CAMERA",
        status="AVAILABLE",
        purchase_date=date(2026, 1, 1)
    )
    db.add(asset)

# Check if employee already exists
if not db.query(Employee).filter_by(employee_code="EMP-001").first():
    employee = Employee(
        employee_code="EMP-001",
        full_name="Rahul Sharma",
        email="rahul@example.com",
        is_active=True
    )
    db.add(employee)

db.commit()
db.close()
print("Sample data added successfully!")