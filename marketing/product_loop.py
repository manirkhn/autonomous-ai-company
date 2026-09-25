"""
Product Improvement Loop & Feedback Integration (Phase 5E, Section 24).

When marketing or customer research detects recurring developer objections or unmet needs:
  Research AI -> Product AI -> CEO AI
Generates structured product improvement proposals grounded in evidence.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from core.db import get_connection


class ProductImprovementLoop:
    """
    Manages data-driven product enhancement proposals.
    """

    @classmethod
    def create_proposal(
        cls,
        payload_or_problem: Union[Dict[str, Any], str],
        **kwargs
    ) -> str:
        """
        Creates a product improvement proposal.
        Accepts dict payload or kwargs. Returns proposal_id.
        """
        if isinstance(payload_or_problem, dict):
            data = payload_or_problem
        else:
            data = {"customer_problem": payload_or_problem}
            data.update(kwargs)

        proposal_id = data.get("proposal_id") or f"PIP-{int(datetime.now(timezone.utc).timestamp())}"
        product_id = data.get("product_id", "PROD-LLM-EVAL-001")
        customer_problem = data.get("customer_problem", "Developer workflow friction")
        evidence = data.get("evidence", "Observed in community discussion")
        proposed_change = data.get("proposed_change", "Feature enhancement")
        expected_benefit = data.get("expected_benefit", "Improve conversion and satisfaction")
        status = data.get("status", "PROPOSED")
        now = datetime.now(timezone.utc).isoformat()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO product_improvement_proposals (
            proposal_id, product_id, customer_problem, evidence,
            proposed_change, expected_benefit, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            proposal_id, product_id, customer_problem, evidence,
            proposed_change, expected_benefit, status, now
        ))
        conn.commit()
        conn.close()

        return proposal_id

    @classmethod
    def propose_improvement(
        cls,
        customer_problem: str,
        evidence: str,
        proposed_change: str,
        expected_benefit: str,
        product_id: str = "PROD-LLM-EVAL-001"
    ) -> Dict[str, Any]:
        prop_id = cls.create_proposal({
            "customer_problem": customer_problem,
            "evidence": evidence,
            "proposed_change": proposed_change,
            "expected_benefit": expected_benefit,
            "product_id": product_id
        })
        return {
            "proposal_id": prop_id,
            "product_id": product_id,
            "proposed_change": proposed_change,
            "status": "PROPOSED"
        }

    @classmethod
    def update_proposal_status(
        cls,
        proposal_id: str,
        status: str,
        actual_outcome: Optional[str] = None
    ) -> bool:
        """Updates proposal status (PROPOSED, APPROVED, IMPLEMENTED, REJECTED)."""
        conn = get_connection()
        cursor = conn.cursor()
        if actual_outcome:
            cursor.execute(
                "UPDATE product_improvement_proposals SET status = ?, actual_outcome = ? WHERE proposal_id = ?",
                (status, actual_outcome, proposal_id)
            )
        else:
            cursor.execute(
                "UPDATE product_improvement_proposals SET status = ? WHERE proposal_id = ?",
                (status, proposal_id)
            )
        changed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return changed

    @classmethod
    def get_proposals(cls, limit: int = 20) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM product_improvement_proposals ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @classmethod
    def list_proposals(cls, limit: int = 20) -> List[Dict[str, Any]]:
        return cls.get_proposals(limit)
