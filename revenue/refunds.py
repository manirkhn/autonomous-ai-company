"""
Customer Refund Engine (Phase 4, Part 23).
Processes legitimate refunds transparently without obstruction.
Feeds refund signals into product refinement and ledger updates.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core.db import get_connection

class RefundProcessingEngine:
    """
    Manages customer refund requests, updates ledger, and logs feedback patterns.
    """

    @classmethod
    def request_refund(
        cls,
        order_id: str,
        customer_id: str,
        product_id: str,
        amount: float,
        reason: str
    ) -> Dict[str, Any]:
        """
        Registers a customer refund request.
        """
        refund_id = f"REF-{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        now = datetime.now(timezone.utc).isoformat()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO refund_records (
            refund_id, order_id, customer_id, product_id,
            amount, reason, status, owner_notes, created_at, resolved_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            refund_id, order_id, customer_id, product_id,
            amount, reason, "REQUESTED", "Under review for immediate processing", now, None
        ))
        conn.commit()
        conn.close()

        return {
            "refund_id": refund_id,
            "order_id": order_id,
            "amount": amount,
            "status": "REQUESTED",
            "reason": reason
        }

    @classmethod
    def process_refund(cls, refund_id: str, resolution_notes: str = "Approved per 14-day guarantee") -> Dict[str, Any]:
        """
        Approves and finalizes a refund, updating the revenue ledger.
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM refund_records WHERE refund_id = ?", (refund_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"Refund record {refund_id} not found.")

        now = datetime.now(timezone.utc).isoformat()
        order_id = row["order_id"]
        amount = row["amount"]

        # Update refund record
        cursor.execute("""
        UPDATE refund_records
        SET status = 'PROCESSED', owner_notes = ?, resolved_at = ?
        WHERE refund_id = ?
        """, (resolution_notes, now, refund_id))

        # Update revenue ledger
        cursor.execute("""
        UPDATE revenue_ledger
        SET payment_status = 'REFUNDED', refund_amount = ?, net_revenue = net_revenue - ?
        WHERE order_id = ?
        """, (amount, amount, order_id))

        conn.commit()
        conn.close()

        return {
            "refund_id": refund_id,
            "order_id": order_id,
            "amount_refunded": amount,
            "status": "PROCESSED",
            "resolved_at": now
        }

    @classmethod
    def get_refund_summary(cls) -> Dict[str, Any]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM refund_records")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()

        total_refunded = sum(r["amount"] for r in rows if r["status"] == "PROCESSED")
        return {
            "total_requests": len(rows),
            "processed_refunds": sum(1 for r in rows if r["status"] == "PROCESSED"),
            "total_refunded_usd": round(total_refunded, 2),
            "recent_refunds": rows[-5:]
        }
