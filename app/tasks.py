from celery import Celery
from datetime import date, datetime
from app.database import SessionLocal
from app.models import CheckOut, OverdueNotice
from sqlalchemy.exc import IntegrityError

celery_app = Celery("tasks", broker="redis://localhost:6379/0")

@celery_app.task
def flag_overdue_checkouts():
    db = SessionLocal()
    try:
        today = date.today()
        now = datetime.utcnow()
        
        # Find all open checkouts past their due date
        overdue_items = db.query(CheckOut).filter(
            CheckOut.returned_at.is_(None),
            CheckOut.due_at < now
        ).all()

        created_count = 0
        for c in overdue_items:
            try:
                
                notice = OverdueNotice(checkout_id=c.id, notice_date=today)
                db.add(notice)
                db.commit()
                created_count += 1
            except IntegrityError:
                db.rollback() 
                
        return f"Successfully flagged {created_count} overdue checkouts."
    finally:
        db.close()