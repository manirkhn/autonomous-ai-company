"""
Customer Support Engine (Phase 4, Part 22).
Automates standard customer inquiry resolution and escalates edge cases to owner.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core.db import get_connection

class CustomerSupportEngine:
    """
    Handles customer troubleshooting, order status checks, and owner escalations.
    """

    KNOWLEDGE_BASE = {
        "python_version": "Our tools require Python 3.8 or newer. You can check your version with `python --version`.",
        "offline_usage": "Yes, our packages are 100% offline and do not communicate with external cloud servers.",
        "license": "Your purchase includes a perpetual single-developer commercial license.",
        "installation": "Simply unzip the package and run the runner script with Python. See README.md for quickstart flags."
    }

    @classmethod
    def submit_inquiry(
        cls,
        customer_ref: str,
        issue_type: str,
        content: str,
        order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes a customer support inquiry. Automatically resolves known issues or escalates.
        """
        ticket_id = f"TICK-{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        now = datetime.now(timezone.utc).isoformat()
        content_lower = content.lower()

        resolution = None
        status = "OPEN"
        escalated = 0

        # Automated resolution matching
        for keyword, answer in cls.KNOWLEDGE_BASE.items():
            if keyword.replace("_", " ") in content_lower or keyword in content_lower:
                resolution = answer
                status = "RESOLVED"
                break

        # Check for complaints or refund requests
        if "refund" in content_lower or "scam" in content_lower or "broken" in content_lower or not resolution:
            escalated = 1
            status = "ESCALATED_TO_OWNER"
            resolution = resolution or "Your inquiry has been escalated to senior engineering for priority review within 24 hours."

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO customer_support_tickets (
            ticket_id, customer_ref, order_id, issue_type,
            content, resolution, status, escalated_to_owner,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket_id, customer_ref, order_id, issue_type,
            content, resolution, status, escalated, now, now
        ))
        conn.commit()
        conn.close()

        return {
            "ticket_id": ticket_id,
            "status": status,
            "resolution": resolution,
            "escalated_to_owner": bool(escalated),
            "updated_at": now
        }

    @classmethod
    def get_tickets(cls) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customer_support_tickets ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
