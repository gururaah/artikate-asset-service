from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_,text
from app import schemas

from app.database import get_db, engine, Base
from app.models import Asset, Employee, CheckOut, OverdueNotice  # Saare models import hone zaroori hain
from app.schemas import CheckOutCreate, ReturnRequest
from app.crud import handle_checkout, get_employee_summary

# 🔑 YE LINE ADD KAREIN: Yeh SQLite/Database ke andar tables create kar degi
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Field Asset Check-Out Service", version="1.0.0")



# --- Health Check (Unauthenticated) ---
@app.get("/api/v1/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # text() function ka use karein SQLAlchemy 2.0 ke liye
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Check-Out Endpoint ---
@app.post("/api/v1/checkouts/", status_code=201)
def checkout_asset(payload: CheckOutCreate, db: Session = Depends(get_db)):
    # Call handle_checkout directly (without 'crud.')
    checkout = handle_checkout(db, payload)
    return {"id": checkout.id, "message": "Asset checked out successfully"}

# --- Employee Summary Endpoint ---
@app.get("/api/v1/employees/{employee_code}/summary/", response_model=schemas.EmployeeSummaryResponse)
def employee_summary(employee_code: str, db: Session = Depends(get_db)):
    return get_employee_summary(db, employee_code)