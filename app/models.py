from datetime import datetime
from sqlalchemy import (
    Boolean, Column, Date, DateTime, Enum, ForeignKey, 
    Integer, String, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    asset_tag = Column(String(32), unique=True, index=True, nullable=False)
    name = Column(String(120), nullable=False)
    category = Column(Enum("CAMERA", "LAPTOP", "SENSOR", "VEHICLE", name="asset_category"), nullable=False)
    status = Column(Enum("AVAILABLE", "CHECKED_OUT", "MAINTENANCE", name="asset_status"), default="AVAILABLE", nullable=False)
    purchase_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    checkouts = relationship("CheckOut", back_populates="asset")

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    employee_code = Column(String(16), unique=True, index=True, nullable=False)
    full_name = Column(String(120), nullable=False)
    email = Column(String(254), unique=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    checkouts = relationship("CheckOut", back_populates="employee")

class CheckOut(Base):
    __tablename__ = "checkouts"

    id = Column(Integer, primary_key=True, index=True)
    # Changed PROTECT to RESTRICT for SQLite compatibility
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="RESTRICT"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False)
    checked_out_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    due_at = Column(DateTime, nullable=False)
    returned_at = Column(DateTime, nullable=True)
    condition_note = Column(Text, default="", nullable=False)

    asset = relationship("Asset", back_populates="checkouts")
    employee = relationship("Employee", back_populates="checkouts")
    notices = relationship("OverdueNotice", back_populates="checkout", cascade="all, delete-orphan")

class OverdueNotice(Base):
    __tablename__ = "overdue_notices"

    id = Column(Integer, primary_key=True, index=True)
    checkout_id = Column(Integer, ForeignKey("checkouts.id", ondelete="CASCADE"), nullable=False)
    notice_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    checkout = relationship("CheckOut", back_populates="notices")

    __table_args__ = (
        UniqueConstraint('checkout_id', 'notice_date', name='uq_checkout_notice_date'),
    )