"""
Owner Action Center (Phase 5H, Section 14).

Maintains a rigorous, transparent ledger of actions requiring human owner execution
(e.g., setting up legal payout entities, KYC verification, approving external posts).
Never pretends or fabricates that external owner requirements are completed.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core.db import get_connection

class OwnerActionCenter:
    """
    Manages explicit owner intervention items.
    """

    INITIAL_ACTIONS = [
        {
            "action_id": "ACT-001-GUMROAD-SETUP",
            "title": "Create Gumroad account and connect payout destination",
            "category": "MARKETPLACE_ONBOARDING",
            "urgency": "HIGH",
            "description": "Register Nexora AI Labs profile on Gumroad.com, paste product copy from GumroadMarketplaceEngine, and attach business bank payout details.",
            "channel": "Gumroad",
            "status": "ACTION_REQUIRED"
        },
        {
            "action_id": "ACT-002-LEMONSQUEEZY-KYC",
            "title": "Connect Lemon Squeezy and submit KYC/KYB business verification",
            "category": "MARKETPLACE_ONBOARDING",
            "urgency": "HIGH",
            "description": "Submit business entity documentation and owner identity verification on LemonSqueezy.com for Merchant of Record automated VAT/tax checkout activation.",
            "channel": "Lemon Squeezy",
            "status": "ACTION_REQUIRED"
        },
        {
            "action_id": "ACT-003-APPROVE-REDDIT-OUTREACH",
            "title": "Review and approve Reddit r/LocalLLaMA technical outreach response",
            "category": "COMMUNITY_OUTREACH",
            "urgency": "MEDIUM",
            "description": "Inspect drafted educational reply regarding quantization prompt regression before publishing to ensure strict compliance with r/LocalLLaMA community rules.",
            "channel": "Reddit",
            "status": "ACTION_REQUIRED"
        },
        {
            "action_id": "ACT-004-PRODUCT-HUNT-LAUNCH",
            "title": "Approve Product Hunt launch date and maker profile submission",
            "category": "MARKETPLACE_LAUNCH",
            "urgency": "MEDIUM",
            "description": "Authorize scheduled Product Hunt launch package and designate primary maker profile for launch day community Q&A.",
            "channel": "Product Hunt",
            "status": "ACTION_REQUIRED"
        }
    ]

    @classmethod
    def init_actions(cls):
        conn = get_connection()
        cursor = conn.cursor()
        now_iso = datetime.now(timezone.utc).isoformat()

        for act in cls.INITIAL_ACTIONS:
            cursor.execute("SELECT action_id FROM owner_actions WHERE action_id = ?", (act["action_id"],))
            if not cursor.fetchone():
                cursor.execute("""
                INSERT INTO owner_actions (
                    action_id, title, category, urgency, description, channel, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    act["action_id"], act["title"], act["category"], act["urgency"],
                    act["description"], act["channel"], act["status"], now_iso
                ))

        conn.commit()
        conn.close()

    @classmethod
    def list_actions(cls, status: Optional[str] = None) -> List[Dict[str, Any]]:
        cls.init_actions()
        conn = get_connection()
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM owner_actions WHERE status = ? ORDER BY urgency DESC, created_at ASC", (status,))
        else:
            cursor.execute("SELECT * FROM owner_actions ORDER BY urgency DESC, created_at ASC")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @classmethod
    def get_pending_actions(cls) -> List[Dict[str, Any]]:
        return cls.list_actions(status="ACTION_REQUIRED")

    @classmethod
    def resolve_action(cls, action_id: str, resolution_notes: str = "Resolved by owner") -> Dict[str, Any]:
        conn = get_connection()
        cursor = conn.cursor()
        now_iso = datetime.now(timezone.utc).isoformat()
        cursor.execute("UPDATE owner_actions SET status = 'COMPLETED', completed_at = ? WHERE action_id = ?", (now_iso, action_id))
        conn.commit()
        conn.close()
        return {"status": "COMPLETED", "action_id": action_id, "resolution": "COMPLETED", "timestamp": now_iso}

    @classmethod
    def complete_action(cls, action_id: str, resolution_notes: str = "Completed by owner") -> Dict[str, Any]:
        return cls.resolve_action(action_id=action_id, resolution_notes=resolution_notes)
