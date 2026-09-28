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
            "status": "ACTION_REQUIRED",
            "why": "Gumroad requires account registration and direct bank payout configuration by the legal account owner. API does not permit third-party autonomous account creation.",
            "what_is_blocked": "Distribution on Gumroad marketplace and automated digital delivery through Gumroad checkout.",
            "exact_action": "1. Open Gumroad.com and log in/register. 2. Copy listing title/description from integrations/gumroad/owner_action_package.json. 3. Enter your payout bank in Gumroad Settings.",
            "estimated_time": "3 minutes",
            "platform": "Gumroad",
            "security_impact": "Zero financial risk. Antigravity never handles bank passwords, OTPs, or withdrawal credentials.",
            "what_antigravity_will_do_after_completion": "Antigravity will automatically monitor sales via Gumroad API, reconcile orders, deliver updates, and track marketing attribution."
        },
        {
            "action_id": "ACT-002-LEMONSQUEEZY-KYC",
            "title": "Connect Lemon Squeezy and submit KYC/KYB business verification",
            "category": "MARKETPLACE_ONBOARDING",
            "urgency": "HIGH",
            "description": "Submit business entity documentation and owner identity verification on LemonSqueezy.com for Merchant of Record automated VAT/tax checkout activation.",
            "channel": "Lemon Squeezy",
            "status": "ACTION_REQUIRED",
            "why": "Lemon Squeezy operates as a Merchant of Record (MoR) and mandates legal entity KYC/KYB identity verification under anti-money laundering regulations.",
            "what_is_blocked": "Global multi-currency checkout with automated global VAT/GST remittance.",
            "exact_action": "1. Open lemonsqueezy.com -> Complete merchant profile. 2. Submit government ID and business details. 3. Generate API Key with 'read,write' permissions and add to server config.",
            "estimated_time": "5 minutes",
            "platform": "Lemon Squeezy",
            "security_impact": "Zero financial risk. Antigravity operates via scoped REST API tokens and cannot initiate payouts or alter bank destinations.",
            "what_antigravity_will_do_after_completion": "Antigravity will autonomously create products, sync variants, generate dynamic checkout links, and process webhook fulfillment events."
        },
        {
            "action_id": "ACT-003-APPROVE-REDDIT-OUTREACH",
            "title": "Review and approve Reddit r/LocalLLaMA technical outreach response",
            "category": "COMMUNITY_OUTREACH",
            "urgency": "MEDIUM",
            "description": "Inspect drafted educational reply regarding quantization prompt regression before publishing to ensure strict compliance with r/LocalLLaMA community rules.",
            "channel": "Reddit",
            "status": "ACTION_REQUIRED",
            "why": "Reddit platform rules and subreddit moderators strictly penalize unverified bot posting. Human oversight guarantees authentic, non-spam technical assistance.",
            "what_is_blocked": "Publishing genuine technical response to r/LocalLLaMA developer query on quantization regression.",
            "exact_action": "1. Review prepared technical response in distribution manager. 2. Verify link points to open-source docs. 3. Click 'Approve' to authorize publication.",
            "estimated_time": "1 minute",
            "platform": "Reddit",
            "security_impact": "Zero financial or security risk. Outreach contains strictly public technical benchmark insights.",
            "what_antigravity_will_do_after_completion": "Antigravity publishes response, monitors thread interactions, and logs conversion attribution without spamming."
        },
        {
            "action_id": "ACT-004-PRODUCT-HUNT-LAUNCH",
            "title": "Approve Product Hunt launch date and maker profile submission",
            "category": "MARKETPLACE_LAUNCH",
            "urgency": "MEDIUM",
            "description": "Authorize scheduled Product Hunt launch package and designate primary maker profile for launch day community Q&A.",
            "channel": "Product Hunt",
            "status": "ACTION_REQUIRED",
            "why": "Product Hunt requires a verified maker profile to claim submissions and host launch-day discussions.",
            "what_is_blocked": "Public scheduling of Product Hunt feature launch.",
            "exact_action": "1. Review generated tagline, gallery screenshots, and first comment. 2. Confirm launch date. 3. Click 'Authorize Launch'.",
            "estimated_time": "2 minutes",
            "platform": "Product Hunt",
            "security_impact": "Zero risk. All copy and media are pre-generated by Antigravity.",
            "what_antigravity_will_do_after_completion": "Antigravity submits scheduled payload via Product Hunt v2 GraphQL API and tracks launch day leaderboard status."
        }
    ]

    @classmethod
    def init_actions(cls):
        conn = get_connection()
        cursor = conn.cursor()
        now_iso = datetime.now(timezone.utc).isoformat()

        for act in cls.INITIAL_ACTIONS:
            cursor.execute("SELECT action_id FROM owner_actions WHERE action_id = ?", (act["action_id"],))
            existing = cursor.fetchone()
            if not existing:
                cursor.execute("""
                INSERT INTO owner_actions (
                    action_id, title, category, urgency, description, channel, status, created_at,
                    why, what_is_blocked, exact_action, estimated_time, platform, security_impact, what_antigravity_will_do_after_completion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    act["action_id"], act["title"], act["category"], act["urgency"],
                    act["description"], act["channel"], act["status"], now_iso,
                    act.get("why", ""), act.get("what_is_blocked", ""), act.get("exact_action", ""),
                    act.get("estimated_time", "5 mins"), act.get("platform", act["channel"]),
                    act.get("security_impact", "Zero financial risk"),
                    act.get("what_antigravity_will_do_after_completion", "")
                ))

        conn.commit()
        conn.close()

    @classmethod
    def create_action(cls, action_id: str, title: str, category: str, urgency: str,
                      description: str, channel: str, why: str = "", what_is_blocked: str = "",
                      exact_action: str = "", estimated_time: str = "5 mins", platform: str = "",
                      security_impact: str = "Zero financial risk",
                      what_antigravity_will_do_after_completion: str = "") -> Dict[str, Any]:
        """Dynamically register a new owner action with full justification fields."""
        conn = get_connection()
        cursor = conn.cursor()
        now_iso = datetime.now(timezone.utc).isoformat()
        
        cursor.execute("SELECT action_id FROM owner_actions WHERE action_id = ?", (action_id,))
        if cursor.fetchone():
            conn.close()
            return {"status": "EXISTS", "action_id": action_id}

        cursor.execute("""
        INSERT INTO owner_actions (
            action_id, title, category, urgency, description, channel, status, created_at,
            why, what_is_blocked, exact_action, estimated_time, platform, security_impact,
            what_antigravity_will_do_after_completion
        ) VALUES (?, ?, ?, ?, ?, ?, 'ACTION_REQUIRED', ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            action_id, title, category, urgency, description, channel, now_iso,
            why, what_is_blocked, exact_action, estimated_time, platform or channel,
            security_impact, what_antigravity_will_do_after_completion
        ))
        conn.commit()
        conn.close()
        return {
            "status": "CREATED",
            "action_id": action_id,
            "title": title,
            "urgency": urgency,
            "platform": platform or channel
        }

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
