"""
Owner Settlement Engine & Payout Tracking (Phase 5D, Sections 17 & 18).

Tracks verifiable payouts from the payment provider to the owner's bank account.
Statuses:
  SETTLEMENT_PENDING -> SETTLEMENT_PROCESSING -> SETTLEMENT_COMPLETED (or SETTLEMENT_FAILED)

CRITICAL INVARIANTS:
1. NEVER infer settlement from payment confirmation alone.
2. The AI must never claim funds reached the owner's bank account without verifiable settlement evidence.
3. Air-gap preserved: only masked destination references (e.g. '****1234') are stored.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core.db import get_connection
from payments.owner_settlement import OwnerSettlementManager

VALID_SETTLEMENT_STATUSES = {
    "SETTLEMENT_PENDING",
    "SETTLEMENT_PROCESSING",
    "SETTLEMENT_COMPLETED",
    "SETTLEMENT_FAILED"
}

class SettlementManager:
    """
    Manages and reports on provider-to-bank settlement cycles.
    """

    @classmethod
    def record_settlement(
        cls,
        settlement_amount: float,
        currency: str = "AED",
        provider: str = "STRIPE_UAE",
        status: str = "SETTLEMENT_PENDING",
        provider_reference: str = "",
        settlement_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Records a new settlement event with the masked destination reference.
        """
        if status not in VALID_SETTLEMENT_STATUSES:
            raise ValueError(f"Invalid settlement status: {status}. Allowed: {VALID_SETTLEMENT_STATUSES}")

        profile = OwnerSettlementManager.get_profile()
        masked_ref = profile.get("masked_destination_reference", "****1234")

        settlement_id = f"SETTLE-{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        now = datetime.now(timezone.utc).isoformat()
        date_str = settlement_date or now

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO settlements (
            settlement_id, provider, settlement_amount, currency,
            settlement_date, status, masked_destination_reference,
            provider_reference, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            settlement_id, provider, settlement_amount, currency,
            date_str, status, masked_ref, provider_reference, now, now
        ))
        conn.commit()
        conn.close()

        return {
            "settlement_id": settlement_id,
            "provider": provider,
            "settlement_amount": settlement_amount,
            "currency": currency,
            "status": status,
            "masked_destination": masked_ref,
            "provider_reference": provider_reference,
            "settlement_date": date_str
        }

    @classmethod
    def update_settlement_status(
        cls,
        settlement_id: str,
        new_status: str,
        provider_reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Updates settlement status based on authentic payment provider payout notification.
        """
        if new_status not in VALID_SETTLEMENT_STATUSES:
            raise ValueError(f"Invalid settlement status: {new_status}")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM settlements WHERE settlement_id = ?", (settlement_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"Settlement '{settlement_id}' not found.")

        now = datetime.now(timezone.utc).isoformat()
        updates = ["status = ?", "updated_at = ?"]
        params = [new_status, now]

        if provider_reference:
            updates.append("provider_reference = ?")
            params.append(provider_reference)

        params.append(settlement_id)
        cursor.execute(f"UPDATE settlements SET {', '.join(updates)} WHERE settlement_id = ?", params)
        conn.commit()

        cursor.execute("SELECT * FROM settlements WHERE settlement_id = ?", (settlement_id,))
        updated = dict(cursor.fetchone())
        conn.close()

        return updated

    @classmethod
    def get_settlement_summary(cls) -> Dict[str, Any]:
        """
        Returns aggregated settlement metrics for dashboard and CEO reports.
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM settlements ORDER BY settlement_date DESC")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()

        pending_total = sum(r["settlement_amount"] for r in rows if r["status"] == "SETTLEMENT_PENDING")
        completed_total = sum(r["settlement_amount"] for r in rows if r["status"] == "SETTLEMENT_COMPLETED")
        failed_total = sum(r["settlement_amount"] for r in rows if r["status"] == "SETTLEMENT_FAILED")

        return {
            "pending_settlements_total": round(pending_total, 2),
            "completed_settlements_total": round(completed_total, 2),
            "failed_settlements_total": round(failed_total, 2),
            "total_settlements_count": len(rows),
            "settlements": rows[:20]
        }

    @classmethod
    def get_where_did_money_go_flow(cls, order_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Section 17: 'Where Did The Money Go?' visual audit pipeline.
        Traces customer funds from payment capture to bank settlement.
        """
        conn = get_connection()
        cursor = conn.cursor()

        tx = None
        if order_id:
            cursor.execute("SELECT * FROM payment_transactions WHERE order_id = ?", (order_id,))
            r = cursor.fetchone()
            if r:
                tx = dict(r)

        if not tx:
            # Get latest verified or most recent transaction
            cursor.execute("""
            SELECT * FROM payment_transactions
            ORDER BY CASE WHEN payment_status = 'PAYMENT_VERIFIED' THEN 1 ELSE 2 END, created_at DESC
            LIMIT 1
            """)
            r = cursor.fetchone()
            if r:
                tx = dict(r)

        conn.close()

        profile = OwnerSettlementManager.get_profile()

        if not tx:
            # Baseline architecture display
            return {
                "sample_order_id": "ORD-SAMPLE",
                "amount_display": "AED 106.50 ($29.00 USD)",
                "steps": [
                    {"step": 1, "name": "CUSTOMER PAID", "status": "READY", "badge": "🟢 READY", "detail": "Customer initiates checkout via secure checkout link."},
                    {"step": 2, "name": "PAYMENT PROVIDER RECEIVED", "status": "READY", "badge": "🟢 READY", "detail": "Stripe UAE / Gateway receives authorized funds."},
                    {"step": 3, "name": "PAYMENT VERIFIED", "status": "VERIFIED_LOGIC", "badge": "🟢 SECURE", "detail": "HMAC-SHA256 webhook verified with anti-replay."},
                    {"step": 4, "name": "REVENUE LEDGER RECORDED", "status": "CONNECTED", "badge": "🟢 CONNECTED", "detail": "Deterministic ledger records actual revenue."},
                    {"step": 5, "name": "PROVIDER FEE", "status": "DETERMINISTIC", "badge": "🟢 2.9% + 1 AED", "detail": "Gateway processing fee deducted automatically."},
                    {"step": 6, "name": "SETTLEMENT", "status": "PENDING", "badge": "🟡 PENDING", "detail": "Scheduled rolling payout (T+2/T+3 days)."},
                    {"step": 7, "name": "OWNER'S DESIGNATED ACCOUNT", "status": "AIR_GAPPED", "badge": "🔒 OWNER-ONLY", "detail": f"{profile.get('bank_name')} ({profile.get('masked_destination_reference')})"}
                ]
            }

        # Dynamic trace based on actual transaction
        status = tx["payment_status"]
        is_verified = status in ["PAYMENT_VERIFIED", "SETTLEMENT_PENDING", "SETTLEMENT_COMPLETED"]
        is_settled = status == "SETTLEMENT_COMPLETED"

        return {
            "order_id": tx["order_id"],
            "product_name": tx["product_name"],
            "amount": tx["amount"],
            "currency": tx["currency"],
            "mode": tx["mode"],
            "steps": [
                {
                    "step": 1,
                    "name": "CUSTOMER PAID",
                    "status": "COMPLETED",
                    "badge": "🟢 PAID",
                    "detail": f"{tx['customer_email']} paid {tx['currency']} {tx['amount']:.2f}"
                },
                {
                    "step": 2,
                    "name": "PAYMENT PROVIDER RECEIVED",
                    "status": "RECEIVED" if is_verified else "PENDING",
                    "badge": "🟢 RECEIVED" if is_verified else "🟡 PENDING",
                    "detail": f"{tx['provider']} Payment ID: {tx.get('provider_payment_id') or 'Pending'}"
                },
                {
                    "step": 3,
                    "name": "PAYMENT VERIFIED",
                    "status": "VERIFIED" if is_verified else "UNVERIFIED",
                    "badge": "🟢 VERIFIED" if is_verified else "🟡 PENDING",
                    "detail": "Verified by cryptographic webhook signature" if is_verified else "Awaiting webhook confirmation"
                },
                {
                    "step": 4,
                    "name": "REVENUE LEDGER RECORDED",
                    "status": "RECORDED" if is_verified and tx['mode'] == 'PRODUCTION' else ("TEST_ISOLATED" if tx['mode'] == 'TEST' else "PENDING"),
                    "badge": "🟢 RECORDED" if is_verified and tx['mode'] == 'PRODUCTION' else ("🟣 TEST ISOLATED" if tx['mode'] == 'TEST' else "🟡 PENDING"),
                    "detail": "Logged into production ledger" if is_verified and tx['mode'] == 'PRODUCTION' else ("Test transaction kept out of production ledger" if tx['mode'] == 'TEST' else "Pending verification")
                },
                {
                    "step": 5,
                    "name": "PROVIDER FEE",
                    "status": "DEDUCTED",
                    "badge": f"🟢 {tx['currency']} {tx['provider_fee']:.2f}",
                    "detail": f"Net merchant revenue: {tx['currency']} {tx['net_amount']:.2f}"
                },
                {
                    "step": 6,
                    "name": "SETTLEMENT",
                    "status": "COMPLETED" if is_settled else "PENDING",
                    "badge": "🟢 SETTLED" if is_settled else "🟡 PENDING",
                    "detail": "Payout transfer executed by provider" if is_settled else "Pending scheduled provider payout cycle"
                },
                {
                    "step": 7,
                    "name": "OWNER'S DESIGNATED ACCOUNT",
                    "status": "AIR_GAPPED",
                    "badge": "🔒 OWNER-ONLY",
                    "detail": f"{profile.get('bank_name')} ({profile.get('masked_destination_reference')})"
                }
            ]
        }
