"""
Owner Time Minimization & Human Intervention Tracker.
Captures every instance where the human owner had to intervene, providing root cause analysis
for subsequent automation, tool creation, and dynamic skill acquisition.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from .db import get_connection
from .audit import AuditLogger

class InterventionTracker:
    @staticmethod
    def record_intervention(
        context: str,
        reason_needed: str,
        can_be_automated: bool,
        missing_capability: str,
        missing_tool: Optional[str] = None,
        new_skill_needed: Optional[str] = None
    ) -> str:
        intervention_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO owner_interventions (
                intervention_id, timestamp, context, reason_needed, 
                can_be_automated, missing_capability, missing_tool, new_skill_needed, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'RECORDED')
        """, (
            intervention_id, now, context, reason_needed,
            1 if can_be_automated else 0, missing_capability,
            missing_tool or "", new_skill_needed or ""
        ))
        conn.commit()
        conn.close()

        AuditLogger.log(
            agent_id="SYSTEM",
            action="OWNER_INTERVENTION_RECORDED",
            result=f"Intervention recorded: {reason_needed[:60]}... Automation potential: {can_be_automated}",
            risk_level="MEDIUM",
            cost=0.0,
            details={"intervention_id": intervention_id, "missing_capability": missing_capability}
        )
        return intervention_id

    @staticmethod
    def get_interventions(limit: int = 50) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM owner_interventions ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_automation_candidates() -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM owner_interventions 
            WHERE can_be_automated = 1 AND status = 'RECORDED' 
            ORDER BY timestamp DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
