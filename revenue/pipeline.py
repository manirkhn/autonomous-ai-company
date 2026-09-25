"""
Sales Pipeline & Customer Lifecycle Engine (Phase 4, Part 15).
Tracks customer leads through 13 standardized stages from DISCOVERED to RETAINED or LOST.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core.db import get_connection

VALID_STAGES = [
    "DISCOVERED",
    "QUALIFIED",
    "CONTACTED",
    "RESPONDED",
    "INTERESTED",
    "OFFERED",
    "CHECKOUT",
    "PAID",
    "DELIVERED",
    "SUPPORTED",
    "RETAINED",
    "REFUNDED",
    "LOST"
]

class SalesPipelineEngine:
    """
    Manages lead progression through the 13 sales stages with timing and conversion metrics.
    """

    @classmethod
    def create_lead(
        cls,
        product_id: str,
        customer_ref: str,
        source: str,
        customer_type: str,
        problem: str,
        consent_basis: str = "INBOUND_INQUIRY"
    ) -> str:
        lead_id = f"LEAD-{int(datetime.now(timezone.utc).timestamp())}"
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()

        cursor.execute("""
        INSERT INTO sales_leads (
            lead_id, product_id, source, customer_type, problem,
            contact_method, status, consent_basis, outcome, next_action,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lead_id, product_id, source, customer_type, problem,
            "EMAIL_OR_WEB", "DISCOVERED", consent_basis, "IN_PROGRESS",
            "Evaluate qualification criteria", now, now
        ))
        conn.commit()
        conn.close()
        return lead_id

    @classmethod
    def advance_stage(cls, lead_id: str, new_stage: str, outcome_notes: str = "") -> Dict[str, Any]:
        if new_stage not in VALID_STAGES:
            raise ValueError(f"Invalid pipeline stage: {new_stage}. Valid stages: {VALID_STAGES}")

        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()

        cursor.execute("SELECT status FROM sales_leads WHERE lead_id = ?", (lead_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"Lead {lead_id} not found.")

        old_stage = row["status"]
        cursor.execute("""
        UPDATE sales_leads
        SET status = ?, outcome = ?, updated_at = ?
        WHERE lead_id = ?
        """, (new_stage, outcome_notes or f"Advanced from {old_stage} to {new_stage}", now, lead_id))
        conn.commit()
        conn.close()

        return {
            "lead_id": lead_id,
            "previous_stage": old_stage,
            "current_stage": new_stage,
            "updated_at": now
        }

    @classmethod
    def get_pipeline_summary(cls) -> Dict[str, Any]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT status, COUNT(*) as cnt FROM sales_leads GROUP BY status")
        rows = cursor.fetchall()
        conn.close()

        stage_counts = {stage: 0 for stage in VALID_STAGES}
        total_leads = 0
        for r in rows:
            st = r["status"]
            cnt = r["cnt"]
            if st in stage_counts:
                stage_counts[st] = cnt
            total_leads += cnt

        paid_count = stage_counts["PAID"] + stage_counts["DELIVERED"] + stage_counts["SUPPORTED"] + stage_counts["RETAINED"]
        conversion_rate = round((paid_count / total_leads * 100.0), 2) if total_leads > 0 else 0.0

        return {
            "total_leads": total_leads,
            "stage_breakdown": stage_counts,
            "paid_customers": paid_count,
            "conversion_rate_percentage": conversion_rate
        }
