"""
Activity Tracking Engine (Phase 5B, Requirements 14, 15, 21, 29).
Records every AI employee activity with genuine execution context.
Enforces the invariant: Never fabricate external activity.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from core.db import get_connection

class ActivityTracker:
    @staticmethod
    def record_activity(
        employee_id: str,
        employee_name: str,
        role: str,
        task_id: str,
        action: str,
        status: str = "COMPLETED",
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        project: Optional[str] = None,
        experiment: Optional[str] = None,
        product: Optional[str] = None,
        campaign: Optional[str] = None,
        module: Optional[str] = None,
        external_platform: Optional[str] = None,
        result: Optional[str] = None,
        error: Optional[str] = None,
        handoff: Optional[str] = None,
        owner_intervention: bool = False
    ) -> Dict[str, Any]:
        """
        Record a genuine employee activity unit.
        """
        now = datetime.now(timezone.utc).isoformat()
        activity_id = f"ACT-{uuid.uuid4().hex[:8].upper()}"
        start = start_time or now
        end = end_time or now

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO employee_activities (
                activity_id, employee_id, employee_name, role, task_id,
                start_time, end_time, status, project, experiment,
                product, campaign, module, external_platform,
                action, result, error, handoff, owner_intervention
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            activity_id, employee_id, employee_name, role, task_id,
            start, end, status.upper(), project or "", experiment or "",
            product or "", campaign or "", module or "", external_platform or "",
            action, result or "", error or "", handoff or "", 1 if owner_intervention else 0
        ))
        conn.commit()
        conn.close()

        return {
            "activity_id": activity_id,
            "employee_id": employee_id,
            "employee_name": employee_name,
            "task_id": task_id,
            "action": action,
            "status": status.upper(),
            "timestamp": end
        }

    @staticmethod
    def get_activities(
        employee_id: Optional[str] = None,
        timeframe: str = "all", # "today", "7days", "all"
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch employee activity history.
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM employee_activities WHERE 1=1"
        params = []
        
        if employee_id:
            query += " AND employee_id = ?"
            params.append(employee_id)
            
        now = datetime.now(timezone.utc)
        if timeframe == "today":
            today_prefix = now.strftime("%Y-%m-%d")
            query += " AND start_time LIKE ?"
            params.append(f"{today_prefix}%")
        elif timeframe == "7days":
            week_ago = (now - timedelta(days=7)).isoformat()
            query += " AND start_time >= ?"
            params.append(week_ago)
            
        query += " ORDER BY start_time DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, tuple(params))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_employee_summary_table(timeframe: str = "today") -> List[Dict[str, Any]]:
        """
        Generates truth-grounded activity summary table per employee (Requirement 21).
        """
        from agents.registry import EmployeeRegistry
        employees = EmployeeRegistry.get_all_employees()
        activities = ActivityTracker.get_activities(timeframe=timeframe, limit=500)
        
        summary = []
        for emp in employees:
            e_id = emp["employee_id"]
            emp_acts = [a for a in activities if a["employee_id"] == e_id]
            tasks_count = len(emp_acts)
            completed_count = sum(1 for a in emp_acts if a["status"] == "COMPLETED")
            failed_count = sum(1 for a in emp_acts if a["status"] == "FAILED")
            blocked_count = sum(1 for a in emp_acts if a["status"] == "BLOCKED")
            
            summary.append({
                "employee_id": e_id,
                "role": emp["role"],
                "total_tasks": tasks_count,
                "completed": completed_count,
                "failed": failed_count,
                "blocked": blocked_count,
                "current_status": emp["status"]
            })
            
        return summary
