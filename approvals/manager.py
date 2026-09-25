"""
Human Approval Center.
Enforces the owner's ultimate decision-making power over high-risk, legal,
financial, and reputation-sensitive operations.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core.db import get_connection
from core.audit import AuditLogger
from core.firewall import FinancialFirewall

APPROVAL_STATUSES = {"PENDING", "APPROVED", "REJECTED", "INFO_REQUESTED", "PAUSED"}
RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

class ApprovalManager:
    @staticmethod
    def create_approval_request(
        requesting_agent: str,
        what: str,
        why: str,
        expected_benefit: str,
        expected_cost: float,
        risk_level: str,
        alternatives: str,
        recommendation: str,
        task_id: Optional[str] = None,
        deadline: Optional[str] = None
    ) -> str:
        """Create a structured request for the human owner."""
        if risk_level.upper() not in RISK_LEVELS:
            risk_level = "HIGH"

        approval_id = f"APP-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO approvals (
                approval_id, task_id, requesting_agent, what, why,
                expected_benefit, expected_cost, risk_level, alternatives,
                recommendation, deadline, status, owner_notes, created_at, resolved_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', '', ?, NULL)
        """, (
            approval_id, task_id or "", requesting_agent, what, why,
            expected_benefit, expected_cost, risk_level.upper(),
            alternatives, recommendation, deadline or "", now
        ))
        
        # If tied to a task, ensure the task reflects approval status
        if task_id:
            cursor.execute("""
                UPDATE tasks SET approval_requirement = 1, approval_status = 'PENDING', status = 'APPROVAL_REQUIRED'
                WHERE task_id = ?
            """, (task_id,))

        conn.commit()
        conn.close()

        AuditLogger.log(
            agent_id=requesting_agent,
            action="APPROVAL_REQUEST_SUBMITTED",
            result=f"Approval request {approval_id} created: {what[:60]}... Cost: ${expected_cost:.2f}",
            risk_level=risk_level.upper(),
            cost=expected_cost,
            details={"approval_id": approval_id, "task_id": task_id}
        )
        return approval_id

    @staticmethod
    def resolve_approval(
        approval_id: str,
        decision: str,  # 'APPROVE', 'REJECT', 'REQUEST_INFO', 'PAUSE'
        owner_notes: str = ""
    ) -> bool:
        """Process owner action on an approval request."""
        decision_map = {
            "APPROVE": "APPROVED",
            "REJECT": "REJECTED",
            "REQUEST_INFO": "INFO_REQUESTED",
            "PAUSE": "PAUSED"
        }
        status = decision_map.get(decision.upper())
        if not status:
            raise ValueError(f"Invalid decision: {decision}. Must be one of APPROVE, REJECT, REQUEST_INFO, PAUSE")

        now = datetime.now(timezone.utc).isoformat()
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM approvals WHERE approval_id = ?", (approval_id,))
        app = cursor.fetchone()
        if not app:
            conn.close()
            raise ValueError(f"Approval request {approval_id} not found.")

        cursor.execute("""
            UPDATE approvals SET status = ?, owner_notes = ?, resolved_at = ? WHERE approval_id = ?
        """, (status, owner_notes, now, approval_id))

        # Update linked task if present
        task_id = app["task_id"]
        if task_id:
            if status == "APPROVED":
                cursor.execute("""
                    UPDATE tasks SET approval_status = 'APPROVED', status = 'PLANNED' WHERE task_id = ?
                """, (task_id,))
            elif status == "REJECTED":
                cursor.execute("""
                    UPDATE tasks SET approval_status = 'REJECTED', status = 'CANCELLED' WHERE task_id = ?
                """, (task_id,))
            elif status == "PAUSED":
                cursor.execute("""
                    UPDATE tasks SET status = 'WAITING' WHERE task_id = ?
                """, (task_id,))

        conn.commit()
        conn.close()

        AuditLogger.log(
            agent_id="OWNER",
            action=f"APPROVAL_{status}",
            result=f"Owner resolved {approval_id} -> {status}. Notes: {owner_notes}",
            risk_level="MEDIUM"
        )
        return True

    @staticmethod
    def get_pending_approvals() -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM approvals WHERE status = 'PENDING' ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_all_approvals(limit: int = 50) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM approvals ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
