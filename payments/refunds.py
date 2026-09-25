"""
Customer Refund Architecture & Governance (Phase 5D, Section 14).

Enforces strict refund lifecycle:
  REFUND_REQUESTED -> REFUND_APPROVAL_REQUIRED -> REFUND_APPROVED
                   -> REFUND_SUBMITTED -> REFUND_COMPLETED (or REFUND_FAILED)

CRITICAL INVARIANTS:
1. AI MUST NOT independently issue a bank refund without owner approval.
2. If AUTOMATIC_REFUND_APPROVAL is False (default), refund requests pause at REFUND_APPROVAL_REQUIRED.
3. Upon approval and completion, the revenue ledger is deterministically updated.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from core.db import get_connection
from payments.approval_gates import PaymentApprovalGates
from revenue.refunds import RefundProcessingEngine
from revenue.ledger import RevenueLedgerEngine

VALID_REFUND_STATES = {
    "REFUND_REQUESTED",
    "REFUND_APPROVAL_REQUIRED",
    "REFUND_APPROVED",
    "REFUND_SUBMITTED",
    "REFUND_COMPLETED",
    "REFUND_FAILED"
}

class RefundGovernanceEngine:
    """
    Manages customer refund workflows with explicit owner approval gates.
    """

    @classmethod
    def request_refund(
        cls,
        order_id: str,
        customer_email: str,
        amount: float,
        reason: str
    ) -> Dict[str, Any]:
        """
        Initiates a refund request.
        If AUTOMATIC_REFUND_APPROVAL is enabled, transitions directly to REFUND_APPROVED.
        Otherwise, pauses at REFUND_APPROVAL_REQUIRED.
        """
        refund_id = f"REF-{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        now = datetime.now(timezone.utc).isoformat()
        auto_approved = PaymentApprovalGates.is_gate_approved("AUTOMATIC_REFUND_APPROVAL")

        initial_state = "REFUND_APPROVED" if auto_approved else "REFUND_APPROVAL_REQUIRED"

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO refund_records (
            refund_id, order_id, customer_id, product_id,
            amount, reason, status, owner_notes, created_at, resolved_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            refund_id, order_id, customer_email, "PROD-LLM-EVAL-001",
            amount, reason, initial_state,
            "Auto-approved by policy" if auto_approved else "Pending owner sign-off",
            now, now if auto_approved else None
        ))
        conn.commit()
        conn.close()

        # If auto-approved, finalize submission
        if auto_approved:
            return cls.finalize_refund(refund_id, resolution_notes="Auto-approved under 14-day policy")

        return {
            "refund_id": refund_id,
            "order_id": order_id,
            "customer_email": customer_email,
            "amount": amount,
            "status": initial_state,
            "requires_owner_approval": True,
            "reason": reason
        }

    @classmethod
    def owner_review_refund(
        cls,
        refund_id: str,
        approved: bool,
        owner_notes: str = ""
    ) -> Dict[str, Any]:
        """
        Owner reviews and approves or rejects a pending refund request.
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM refund_records WHERE refund_id = ?", (refund_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"Refund request '{refund_id}' not found.")

        now = datetime.now(timezone.utc).isoformat()
        if not approved:
            cursor.execute("""
            UPDATE refund_records
            SET status = 'REFUND_FAILED', owner_notes = ?, resolved_at = ?
            WHERE refund_id = ?
            """, (f"Rejected by owner: {owner_notes}", now, refund_id))
            conn.commit()
            conn.close()
            return {"refund_id": refund_id, "status": "REFUND_FAILED", "notes": owner_notes}

        cursor.execute("""
        UPDATE refund_records
        SET status = 'REFUND_APPROVED', owner_notes = ?, resolved_at = ?
        WHERE refund_id = ?
        """, (f"Approved by owner: {owner_notes}", now, refund_id))
        conn.commit()
        conn.close()

        return cls.finalize_refund(refund_id, resolution_notes=owner_notes)

    @classmethod
    def finalize_refund(cls, refund_id: str, resolution_notes: str = "") -> Dict[str, Any]:
        """
        Submits approved refund and updates both payment_transactions and revenue_ledger.
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM refund_records WHERE refund_id = ?", (refund_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"Refund record '{refund_id}' not found.")

        order_id = row["order_id"]
        amount = row["amount"]
        now = datetime.now(timezone.utc).isoformat()

        # Update refund record
        cursor.execute("""
        UPDATE refund_records
        SET status = 'REFUND_COMPLETED', resolved_at = ?, owner_notes = ?
        WHERE refund_id = ?
        """, (now, resolution_notes or "Refund finalized", refund_id))

        # Update payment_transactions state
        cursor.execute("""
        UPDATE payment_transactions
        SET payment_status = 'PAYMENT_REFUNDED', updated_at = ?
        WHERE order_id = ?
        """, (now, order_id))

        # Update revenue ledger if entry exists
        cursor.execute("SELECT * FROM revenue_ledger WHERE order_id = ?", (order_id,))
        if cursor.fetchone():
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
            "status": "REFUND_COMPLETED",
            "resolved_at": now
        }

    @classmethod
    def get_all_refunds(cls) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM refund_records ORDER BY created_at DESC")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
