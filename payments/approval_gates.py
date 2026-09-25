"""
Owner Payment Approval Gates (Phase 5D, Section 15).

Enforces explicit owner controls:
  1. PAYMENT_PROVIDER_ACTIVATION_APPROVAL: Prevents activating live payment gateways without owner sign-off.
  2. SETTLEMENT_DESTINATION_APPROVAL: Requires owner approval before setting or changing payout destinations.
  3. AUTOMATIC_REFUND_APPROVAL: Defaults to False (refunds require owner review before submission).
  4. PAID_INFRASTRUCTURE_APPROVAL: Preserves $0.00 spending limit on cloud infrastructure.
  5. PAID_API_APPROVAL: Preserves $0.00 spending limit on third-party APIs.

Default for all gates: FALSE.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from core.db import get_connection

DEFAULT_GATES = [
    {
        "gate_key": "PAYMENT_PROVIDER_ACTIVATION_APPROVAL",
        "title": "Payment Provider Activation Approval",
        "is_approved": 0,
        "notes": "Requires owner authorization before connecting live production merchant keys."
    },
    {
        "gate_key": "SETTLEMENT_DESTINATION_APPROVAL",
        "title": "Settlement Destination Approval",
        "is_approved": 0,
        "notes": "Requires owner authorization before establishing Emirates Islamic payout link."
    },
    {
        "gate_key": "AUTOMATIC_REFUND_APPROVAL",
        "title": "Automatic Refunds Approval",
        "is_approved": 0,
        "notes": "When False, all refund requests require manual owner review."
    },
    {
        "gate_key": "PAID_INFRASTRUCTURE_APPROVAL",
        "title": "Paid Infrastructure Approval",
        "is_approved": 0,
        "notes": "Strict $0 unapproved spending ceiling on cloud resources."
    },
    {
        "gate_key": "PAID_API_APPROVAL",
        "title": "Paid API Usage Approval",
        "is_approved": 0,
        "notes": "Strict $0 unapproved spending ceiling on external API tokens."
    }
]

class PaymentApprovalGates:
    """
    Manages explicit owner security and governance gates.
    """

    @classmethod
    def get_all_gates(cls) -> Dict[str, Any]:
        """
        Retrieves current gate statuses from DB, initializing defaults if needed.
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM payment_approval_gates")
        rows = cursor.fetchall()

        if not rows:
            now = datetime.now(timezone.utc).isoformat()
            for gate in DEFAULT_GATES:
                cursor.execute("""
                INSERT OR IGNORE INTO payment_approval_gates (gate_key, title, is_approved, approved_by, approved_at, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (gate["gate_key"], gate["title"], gate["is_approved"], None, None, gate["notes"]))
            conn.commit()
            cursor.execute("SELECT * FROM payment_approval_gates")
            rows = cursor.fetchall()

        conn.close()
        gates_dict = {}
        for r in rows:
            d = dict(r)
            d["is_approved"] = bool(d["is_approved"])
            gates_dict[d["gate_key"]] = d
        return gates_dict

    @classmethod
    def is_gate_approved(cls, gate_key: str) -> bool:
        """
        Returns whether a specific gate is approved by the owner.
        """
        gates = cls.get_all_gates()
        gate = gates.get(gate_key)
        return bool(gate and gate.get("is_approved"))

    @classmethod
    def update_gate(
        cls,
        gate_key: str,
        is_approved: bool,
        approved_by: str = "OWNER",
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        Updates owner approval status on a gate.
        """
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()

        cursor.execute("""
        UPDATE payment_approval_gates
        SET is_approved = ?, approved_by = ?, approved_at = ?, notes = ?
        WHERE gate_key = ?
        """, (
            1 if is_approved else 0,
            approved_by,
            now if is_approved else None,
            notes,
            gate_key
        ))
        conn.commit()
        conn.close()

        return cls.get_all_gates().get(gate_key, {})
