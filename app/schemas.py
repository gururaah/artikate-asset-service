from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

# --- Asset Schemas ---
class AssetCreate(BaseModel):
    asset_tag: str = Field(..., max_length=32)
    name: str = Field(..., max_length=120)
    category: str  # CAMERA, LAPTOP, SENSOR, VEHICLE
    purchase_date: date

class AssetResponse(BaseModel):
    id: int
    asset_tag: str
    name: str
    category: str
    status: str
    purchase_date: date
    current_holder: Optional[dict] = None  

    class Config:
        from_attributes = True


# --- CheckOut Schemas ---
class CheckOutCreate(BaseModel):
    asset_tag: str = Field(..., max_length=32)
    employee_code: str = Field(..., max_length=16)
    due_at: datetime

class CheckOutResponse(BaseModel):
    id: int
    asset_id: int
    employee_id: int
    checked_out_at: datetime
    due_at: datetime
    returned_at: Optional[datetime] = None
    condition_note: str

    class Config:
        from_attributes = True


# --- Return Schemas ---
class ReturnRequest(BaseModel):
    condition_note: str = ""
    needs_maintenance: bool = False


# --- Employee Summary Schema ---
class EmployeeSummaryResponse(BaseModel):
    employee_code: str
    lifetime_count: int
    currently_held: int
    currently_overdue: int
    mean_hold_duration_days: float