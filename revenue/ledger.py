"""
Revenue Ledger & Financial Truth Engine (Phase 4, Parts 16, 17, 18 & 35).
Maintains strict separation between ESTIMATED, PENDING, VERIFIED, REFUNDED, and DISPUTED funds.
CRITICAL INVARIANT: Only VERIFIED revenue counts as actual company revenue.
Enforces the Owner Banking Air-Gap: AI has zero withdrawal or transfer permissions.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from core.db import get_connection

class BankingSecurityViolation(Exception):
    """Raised whenever unauthorized banking operations are attempted."""
    pass

class RevenueLedgerEngine:
    """
    Financial truth engine for tracking legitimate revenue transactions.
    """

    ALLOWED_PAYMENT_STATUSES = ["ESTIMATED", "PENDING", "VERIFIED", "REFUNDED", "DISPUTED"]

    @classmethod
    def record_transaction(
        cls,
        customer_id: str,
        product_id: str,
        order_id: str,
        amount: float,
        payment_status: str,
        payment_provider: str = "STRIPE_CHECKOUT",
        fees: float = 0.0,
        source: str = "ORGANIC",
        verification_evidence: str = "",
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """
        Records a transaction into the revenue ledger.
        """
        if payment_status not in cls.ALLOWED_PAYMENT_STATUSES:
            raise ValueError(f"Invalid payment status {payment_status}. Allowed: {cls.ALLOWED_PAYMENT_STATUSES}")

        # Verification check
        verification_status = "VERIFIED" if payment_status == "VERIFIED" else (
            "PENDING_CONFIRMATION" if payment_status == "PENDING" else "UNVERIFIED"
        )
        if payment_status == "VERIFIED" and not verification_evidence:
            raise ValueError("VERIFIED transactions require verifiable payment processor evidence or receipt ID.")

        revenue_id = f"REV-{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        now = datetime.now(timezone.utc).isoformat()
        net_revenue = amount - fees if payment_status in ["VERIFIED", "PENDING"] else 0.0

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO revenue_ledger (
            revenue_id, customer_id, product_id, order_id, amount,
            currency, payment_status, payment_provider, fees, refund_amount,
            net_revenue, date, source, verification_status, evidence
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            revenue_id, customer_id, product_id, order_id, amount,
            currency, payment_status, payment_provider, fees, 0.0,
            net_revenue, now, source, verification_status, verification_evidence
        ))
        conn.commit()
        conn.close()

        return {
            "revenue_id": revenue_id,
            "order_id": order_id,
            "amount": amount,
            "payment_status": payment_status,
            "verification_status": verification_status,
            "net_revenue": net_revenue
        }

    @classmethod
    def verify_payment(cls, revenue_id: str, processor_receipt_id: str) -> Dict[str, Any]:
        """
        Upgrades a PENDING transaction to VERIFIED upon receipt of legitimate processor confirmation.
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM revenue_ledger WHERE revenue_id = ?", (revenue_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"Transaction {revenue_id} not found.")

        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
        UPDATE revenue_ledger
        SET payment_status = 'VERIFIED', verification_status = 'VERIFIED', evidence = ?
        WHERE revenue_id = ?
        """, (f"Receipt: {processor_receipt_id}", revenue_id))
        conn.commit()
        conn.close()

        return {
            "revenue_id": revenue_id,
            "payment_status": "VERIFIED",
            "receipt_id": processor_receipt_id,
            "verified_at": now
        }

    @classmethod
    def get_revenue_metrics(cls) -> Dict[str, Any]:
        """
        Returns real-time revenue analytics for Today, This Week, and This Month.
        Strictly distinguishes ACTUAL (VERIFIED) from ESTIMATED and PENDING.
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM revenue_ledger")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()

        now = datetime.now(timezone.utc)
        today_str = now.strftime("%Y-%m-%d")
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        verified_total = sum(r["net_revenue"] for r in rows if r["payment_status"] == "VERIFIED")
        pending_total = sum(r["amount"] for r in rows if r["payment_status"] == "PENDING")
        estimated_total = sum(r["amount"] for r in rows if r["payment_status"] == "ESTIMATED")
        refunded_total = sum(r["refund_amount"] for r in rows if r["payment_status"] == "REFUNDED")

        # Time filters
        today_verified = sum(r["net_revenue"] for r in rows if r["payment_status"] == "VERIFIED" and r["date"].startswith(today_str))
        week_verified = sum(r["net_revenue"] for r in rows if r["payment_status"] == "VERIFIED" and datetime.fromisoformat(r["date"]) >= week_ago)
        month_verified = sum(r["net_revenue"] for r in rows if r["payment_status"] == "VERIFIED" and datetime.fromisoformat(r["date"]) >= month_ago)

        # Company operating mode
        operating_mode = "FIRST_REVENUE_MODE"
        if verified_total > 0:
            operating_mode = "VALIDATED_REVENUE_MODE"

        return {
            "all_time": {
                "verified_actual_revenue": round(verified_total, 2),
                "pending_revenue": round(pending_total, 2),
                "estimated_revenue": round(estimated_total, 2),
                "refunded_revenue": round(refunded_total, 2),
                "verified_transaction_count": sum(1 for r in rows if r["payment_status"] == "VERIFIED")
            },
            "today": {
                "verified_revenue": round(today_verified, 2),
                "pending_revenue": round(sum(r["amount"] for r in rows if r["payment_status"] == "PENDING" and r["date"].startswith(today_str)), 2)
            },
            "this_week": {
                "verified_revenue": round(week_verified, 2)
            },
            "this_month": {
                "verified_revenue": round(month_verified, 2)
            },
            "operating_mode": operating_mode,
            "banking_air_gap_enforced": True
        }

    @classmethod
    def attempt_banking_withdrawal(cls, amount: float) -> None:
        """
        Security Invariant enforcement: AI is strictly prohibited from executing banking withdrawals.
        """
        raise BankingSecurityViolation(
            "CRITICAL SECURITY BLOCK: AI is strictly prohibited from accessing, transferring, "
            "or withdrawing money from owner personal banking accounts."
        )
