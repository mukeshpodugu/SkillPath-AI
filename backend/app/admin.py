from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from .models import (
    User, LearningModule, LearningResource, AssessmentAttempt, 
    PaymentOrder, EmailNotificationLog
)
from .schemas import AdminStatsResponse
from .auth import require_admin
from .database import get_db

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/overview", response_model=AdminStatsResponse)
def get_admin_overview(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Retrieve system telemetry and platform health metrics."""
    total_users = db.query(User).count()
    total_students = db.query(User).filter(User.role == "student").count()
    total_admins = db.query(User).filter(User.role == "admin").count()
    total_modules = db.query(LearningModule).count()
    total_resources = db.query(LearningResource).count()
    total_attempts = db.query(AssessmentAttempt).count()
    
    paid_orders = db.query(PaymentOrder).filter(PaymentOrder.status == "paid").all()
    total_rev = sum([o.amount_inr for o in paid_orders])
    recent_emails = db.query(EmailNotificationLog).count()

    return AdminStatsResponse(
        total_users=total_users,
        total_students=total_students,
        total_admins=total_admins,
        total_modules=total_modules,
        total_resources=total_resources,
        total_exam_attempts=total_attempts,
        total_revenue_inr=total_rev,
        recent_email_count=recent_emails
    )

@router.get("/users")
def get_admin_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """List users for admin monitoring."""
    users = db.query(User).order_by(User.created_at.desc()).limit(50).all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "subscription_tier": u.subscription_tier,
            "is_verified": u.is_email_verified,
            "streak": u.study_streak_days,
            "study_mins": u.total_study_minutes,
            "career": u.career.name if u.career else "None Selected"
        }
        for u in users
    ]

@router.get("/emails")
def get_admin_emails(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Audit log of recent system notifications."""
    logs = db.query(EmailNotificationLog).order_by(EmailNotificationLog.created_at.desc()).limit(50).all()
    return [
        {
            "id": l.id,
            "recipient": l.recipient_email,
            "subject": l.subject,
            "template": l.template_name,
            "status": l.status,
            "timestamp": l.created_at.isoformat()
        }
        for l in logs
    ]

@router.get("/payments")
def get_admin_payments(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Audit log of financial orders."""
    orders = db.query(PaymentOrder).order_by(PaymentOrder.created_at.desc()).limit(50).all()
    return [
        {
            "id": o.id,
            "user_id": o.user_id,
            "order_id": o.razorpay_order_id,
            "payment_id": o.razorpay_payment_id,
            "plan_code": o.plan_code,
            "amount_inr": o.amount_inr,
            "status": o.status,
            "timestamp": o.created_at.isoformat()
        }
        for o in orders
    ]
