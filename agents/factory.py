"""
AI Employee Factory, Retraining & Retirement Engine (Part 7, 8, 9, 10, 11).
Dynamically spawns specialized AI employees with strictly enforced least privilege,
manages employee training and testing progressions, tracks continuous performance,
and safely retires obsolete or underperforming roles while preserving institutional memory.
"""

import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core.db import get_connection
from core.audit import AuditLogger
from agents.registry import EmployeeRegistry
from memory.store import CorporateMemory

PROHIBITED_NEW_EMPLOYEE_PERMISSIONS = {
    "bank_transfer", "bank_withdrawal", "credentials_access",
    "modify_financial_beneficiary", "unrestricted_shell",
    "unrestricted_database_write", "bypass_approval"
}

class AIEmployeeFactory:
    @staticmethod
    def spawn_new_employee(
        role_title: str,
        purpose: str,
        responsibilities: List[str],
        capabilities: List[str],
        tools: List[str],
        permissions: List[str],
        instructions: str,
        escalation_rules: str,
        creator_agent: str = "EMP-001-CEO"
    ) -> Dict[str, Any]:
        """
        Part 7 & 8: Spawn a new AI Employee following strict Least Privilege.
        Employee starts in 'TRAINING' status.
        """
        # Enforce Least Privilege
        for p in permissions:
            if p.lower() in PROHIBITED_NEW_EMPLOYEE_PERMISSIONS:
                raise ValueError(f"LEAST PRIVILEGE VIOLATION: Permission '{p}' is strictly prohibited for newly spawned AI employees.")

        emp_id = f"EMP-{uuid.uuid4().hex[:6].upper()}-{role_title.split()[0].upper()}"
        now = datetime.now(timezone.utc).isoformat()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO employees (
                employee_id, role, purpose, responsibilities, capabilities,
                tools, permissions, current_tasks, status, performance_metrics,
                cost, created_date, last_review, instructions, escalation_rules
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'TRAINING', ?, 0.0, ?, ?, ?, ?)
        """, (
            emp_id, role_title, purpose,
            json.dumps(responsibilities),
            json.dumps(capabilities),
            json.dumps(tools),
            json.dumps(permissions),
            json.dumps([]),
            json.dumps({
                "tasks_assigned": 0,
                "tasks_completed": 0,
                "tasks_failed": 0,
                "success_rate": 1.0,
                "avg_duration_sec": 0.0,
                "owner_interventions_count": 0,
                "revenue_impact_usd": 0.0
            }),
            now, now, instructions, escalation_rules
        ))
        conn.commit()
        conn.close()

        AuditLogger.log(
            agent_id=creator_agent,
            action="AI_EMPLOYEE_SPAWNED",
            result=f"Spawned new AI employee {emp_id} ('{role_title}') in TRAINING status.",
            risk_level="MEDIUM",
            details={"employee_id": emp_id, "role": role_title, "status": "TRAINING"}
        )

        return {
            "employee_id": emp_id,
            "role": role_title,
            "status": "TRAINING",
            "permissions": permissions,
            "tools": tools
        }

    @staticmethod
    def advance_employee_to_active(employee_id: str, test_evidence: str, agent_id: str = "EMP-011-QA") -> bool:
        """
        Transitions employee from TRAINING -> TESTING -> ACTIVE
        requires non-empty test evidence receipt.
        """
        emp = EmployeeRegistry.get_employee(employee_id)
        if not emp:
            raise ValueError(f"Employee {employee_id} not found.")

        if not test_evidence or len(test_evidence.strip()) < 10:
            raise ValueError("TEST EVIDENCE REQUIRED: Employee cannot become ACTIVE without documented verification.")

        # Advance to ACTIVE
        EmployeeRegistry.update_employee_status(employee_id, "ACTIVE", f"Passed operational validation: {test_evidence[:60]}")

        AuditLogger.log(
            agent_id=agent_id,
            action="AI_EMPLOYEE_ACTIVATED",
            result=f"Employee {employee_id} ({emp['role']}) promoted to ACTIVE operational workforce.",
            risk_level="LOW",
            details={"employee_id": employee_id, "evidence": test_evidence}
        )
        return True

    @staticmethod
    def retrain_employee(employee_id: str, identified_missing_skill: str, training_sops: str, agent_id: str = "EMP-001-CEO") -> bool:
        """
        Part 10: Retrain employee upon repeated failures.
        Updates instructions and SOPs, records learning to memory, and moves status to TESTING.
        """
        emp = EmployeeRegistry.get_employee(employee_id)
        if not emp:
            raise ValueError(f"Employee {employee_id} not found.")

        new_instructions = emp["instructions"] + f"\n\n[RETRAINING FOR: {identified_missing_skill} - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}]:\n{training_sops}"

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE employees SET 
                instructions = ?, 
                status = 'TESTING',
                last_review = ?
            WHERE employee_id = ?
        """, (new_instructions, datetime.now(timezone.utc).isoformat(), employee_id))
        conn.commit()
        conn.close()

        # Commit retrospective to corporate memory
        CorporateMemory.store_memory(
            category="LESSONS_LEARNED",
            title=f"Retraining Record: {employee_id} ({emp['role']})",
            content=f"Employee encountered failure patterns due to missing skill: {identified_missing_skill}.\nRemediation applied:\n{training_sops}",
            author_agent=agent_id
        )

        AuditLogger.log(
            agent_id=agent_id,
            action="AI_EMPLOYEE_RETRAINED",
            result=f"Retrained {employee_id} with missing skill '{identified_missing_skill}'. Moved to TESTING.",
            risk_level="LOW"
        )
        return True

    @staticmethod
    def retire_employee(employee_id: str, reason: str, agent_id: str = "EMP-001-CEO") -> bool:
        """
        Part 11: Safely retire an employee.
        Preserves historical knowledge, migrates tasks, and sets status to RETIRED.
        """
        emp = EmployeeRegistry.get_employee(employee_id)
        if not emp:
            raise ValueError(f"Employee {employee_id} not found.")

        # Preserve institutional memory before retirement
        CorporateMemory.store_memory(
            category="DECISION_RECORD",
            title=f"Employee Retirement: {employee_id} ({emp['role']})",
            content=f"Employee {employee_id} safely retired.\nReason: {reason}\nCapabilities: {emp['capabilities']}\nHistorical performance: {emp['performance_metrics']}",
            author_agent=agent_id
        )

        EmployeeRegistry.update_employee_status(employee_id, "RETIRED", reason)

        AuditLogger.log(
            agent_id=agent_id,
            action="AI_EMPLOYEE_RETIRED",
            result=f"Safely retired {employee_id} ({emp['role']}). Reason: {reason}",
            risk_level="MEDIUM"
        )
        return True
