"""
Customer Feedback Loop Engine (EMP-007-SUPPORT).
Captures all user inquiries, complaints, feature requests, and usability issues.
Channels insights directly into Product, Marketing, Sales, and CEO Strategy.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core.db import get_connection
from core.audit import AuditLogger
from memory.store import CorporateMemory

FEEDBACK_TYPES = {
    "QUESTION", "COMPLAINT", "FEATURE_REQUEST", "REFUND_REQUEST",
    "POSITIVE", "NEGATIVE", "USABILITY_ISSUE", "RECURRING_REQUEST"
}

class CustomerFeedbackEngine:
    @staticmethod
    def record_feedback(
        product_id: str,
        customer_ref: str,
        feedback_type: str,
        content: str,
        resolution: str = "",
        agent_id: str = "EMP-007-SUPPORT"
    ) -> str:
        if feedback_type.upper() not in FEEDBACK_TYPES:
            feedback_type = "QUESTION"

        feedback_id = f"FDB-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO customer_feedback (
                feedback_id, product_id, customer_ref, feedback_type, content, resolution, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (feedback_id, product_id, customer_ref, feedback_type.upper(), content, resolution, now))
        conn.commit()
        conn.close()

        # Feed into Corporate Memory for product & marketing optimization
        CorporateMemory.store_memory(
            category="CUSTOMER_FEEDBACK",
            title=f"Feedback on {product_id} [{feedback_type}]: {content[:50]}",
            content=f"Customer: {customer_ref}\nType: {feedback_type}\nDetail:\n{content}\nResolution: {resolution}",
            metadata={"product_id": product_id, "feedback_id": feedback_id, "type": feedback_type},
            tags=["customer", feedback_type.lower(), product_id],
            author_agent=agent_id
        )

        AuditLogger.log(
            agent_id=agent_id,
            action=f"FEEDBACK_RECORDED_{feedback_type}",
            result=f"Recorded customer feedback for {product_id}: {content[:60]}...",
            risk_level="HIGH" if feedback_type in {"REFUND_REQUEST", "COMPLAINT"} else "LOW",
            details={"feedback_id": feedback_id, "product_id": product_id}
        )
        return feedback_id

    @staticmethod
    def get_feedback(product_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        if product_id:
            cursor.execute("SELECT * FROM customer_feedback WHERE product_id = ? ORDER BY created_at DESC LIMIT ?", (product_id, limit))
        else:
            cursor.execute("SELECT * FROM customer_feedback ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
