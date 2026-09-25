"""
Capability Gap Registry & Self-Growth Preparation (Part 27).
Tracks missing corporate capabilities, evaluates free/open-source tools vs paid alternatives,
and prepares the foundation for dynamic skill and employee acquisition in Phase 3.
"""

import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core.db import get_connection
from core.audit import AuditLogger

class CapabilityGapRegistry:
    @staticmethod
    def record_capability_gap(
        title: str,
        why_required: str,
        frequency: str, # DAILY, WEEKLY, OCCASIONAL
        expected_business_impact: str,
        free_tools: Optional[List[str]] = None,
        oss_options: Optional[List[str]] = None,
        free_tiers: Optional[List[str]] = None,
        paid_options: Optional[List[str]] = None,
        estimated_cost: float = 0.0,
        expected_roi: str = "",
        owner_time_saved_hours: float = 1.0,
        risk: str = "LOW",
        agent_id: str = "EMP-012-AUTOMATION"
    ) -> str:
        gap_id = f"GAP-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO capability_gaps (
                gap_id, title, why_required, frequency, expected_business_impact,
                free_tools, oss_options, free_tiers, paid_options, estimated_cost,
                expected_roi, owner_time_saved, risk, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'IDENTIFIED', ?)
        """, (
            gap_id, title, why_required, frequency, expected_business_impact,
            json.dumps(free_tools or []), json.dumps(oss_options or []),
            json.dumps(free_tiers or []), json.dumps(paid_options or []),
            estimated_cost, expected_roi, owner_time_saved_hours, risk, now
        ))
        conn.commit()
        conn.close()

        AuditLogger.log(
            agent_id=agent_id,
            action="CAPABILITY_GAP_IDENTIFIED",
            result=f"Identified capability gap '{title}'. Free/OSS alternatives cataloged.",
            risk_level="LOW",
            details={"gap_id": gap_id, "free_tools": free_tools}
        )
        return gap_id

    @staticmethod
    def get_capability_gaps() -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM capability_gaps ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for r in rows:
            results.append({
                "gap_id": r["gap_id"],
                "title": r["title"],
                "why_required": r["why_required"],
                "frequency": r["frequency"],
                "expected_business_impact": r["expected_business_impact"],
                "free_tools": json.loads(r["free_tools"]) if r["free_tools"] else [],
                "oss_options": json.loads(r["oss_options"]) if r["oss_options"] else [],
                "free_tiers": json.loads(r["free_tiers"]) if r["free_tiers"] else [],
                "paid_options": json.loads(r["paid_options"]) if r["paid_options"] else [],
                "estimated_cost": r["estimated_cost"],
                "expected_roi": r["expected_roi"],
                "owner_time_saved": r["owner_time_saved"],
                "risk": r["risk"],
                "status": r["status"],
                "created_at": r["created_at"]
            })
        return results
