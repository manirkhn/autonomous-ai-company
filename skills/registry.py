"""
AI Skill Registry & Governance (Part 5).
Tracks all modular agent skills with strict status transitions, explicit tool permissions,
security rules, and performance tracking.
"""

import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core.db import get_connection
from core.audit import AuditLogger

SKILL_STATUSES = {
    "PROPOSED", "DESIGNING", "BUILDING", "TESTING",
    "ACTIVE", "DEGRADED", "PAUSED", "RETIRED"
}

class SkillRegistry:
    @staticmethod
    def register_skill(
        name: str,
        purpose: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        tools: List[str],
        permissions: List[str],
        instructions: str,
        security_rules: str,
        tests: List[Dict[str, Any]],
        business_value: str,
        dependencies: Optional[List[str]] = None,
        cost: float = 0.0,
        owner_time_saved_hours: float = 1.0,
        initial_status: str = "PROPOSED",
        version: str = "1.0.0"
    ) -> str:
        """Register a new formal skill into the enterprise registry."""
        if initial_status.upper() not in SKILL_STATUSES:
            initial_status = "PROPOSED"

        skill_id = f"SKL-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO skills (
                skill_id, name, version, purpose, inputs, outputs,
                tools, permissions, dependencies, instructions, tests,
                security_rules, cost, owner_time_saved, business_value,
                performance, created_date, last_updated, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            skill_id, name, version, purpose,
            json.dumps(inputs), json.dumps(outputs),
            json.dumps(tools), json.dumps(permissions),
            json.dumps(dependencies or []), instructions,
            json.dumps(tests), security_rules, cost,
            owner_time_saved_hours, business_value,
            json.dumps({"success_rate": 1.0, "total_runs": 0, "avg_duration_sec": 0.0}),
            now, now, initial_status.upper()
        ))
        conn.commit()
        conn.close()

        AuditLogger.log(
            agent_id="SYSTEM",
            action="SKILL_REGISTERED",
            result=f"Skill {skill_id} ('{name}') registered with status {initial_status}",
            risk_level="LOW",
            details={"skill_id": skill_id, "name": name, "status": initial_status}
        )
        return skill_id

    @staticmethod
    def get_skill(skill_id: str) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM skills WHERE skill_id = ?", (skill_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return SkillRegistry._row_to_dict(row)

    @staticmethod
    def get_all_skills(status: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM skills WHERE status = ? ORDER BY created_date DESC", (status.upper(),))
        else:
            cursor.execute("SELECT * FROM skills ORDER BY created_date DESC")
        rows = cursor.fetchall()
        conn.close()
        return [SkillRegistry._row_to_dict(r) for r in rows]

    @staticmethod
    def update_skill_status(skill_id: str, new_status: str, reason: str = "") -> bool:
        if new_status.upper() not in SKILL_STATUSES:
            raise ValueError(f"Invalid skill status: {new_status}")

        now = datetime.now(timezone.utc).isoformat()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE skills SET status = ?, last_updated = ? WHERE skill_id = ?", (new_status.upper(), now, skill_id))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()

        if updated:
            AuditLogger.log(
                agent_id="SYSTEM",
                action="SKILL_STATUS_UPDATED",
                result=f"Skill {skill_id} status changed to {new_status}. {reason}",
                risk_level="LOW"
            )
        return updated

    @staticmethod
    def _row_to_dict(row) -> Dict[str, Any]:
        return {
            "skill_id": row["skill_id"],
            "name": row["name"],
            "version": row["version"],
            "purpose": row["purpose"],
            "inputs": json.loads(row["inputs"]) if row["inputs"] else {},
            "outputs": json.loads(row["outputs"]) if row["outputs"] else {},
            "tools": json.loads(row["tools"]) if row["tools"] else [],
            "permissions": json.loads(row["permissions"]) if row["permissions"] else [],
            "dependencies": json.loads(row["dependencies"]) if row["dependencies"] else [],
            "instructions": row["instructions"],
            "tests": json.loads(row["tests"]) if row["tests"] else [],
            "security_rules": row["security_rules"],
            "cost": row["cost"],
            "owner_time_saved": row["owner_time_saved"],
            "business_value": row["business_value"],
            "performance": json.loads(row["performance"]) if row["performance"] else {},
            "created_date": row["created_date"],
            "last_updated": row["last_updated"],
            "status": row["status"]
        }
