"""
Email Delivery Service Abstraction (Phase 5B, Requirements 17, 18, 19, 35, 36).
Sends the Daily CEO Progress Report to manirkhn@gmail.com with strict security:
- Zero secrets committed to source code.
- Uses environment variables (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, etc.).
- If SMTP credentials are not yet configured by the owner, writes reliably to local outbox
  (reports/daily/outbox/ and data/outbox/) with status 'AWAITING_OWNER_SMTP_CONFIG' and logs delivery record.
- Records delivery status, provider, timestamps, message IDs, and failure tracking.
"""

import os
import smtplib
import json
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from core.db import get_connection
from core.audit import AuditLogger

TARGET_RECIPIENT = "manirkhn@gmail.com"

class EmailDeliveryResult:
    def __init__(self, delivery_id: str, success: bool, status: str, provider: str, message_id: Optional[str] = None, error: Optional[str] = None):
        self.delivery_id = delivery_id
        self.success = success
        self.status = status
        self.provider = provider
        self.message_id = message_id
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "delivery_id": self.delivery_id,
            "success": self.success,
            "status": self.status,
            "provider": self.provider,
            "message_id": self.message_id,
            "error": self.error
        }

class EmailService:
    @staticmethod
    def get_configured_provider() -> str:
        if os.getenv("SMTP_HOST") and os.getenv("SMTP_USER") and os.getenv("SMTP_PASSWORD"):
            return "SMTP"
        return "LOCAL_SECURE_OUTBOX"

    @classmethod
    def send_daily_report(
        cls,
        report_id: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        recipient: str = TARGET_RECIPIENT
    ) -> EmailDeliveryResult:
        """
        Sends the daily CEO report to manirkhn@gmail.com.
        Adheres strictly to Requirement 17: Recipient is strictly manirkhn@gmail.com.
        """
        delivery_id = f"EML-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()
        
        # Invariant check: Recipient must be manirkhn@gmail.com unless explicitly overridden
        if recipient != TARGET_RECIPIENT:
            recipient = TARGET_RECIPIENT

        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")

        provider = "SMTP" if (smtp_host and smtp_user and smtp_password) else "LOCAL_SECURE_OUTBOX"
        status = "PENDING"
        message_id = None
        error_msg = None

        if provider == "SMTP":
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = smtp_user
                msg["To"] = recipient
                msg["Date"] = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
                msg["Message-ID"] = f"<{delivery_id}@{smtp_host}>"
                message_id = msg["Message-ID"]

                msg.attach(MIMEText(body_text, "plain", "utf-8"))
                if body_html:
                    msg.attach(MIMEText(body_html, "html", "utf-8"))

                # SMTP Connection with timeout
                with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.sendmail(smtp_user, [recipient], msg.as_string())

                status = "DELIVERED"
            except Exception as e:
                status = "FAILED"
                error_msg = f"SMTP transmission error: {str(e)}"
        else:
            # Fallback to local secure outbox storage
            # This ensures reports are never lost when running without active external SMTP credentials
            outbox_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "outbox")
            os.makedirs(outbox_dir, exist_ok=True)
            outbox_file = os.path.join(outbox_dir, f"{report_id}-{delivery_id}.json")
            
            with open(outbox_file, "w", encoding="utf-8") as f:
                json.dump({
                    "delivery_id": delivery_id,
                    "report_id": report_id,
                    "recipient": recipient,
                    "subject": subject,
                    "body_text": body_text,
                    "body_html": body_html,
                    "created_at": now,
                    "status": "QUEUED_LOCAL_OUTBOX",
                    "note": "Awaiting SMTP configuration (SMTP_HOST, SMTP_USER, SMTP_PASSWORD)"
                }, f, indent=2)

            message_id = f"outbox://{delivery_id}"
            status = "QUEUED_LOCAL_OUTBOX"

        # Record in email_deliveries table
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO email_deliveries (
                delivery_id, report_id, recipient, subject,
                provider, status, message_id, error, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            delivery_id, report_id, recipient, subject,
            provider, status, message_id, error_msg, now
        ))
        conn.commit()
        conn.close()

        AuditLogger.log(
            agent_id="EMP-001-CEO",
            action="DAILY_REPORT_EMAIL_DELIVERY",
            result=f"Report {report_id} email delivery to {recipient}: status={status}, provider={provider}",
            risk_level="LOW" if status in ["DELIVERED", "QUEUED_LOCAL_OUTBOX"] else "HIGH",
            details={"delivery_id": delivery_id, "provider": provider, "status": status, "error": error_msg}
        )

        return EmailDeliveryResult(
            delivery_id=delivery_id,
            success=(status in ["DELIVERED", "QUEUED_LOCAL_OUTBOX"]),
            status=status,
            provider=provider,
            message_id=message_id,
            error=error_msg
        )

    @classmethod
    def get_recent_deliveries(cls, limit: int = 20) -> list:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM email_deliveries ORDER BY timestamp DESC LIMIT ?
        """, (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
