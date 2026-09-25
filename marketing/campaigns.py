"""
Campaign Management & Multi-Channel Orchestration (Phase 5E, Section 9).

Manages marketing campaigns for 'PROD-LLM-EVAL-001' with explicit approval integration,
zero-cost budget enforcement ($0.00), and performance tracking.

Statuses:
  PLANNED -> DRAFT -> AWAITING_APPROVAL -> ACTIVE -> PAUSED -> COMPLETED (or FAILED)
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from core.db import get_connection
from core.firewall import FinancialFirewall, FinancialFirewallViolation
from approvals.manager import ApprovalManager

VALID_CAMPAIGN_STATUSES = {
    "PLANNED",
    "DRAFT",
    "AWAITING_APPROVAL",
    "ACTIVE",
    "PAUSED",
    "COMPLETED",
    "FAILED"
}


class CampaignManager:
    """
    Creates, validates, and manages marketing campaigns across organic channels.
    """

    @classmethod
    def create_campaign(
        cls,
        payload_or_name: Union[Dict[str, Any], str],
        **kwargs
    ) -> str:
        """
        Registers a new campaign. Default budget is $0.00 (Free-First Mode).
        Enforces FinancialFirewall on budget spend.
        Returns the campaign_id string.
        """
        if isinstance(payload_or_name, dict):
            data = payload_or_name
        else:
            data = {"name": payload_or_name}
            data.update(kwargs)

        name = data.get("name", "Organic Acquisition Campaign")
        objective = data.get("objective", "Acquisition")
        target_persona = data.get("target_persona", "Local LLM Developers")
        target_problem = data.get("target_problem", "Model drift and evaluation")
        channel = data.get("channel", "Community")
        employee_owner = data.get("employee_owner", "marketing_ai")
        product_id = data.get("product_id", "PROD-LLM-EVAL-001")
        experiment_hypothesis = data.get("experiment_hypothesis", "")
        success_metric = data.get("success_metric", "Qualified developer visits and initial sandbox checkouts")
        budget = float(data.get("budget", 0.0))
        owner_approval = bool(data.get("owner_approval", False))
        campaign_id = data.get("campaign_id") or f"CAMP-{int(datetime.now(timezone.utc).timestamp())}"

        # Financial Firewall validation: if budget > 0 without approval, reject!
        if budget > 0.0 and not owner_approval:
            raise FinancialFirewallViolation(
                f"Campaign '{name}' requested ${budget:.2f} exceeding $0.00 unapproved limit without owner authorization."
            )

        now = datetime.now(timezone.utc).isoformat()
        initial_status = data.get("status") or ("AWAITING_APPROVAL" if (budget > 0 and not owner_approval) else "ACTIVE")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO marketing_campaigns (
            campaign_id, name, objective, product_id, target_persona,
            target_problem, channel, start_time, budget, spend, status,
            owner_approval, employee_owner, experiment_hypothesis,
            success_metric, result, next_action, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            campaign_id, name, objective, product_id, target_persona,
            target_problem, channel, now, budget, 0.0, initial_status,
            1 if owner_approval else 0, employee_owner,
            experiment_hypothesis, success_metric,
            "Campaign initialized. Ready for activity execution.",
            "Draft high-value technical benchmarking guide.", now, now
        ))
        conn.commit()
        conn.close()

        return campaign_id

    @classmethod
    def get_campaigns(cls, limit: int = 50) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM marketing_campaigns ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @classmethod
    def list_campaigns(cls, limit: int = 50) -> List[Dict[str, Any]]:
        return cls.get_campaigns(limit)

    @classmethod
    def update_campaign_status(
        cls,
        campaign_id: str,
        new_status: str,
        result: Optional[str] = None,
        next_action: Optional[str] = None
    ) -> Dict[str, Any]:
        if new_status not in VALID_CAMPAIGN_STATUSES:
            raise ValueError(f"Invalid campaign status: {new_status}. Allowed: {VALID_CAMPAIGN_STATUSES}")

        now = datetime.now(timezone.utc).isoformat()
        conn = get_connection()
        cursor = conn.cursor()

        updates = ["status = ?", "updated_at = ?"]
        params = [new_status, now]

        if result:
            updates.append("result = ?")
            params.append(result)
        if next_action:
            updates.append("next_action = ?")
            params.append(next_action)

        params.append(campaign_id)
        cursor.execute(f"UPDATE marketing_campaigns SET {', '.join(updates)} WHERE campaign_id = ?", params)
        conn.commit()

        cursor.execute("SELECT * FROM marketing_campaigns WHERE campaign_id = ?", (campaign_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise ValueError(f"Campaign {campaign_id} not found.")
        return dict(row)
