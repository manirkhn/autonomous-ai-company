"""
Central Task Management Engine.
Enforces structured handoffs, evidence-based completion, dependency resolution,
and integration with the Human Approval Center.
"""

import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core.db import get_connection
from core.audit import AuditLogger
from core.firewall import FinancialFirewall

TASK_STATUSES = {
    "NEW", "PLANNED", "IN_PROGRESS", "WAITING", 
    "REVIEW", "APPROVAL_REQUIRED", "COMPLETED", 
    "FAILED", "CANCELLED"
}

PRIORITIES = {"LOW", "MEDIUM", "HIGH", "URGENT"}

class TaskEngine:
    @staticmethod
    def create_task(
        creator: str,
        assigned_agent: str,
        objective: str,
        description: str,
        priority: str = "MEDIUM",
        deadline: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        required_tools: Optional[List[str]] = None,
        requires_approval: bool = False,
        estimated_cost: float = 0.0,
        estimated_revenue_impact: float = 0.0
    ) -> str:
        """Create a new structured corporate task."""
        if priority.upper() not in PRIORITIES:
            priority = "MEDIUM"

        task_id = f"TSK-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()
        initial_status = "APPROVAL_REQUIRED" if requires_approval else "NEW"
        approval_status = "PENDING" if requires_approval else "NONE"

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (
                task_id, creator, assigned_agent, objective, description,
                priority, deadline, dependencies, required_tools, status,
                result, evidence, errors, approval_requirement, approval_status,
                timestamp, cost, revenue_impact
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_id, creator, assigned_agent, objective, description,
            priority.upper(), deadline or "", json.dumps(dependencies or []),
            json.dumps(required_tools or []), initial_status,
            "", "", "", 1 if requires_approval else 0, approval_status,
            now, estimated_cost, estimated_revenue_impact
        ))
        conn.commit()
        conn.close()

        AuditLogger.log(
            agent_id=creator,
            action="TASK_CREATED",
            result=f"Task {task_id} assigned to {assigned_agent}: {objective}",
            risk_level="MEDIUM" if requires_approval else "LOW",
            cost=estimated_cost,
            details={"task_id": task_id, "priority": priority, "requires_approval": requires_approval}
        )
        return task_id

    @staticmethod
    def transition_state(task_id: str, new_status: str, agent_id: str, reason: str = "") -> bool:
        """Safely transition task lifecycle state with prerequisite checks."""
        if new_status.upper() not in TASK_STATUSES:
            raise ValueError(f"Invalid status {new_status}. Allowed: {TASK_STATUSES}")

        task = TaskEngine.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found.")

        # Check dependencies if moving to IN_PROGRESS
        if new_status.upper() == "IN_PROGRESS" and task["dependencies"]:
            for dep_id in task["dependencies"]:
                dep = TaskEngine.get_task(dep_id)
                if not dep or dep["status"] != "COMPLETED":
                    raise ValueError(f"Cannot start task {task_id}: Dependency {dep_id} is not COMPLETED.")

        # If task requires approval, prevent in_progress without approval
        if task["approval_requirement"] and task["approval_status"] != "APPROVED":
            if new_status.upper() in {"IN_PROGRESS", "COMPLETED"}:
                raise ValueError(f"Cannot move task {task_id} to {new_status}: Pending human approval.")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET status = ? WHERE task_id = ?", (new_status.upper(), task_id))
        conn.commit()
        conn.close()

        AuditLogger.log(
            agent_id=agent_id,
            action="TASK_STATE_TRANSITION",
            result=f"Task {task_id} transitioned from {task['status']} to {new_status}. {reason}",
            risk_level="LOW"
        )
        return True

    @staticmethod
    def complete_task(
        task_id: str,
        agent_id: str,
        result: str,
        evidence: str,
        actual_cost: float = 0.0,
        revenue_impact: float = 0.0
    ) -> bool:
        """
        Mark a task completed.
        Strict Rule: Non-empty verifiable evidence is MANDATORY.
        """
        if not evidence or len(evidence.strip()) < 5:
            raise ValueError("EVIDENCE REQUIRED: Tasks cannot be marked COMPLETED without verifiable proof.")

        task = TaskEngine.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found.")

        if task["approval_requirement"] and task["approval_status"] != "APPROVED":
            raise ValueError("APPROVAL REQUIRED: Cannot complete task without explicit human owner approval.")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tasks SET 
                status = 'COMPLETED',
                result = ?,
                evidence = ?,
                cost = ?,
                revenue_impact = ?
            WHERE task_id = ?
        """, (result, evidence, actual_cost, revenue_impact, task_id))
        conn.commit()
        conn.close()

        AuditLogger.log(
            agent_id=agent_id,
            action="TASK_COMPLETED",
            result=f"Task {task_id} successfully verified with evidence.",
            risk_level="LOW",
            cost=actual_cost,
            details={"task_id": task_id, "evidence_preview": evidence[:100]}
        )
        return True

    @staticmethod
    def fail_task(task_id: str, agent_id: str, errors: str) -> bool:
        """Record task failure with diagnostic error trace."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tasks SET status = 'FAILED', errors = ? WHERE task_id = ?
        """, (errors, task_id))
        conn.commit()
        conn.close()

        AuditLogger.log(
            agent_id=agent_id,
            action="TASK_FAILED",
            result=f"Task {task_id} failed: {errors[:80]}",
            risk_level="HIGH",
            details={"task_id": task_id, "errors": errors}
        )
        return True

    @staticmethod
    def get_task(task_id: str) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return TaskEngine._row_to_dict(row)

    @staticmethod
    def get_tasks(status: Optional[str] = None, agent: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status.upper())
        if agent:
            query += " AND assigned_agent = ?"
            params.append(agent)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()
        return [TaskEngine._row_to_dict(r) for r in rows]

    @staticmethod
    def _row_to_dict(row) -> Dict[str, Any]:
        return {
            "task_id": row["task_id"],
            "creator": row["creator"],
            "assigned_agent": row["assigned_agent"],
            "objective": row["objective"],
            "description": row["description"],
            "priority": row["priority"],
            "deadline": row["deadline"],
            "dependencies": json.loads(row["dependencies"]) if row["dependencies"] else [],
            "required_tools": json.loads(row["required_tools"]) if row["required_tools"] else [],
            "status": row["status"],
            "result": row["result"],
            "evidence": row["evidence"],
            "errors": row["errors"],
            "approval_requirement": bool(row["approval_requirement"]),
            "approval_status": row["approval_status"],
            "timestamp": row["timestamp"],
            "cost": row["cost"],
            "revenue_impact": row["revenue_impact"]
        }
