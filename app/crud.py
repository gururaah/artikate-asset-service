from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models import Asset, Employee, CheckOut
from app.schemas import CheckOutCreate

def handle_checkout(db: Session, data: CheckOutCreate):
    # 1. Validate due_at range
    now = datetime.now(timezone.utc)
    incoming_due = data.due_at
    if incoming_due.tzinfo is None:
        incoming_due = incoming_due.replace(tzinfo=timezone.utc)

    if incoming_due <= now or (incoming_due - now).days > 30:
        raise HTTPException(
            status_code=400, 
            detail="due_at must be in future and within 30 days."
        )

    # Begin explicit transaction block with row-level locking
    with db.begin():
        # 8. Unknown asset or employee -> 404
        asset = db.execute(
            select(Asset).where(Asset.asset_tag == data.asset_tag).with_for_update()
        ).scalars().first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found.")

        employee = db.execute(
            select(Employee).where(Employee.employee_code == data.employee_code)
        ).scalars().first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found.")

        # 2. Inactive employee check -> 400
        if not employee.is_active:
            raise HTTPException(
                status_code=400, 
                detail="Inactive employee cannot check out items."
            )

        # 1. Asset availability check -> 409
        if asset.status != "AVAILABLE":
            raise HTTPException(
                status_code=409, 
                detail="Asset is not available."
            )

        # 3. Limit check (Max 3 open checkouts) -> 409
        open_count = db.execute(
            select(func.count(CheckOut.id)).where(
                CheckOut.employee_id == employee.id,
                CheckOut.returned_at.is_(None)
            )
        ).scalar()
        if open_count >= 3:
            raise HTTPException(
                status_code=409, 
                detail="Employee has reached the maximum of 3 open check-outs."
            )

        # 5. Create checkout & lock/update asset status atomically
        checkout = CheckOut(
            asset_id=asset.id,
            employee_id=employee.id,
            due_at=incoming_due
        )
        asset.status = "CHECKED_OUT"
        db.add(checkout)
        db.flush()
        
    return checkout


def get_employee_summary(db: Session, employee_code: str):
    # 1. Employee validation -> 404 if not found
    employee = db.execute(
        select(Employee).where(Employee.employee_code == employee_code)
    ).scalars().first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")

    # 2. Total lifetime checkouts count
    lifetime_count = db.execute(
        select(func.count(CheckOut.id)).where(
            CheckOut.employee_id == employee.id
        )
    ).scalar() or 0

    # 3. Currently held (active checkouts where returned_at is null)
    currently_held = db.execute(
        select(func.count(CheckOut.id)).where(
            CheckOut.employee_id == employee.id,
            CheckOut.returned_at.is_(None)
        )
    ).scalar() or 0

    # 4. Currently overdue (active checkouts where due_at < current time)
    now = datetime.now(timezone.utc)
    currently_overdue = db.execute(
        select(func.count(CheckOut.id)).where(
            CheckOut.employee_id == employee.id,
            CheckOut.returned_at.is_(None),
            CheckOut.due_at < now
        )
    ).scalar() or 0

    # 5. Mean hold duration days (average time items were held)
    # Completed checkouts ke liye duration calculate karte hain
    completed_checkouts = db.execute(
        select(CheckOut).where(
            CheckOut.employee_id == employee.id,
            CheckOut.returned_at.is_not(None)
        )
    ).scalars().all()

    mean_hold_duration_days = 0.0
    if completed_checkouts:
        total_days = sum(
            (c.returned_at - c.checked_out_at).total_seconds() / 86400 
            for c in completed_checkouts
        )
        mean_hold_duration_days = round(total_days / len(completed_checkouts), 2)

    # 6. Return dictionary matching the schema fields precisely
    return {
        "employee_code": employee.employee_code,
        "lifetime_count": lifetime_count,
        "currently_held": currently_held,
        "currently_overdue": currently_overdue,
        "mean_hold_duration_days": mean_hold_duration_days
    }