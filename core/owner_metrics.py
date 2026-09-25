"""
Owner Time Metrics & Automation Opportunity Engine (Part 21, 22).
Measures human owner burden in minutes/day and minutes/week, detects repeated manual tasks,
and proposes high-yield automations to continuously drive owner involvement toward zero.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
from core.db import get_connection
from core.interventions import InterventionTracker
from approvals.manager import ApprovalManager
from tasks.engine import TaskEngine

class OwnerMetricsEngine:
    @staticmethod
    def get_metrics() -> Dict[str, Any]:
        """Compute owner time expenditure, approval loads, and automation opportunities."""
        conn = get_connection()
        cursor = conn.cursor()

        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        week_start = (now - timedelta(days=7)).isoformat()

        # Interventions
        cursor.execute("SELECT * FROM owner_interventions WHERE timestamp >= ?", (week_start,))
        interventions = cursor.fetchall()
        
        # Approvals
        cursor.execute("SELECT * FROM approvals WHERE created_at >= ?", (week_start,))
        approvals = cursor.fetchall()

        # Tasks
        cursor.execute("SELECT * FROM tasks WHERE timestamp >= ?", (week_start,))
        tasks = cursor.fetchall()

        conn.close()

        # Calculate minutes (assume average 3 minutes per approval review, 10 min per manual intervention)
        approvals_today = [a for a in approvals if a["created_at"] >= today_start]
        interventions_today = [i for i in interventions if i["timestamp"] >= today_start]

        mins_today = (len(approvals_today) * 3.0) + (len(interventions_today) * 10.0)
        mins_week = (len(approvals) * 3.0) + (len(interventions) * 10.0)

        # Categorize reasons
        reasons_count = {}
        for i in interventions:
            r = i["reason_needed"][:40]
            reasons_count[r] = reasons_count.get(r, 0) + 1

        top_reasons = sorted([{"reason": k, "count": v} for k, v in reasons_count.items()], key=lambda x: x["count"], reverse=True)[:5]
        automation_candidates = InterventionTracker.get_automation_candidates()

        return {
            "owner_minutes_today": round(mins_today, 1),
            "owner_minutes_week": round(mins_week, 1),
            "total_approvals_week": len(approvals),
            "pending_approvals_count": len([a for a in approvals if a["status"] == "PENDING"]),
            "manual_interventions_count": len(interventions),
            "automated_tasks_count": len([t for t in tasks if t["assigned_agent"] != "OWNER"]),
            "top_reasons_owner_required": top_reasons,
            "automation_opportunities_count": len(automation_candidates),
            "automation_candidates": automation_candidates[:5]
        }

    @staticmethod
    def propose_automation_from_task(
        task_name: str,
        frequency_per_week: int,
        estimated_time_cost_min: float,
        proposed_automation_method: str,
        implementation_cost_usd: float = 0.0
    ) -> Dict[str, Any]:
        """Part 22: Structure a formal automation proposal."""
        weekly_saved_min = frequency_per_week * estimated_time_cost_min
        yearly_saved_hours = (weekly_saved_min * 52) / 60.0

        return {
            "task_name": task_name,
            "frequency_per_week": frequency_per_week,
            "estimated_time_cost_min": estimated_time_cost_min,
            "proposed_automation_method": proposed_automation_method,
            "implementation_cost_usd": implementation_cost_usd,
            "expected_weekly_time_saved_min": round(weekly_saved_min, 1),
            "expected_yearly_time_saved_hours": round(yearly_saved_hours, 1),
            "recommendation": "PROCEED" if weekly_saved_min >= 15 else "DEFER"
        }
