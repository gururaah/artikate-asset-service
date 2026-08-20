from datetime import datetime, timezone
from app.database import SessionLocal
from app.models import CheckOut, OverdueNotice

def flag_overdue_checkouts(db_session=None):
    """
    Finds every open, overdue check-out and creates an OverdueNotice dated today.
    Safe to run repeatedly (Idempotent).
    """
    db = db_session if db_session else SessionLocal()
    close_db = db_session is None
    
    try:
        today = datetime.utcnow().date()

        # 1. Find all active checkouts where due_at < now and returned_at is None
        overdue_checkouts = db.query(CheckOut).filter(
            CheckOut.returned_at.is_(None),
            CheckOut.due_at < datetime.utcnow()
        ).all()

        created_count = 0
        for checkout in overdue_checkouts:
            # 2. Check if a notice already exists for this checkout today (Idempotency check)
            existing_notice = db.query(OverdueNotice).filter(
                OverdueNotice.checkout_id == checkout.id,
                OverdueNotice.notice_date == today
            ).first()

            if not existing_notice:
                notice = OverdueNotice(
                    checkout_id=checkout.id,
                    notice_date=today
                )
                db.add(notice)
                created_count += 1

        db.commit()
        print(f"✅ Flagged overdue checkouts: {created_count} new notices created.")
        return created_count

    except Exception as e:
        db.rollback()
        print(f"❌ Error in flag_overdue_checkouts: {e}")
        return 0
    finally:
        if close_db:
            db.close()