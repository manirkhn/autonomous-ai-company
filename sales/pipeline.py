"""
Sales Pipeline & Lead Management Engine (EMP-006-SALES).
Maintains structured deal flow from discovery through to upsell.
ZERO SPAM POLICY: Mandates explicit consent and permission basis for any contact.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core.db import get_connection
from core.audit import AuditLogger

LEAD_STAGES = {
    "DISCOVERED", "QUALIFIED", "CONTACTED", "RESPONDED",
    "INTERESTED", "OFFERED", "PURCHASED", "DELIVERED",
    "SUPPORTED", "REPEAT_UPSELL", "LOST"
}

class SalesPipelineEngine:
    @staticmethod
    def create_lead(
        source: str,
        customer_type: str,
        problem: str,
        contact_method: str,
        consent_basis: str,
        product_id: Optional[str] = None,
        agent_id: str = "EMP-006-SALES"
    ) -> str:
        """Register a qualified prospect with explicit compliance consent basis."""
        if not consent_basis or "unsolicited" in consent_basis.lower():
            raise ValueError("SPAM POLICY VIOLATION: Cannot register lead without documented legitimate consent basis.")

        lead_id = f"LED-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sales_leads (
                lead_id, product_id, source, customer_type, problem,
                contact_method, status, consent_basis, outcome, next_action,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'DISCOVERED', ?, '', 'Qualify problem and alignment', ?, ?)
        """, (
            lead_id, product_id or "", source, customer_type, problem,
            contact_method, consent_basis, now, now
        ))
        conn.commit()
        conn.close()

        AuditLogger.log(
            agent_id=agent_id,
            action="SALES_LEAD_DISCOVERED",
            result=f"Lead {lead_id} ({customer_type}) logged via {source}. Consent: {consent_basis[:40]}",
            risk_level="LOW"
        )
        return lead_id

    @staticmethod
    def advance_lead_stage(
        lead_id: str,
        new_stage: str,
        outcome: str = "",
        next_action: str = "",
        agent_id: str = "EMP-006-SALES"
    ) -> bool:
        if new_stage.upper() not in LEAD_STAGES:
            raise ValueError(f"Invalid lead stage: {new_stage}")

        now = datetime.now(timezone.utc).isoformat()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE sales_leads SET 
                status = ?,
                outcome = CASE WHEN ? != '' THEN ? ELSE outcome END,
                next_action = CASE WHEN ? != '' THEN ? ELSE next_action END,
                updated_at = ?
            WHERE lead_id = ?
        """, (new_stage.upper(), outcome, outcome, next_action, next_action, now, lead_id))
        conn.commit()
        conn.close()

        AuditLogger.log(
            agent_id=agent_id,
            action="LEAD_STAGE_UPDATED",
            result=f"Lead {lead_id} advanced to stage {new_stage}. Outcome: {outcome}",
            risk_level="LOW"
        )
        return True

    @staticmethod
    def get_leads(status: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM sales_leads WHERE status = ? ORDER BY created_at DESC", (status.upper(),))
        else:
            cursor.execute("SELECT * FROM sales_leads ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
