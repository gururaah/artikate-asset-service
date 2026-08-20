from datetime import date, datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Asset, Employee, CheckOut, OverdueNotice

def seed_database():
    db: Session = SessionLocal()
    try:
        print("🌱 Seeding database...")

        # 1. Check if data already exists (Idempotency check)
        if db.query(Asset).first():
            print("Database already seeded. Skipping seed process.")
            return

        # 2. Seed Employees (at least 4, 1 inactive)
        employees_data = [
            {"code": "EMP-001", "name": "Aarav Sharma", "email": "aarav@example.com", "active": True},
            {"code": "EMP-002", "name": "Priya Verma", "email": "priya@example.com", "active": True},
            {"code": "EMP-003", "name": "Rahul Singh", "email": "rahul@example.com", "active": True},
            {"code": "EMP-004", "name": "Inactive User", "email": "inactive@example.com", "active": False},
        ]
        
        employees = {}
        for emp in employees_data:
            db_emp = Employee(employee_code=emp["code"], full_name=emp["name"], email=emp["email"], is_active=emp["active"])
            db.add(db_emp)
            employees[emp["code"]] = db_emp
        
        db.commit()

        # 3. Seed Assets (at least 8 across categories)
        assets_data = [
            {"tag": "CAM-01", "name": "Sony DSLR", "category": "CAMERA"},
            {"tag": "CAM-02", "name": "Canon Mirrorless", "category": "CAMERA"},
            {"tag": "LAP-01", "name": "MacBook Pro", "category": "LAPTOP"},
            {"tag": "LAP-02", "name": "Dell XPS", "category": "LAPTOP"},
            {"tag": "MIC-01", "name": "Rode Wireless", "category": "MICROPHONE"},
            {"tag": "MIC-02", "name": "Shure SM58", "category": "MICROPHONE"},
            {"tag": "ACC-01", "name": "Tripod Stand", "category": "ACCESSORY"},
            {"tag": "ACC-02", "name": "LED Ring Light", "category": "ACCESSORY"},
        ]
        
        assets = {}
        for ast in assets_data:
            db_ast = Asset(asset_tag=ast["tag"], name=ast["name"], category=ast["category"], status="AVAILABLE", purchase_date=date(2025, 1, 1))
            db.add(db_ast)
            assets[ast["tag"]] = db_ast
        
        db.commit()

        # 4. Seed Checkouts (Overdue, Returned on time, Returned late, etc.)
        now = datetime.now(timezone.utc)
        
        checkouts_data = [
            # Currently Overdue 1
            {
                "asset_tag": "CAM-01", "emp_code": "EMP-001", 
                "checked_out_at": now - timedelta(days=10), 
                "due_at": now - timedelta(days=3), 
                "returned_at": None, "status": "CHECKED_OUT"
            },
            # Currently Overdue 2
            {
                "asset_tag": "LAP-01", "emp_code": "EMP-002", 
                "checked_out_at": now - timedelta(days=15), 
                "due_at": now - timedelta(days=5), 
                "returned_at": None, "status": "CHECKED_OUT"
            },
            # Returned on time
            {
                "asset_tag": "MIC-01", "emp_code": "EMP-001", 
                "checked_out_at": now - timedelta(days=10), 
                "due_at": now - timedelta(days=2), 
                "returned_at": now - timedelta(days=3), "status": "RETURNED"
            },
            # Returned late
            {
                "asset_tag": "ACC-01", "emp_code": "EMP-003", 
                "checked_out_at": now - timedelta(days=10), 
                "due_at": now - timedelta(days=5), 
                "returned_at": now - timedelta(days=2), "status": "RETURNED"
            },
        ]

        for co in checkouts_data:
            db_co = CheckOut(
                asset_tag=co["asset_tag"],
                employee_code=co["emp_code"],
                checked_out_at=co["checked_out_at"],
                due_at=co["due_at"],
                returned_at=co["returned_at"],
                status=co["status"]
            )
            if co["status"] == "CHECKED_OUT":
                assets[co["asset_tag"]].status = "CHECKED_OUT"
                
            db.add(db_co)

        db.commit()
        print(" Database seeding completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()