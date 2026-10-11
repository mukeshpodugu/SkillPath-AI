import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from sqlalchemy.orm import Session
from .models import EmailNotificationLog

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "notifications@edupath-ai.edu")

def send_email(
    db: Session,
    recipient_email: str,
    subject: str,
    html_content: str,
    template_name: str,
    user_id: int = None
) -> bool:
    """
    Sends transactional email via SMTP if credentials are configured;
    otherwise logs the event cleanly in database sandbox for auditing.
    """
    delivery_status = "sent"
    
    if SMTP_HOST and SMTP_USER and SMTP_PASSWORD:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = FROM_EMAIL
            msg["To"] = recipient_email
            msg.attach(MIMEText(html_content, "html"))
            
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(FROM_EMAIL, [recipient_email], msg.as_string())
            delivery_status = "sent_live"
        except Exception as e:
            delivery_status = f"failed: {str(e)}"
    else:
        delivery_status = "logged_sandbox"

    # Persist log
    try:
        log_entry = EmailNotificationLog(
            user_id=user_id,
            recipient_email=recipient_email,
            subject=subject,
            template_name=template_name,
            status=delivery_status,
            created_at=datetime.utcnow()
        )
        db.add(log_entry)
        db.commit()
    except Exception:
        db.rollback()

    return True

# --- Specific Transactional Email Templates ---

def send_welcome_email(db: Session, user_id: int, name: str, email: str):
    subject = "Welcome to EduPath AI — Your Adaptive Learning Journey Begins"
    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px;">
        <h2 style="color: #2563eb; margin-top: 0;">Welcome to EduPath AI, {name}!</h2>
        <p style="color: #334155; line-height: 1.6;">
            Your account has been created. EduPath AI optimizes what you should study next to achieve your selected career goal using knowledge tracing, prerequisite graph intelligence, and time-efficiency scoring.
        </p>
        <div style="margin: 20px 0; padding: 16px; background-color: #f8fafc; border-radius: 6px;">
            <p style="margin: 0; color: #475569; font-size: 14px;">
                <strong>Next Step:</strong> Complete your diagnostic assessment to establish your baseline skill mastery and unlock your personalized roadmap.
            </p>
        </div>
        <p style="color: #64748b; font-size: 12px; margin-top: 24px;">EduPath AI Learning Engine &bull; Automated Notification</p>
    </div>
    """
    return send_email(db, email, subject, html, "WELCOME", user_id=user_id)

def send_exam_result_email(db: Session, user_id: int, email: str, module_title: str, score: float, passed: bool):
    status_str = "Passed" if passed else "Needs Practice"
    color = "#16a34a" if passed else "#dc2626"
    subject = f"Module Assessment {status_str}: {module_title} ({int(score)}%)"
    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px;">
        <h2 style="color: {color}; margin-top: 0;">Exam {status_str} — {module_title}</h2>
        <p style="color: #334155;">You scored <strong>{int(score)}%</strong> on your module evaluation.</p>
        <p style="color: #475569;">
            {'Congratulations! Your knowledge state has been updated, and dependent advanced modules have been unlocked in your roadmap.' if passed else 'Don\'t worry! Review the recommended practice activities and you can retake the assessment when ready.'}
        </p>
        <p style="color: #64748b; font-size: 12px; margin-top: 24px;">EduPath AI Assessment Engine</p>
    </div>
    """
    return send_email(db, email, subject, html, "EXAM_RESULT", user_id=user_id)

def send_subscription_email(db: Session, user_id: int, email: str, plan_name: str, amount_inr: int):
    subject = f"EduPath AI Subscription Activated: {plan_name}"
    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px;">
        <h2 style="color: #2563eb; margin-top: 0;">Subscription Confirmed</h2>
        <p style="color: #334155;">Thank you for upgrading to <strong>{plan_name}</strong>!</p>
        <div style="padding: 16px; background-color: #f1f5f9; border-radius: 6px; margin: 16px 0;">
            <p style="margin: 4px 0;"><strong>Plan:</strong> {plan_name}</p>
            <p style="margin: 4px 0;"><strong>Amount Paid:</strong> ₹{amount_inr}</p>
            <p style="margin: 4px 0;"><strong>Status:</strong> Active</p>
        </div>
        <p style="color: #475569;">You now have full access to multiple career roadmaps, advanced assessments, and priority NBLA recommendations.</p>
    </div>
    """
    return send_email(db, email, subject, html, "SUBSCRIPTION_RECEIPT", user_id=user_id)
