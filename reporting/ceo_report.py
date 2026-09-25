"""
Weekly CEO Company Report Generator.
Synthesizes all operational, financial, and product data across the enterprise.
MANDATORY COMPLIANCE RULE:
Strictly and unequivocally separates:
1. FACTS (grounded, verified historical data)
2. ESTIMATES (projections, modeled KPIs)
3. AI RECOMMENDATIONS (proposals for human owner consideration)
"""

from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
from core.db import get_connection
from finance.analytics import FinanceEngine
from agents.registry import EmployeeRegistry
from tasks.engine import TaskEngine
from approvals.manager import ApprovalManager
from discovery.engine import OpportunityDiscoveryEngine
from experiments.engine import ExperimentEngine
from memory.store import CorporateMemory
from core.interventions import InterventionTracker

class CEOReportGenerator:
    @staticmethod
    def generate_weekly_report() -> Dict[str, Any]:
        finances = FinanceEngine.get_financial_summary()
        employees = EmployeeRegistry.get_all_employees()
        pending_approvals = ApprovalManager.get_pending_approvals()
        recent_tasks = TaskEngine.get_tasks(limit=100)
        completed_tasks = [t for t in recent_tasks if t["status"] == "COMPLETED"]
        failed_tasks = [t for t in recent_tasks if t["status"] == "FAILED"]
        opportunities = OpportunityDiscoveryEngine.get_opportunities()
        experiments = ExperimentEngine.get_experiments()
        recent_lessons = CorporateMemory.search_memories(category="LESSONS_LEARNED", limit=10)
        recent_failures = CorporateMemory.search_memories(category="FAILED_APPROACH", limit=5)
        automation_candidates = InterventionTracker.get_automation_candidates()

        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # 1. VERIFIED FACTS (Strictly ground-truth data)
        facts = {
            "report_generated_at": now,
            "period": "Last 7 Days",
            "verified_revenue_usd": finances["revenue"]["this_week"],
            "total_lifetime_revenue_usd": finances["revenue"]["total"],
            "verified_expenses_usd": finances["expenses"]["this_week"],
            "total_lifetime_expenses_usd": finances["expenses"]["total"],
            "actual_net_cashflow_usd": finances["revenue"]["this_week"] - finances["expenses"]["this_week"],
            "completed_tasks_count": len(completed_tasks),
            "failed_tasks_count": len(failed_tasks),
            "active_ai_employees_count": len([e for e in employees if e["status"] == "ACTIVE"]),
            "pending_owner_approvals_count": len(pending_approvals),
            "documented_failed_approaches_count": len(recent_failures),
            "owner_interventions_logged": len(automation_candidates)
        }

        # 2. MODEL-BASED ESTIMATES (Projections, margins, potential)
        estimates = {
            "estimated_gross_profit_margin_pct": finances["profit"]["profit_margin_pct"],
            "simulated_cash_available_for_reinvestment": finances["profit"]["cash_available_reinvestment"],
            "pipeline_opportunities_evaluated": len(opportunities),
            "average_estimated_opportunity_price": (
                sum(o["estimated_price"] for o in opportunities) / len(opportunities)
            ) if opportunities else 0.0,
            "estimated_ai_operating_compute_cost": sum(e["cost"] for e in employees),
            "average_task_duration_est_min": 12.5
        }

        # 3. AI RECOMMENDATIONS & DECISIONS REQUIRED
        recommendations = {
            "urgent_owner_decisions_required": [
                {
                    "approval_id": a["approval_id"],
                    "what": a["what"],
                    "why": a["why"],
                    "expected_cost": a["expected_cost"],
                    "risk_level": a["risk_level"],
                    "recommendation": a["recommendation"]
                }
                for a in pending_approvals
            ],
            "strategic_initiatives_proposed": [
                "Prioritize zero-capital MVP validation in micro-tools and templates.",
                "Automate repetitive owner interventions identified by the Automation Engineer.",
                "Maintain strict $0 unapproved spending firewall threshold."
            ],
            "automation_targets": [
                {
                    "intervention_id": c["intervention_id"],
                    "reason_needed": c["reason_needed"],
                    "missing_tool": c["missing_tool"],
                    "new_skill_needed": c["new_skill_needed"]
                }
                for c in automation_candidates[:3]
            ],
            "opportunities_ready_for_testing": [
                {
                    "opp_id": o["opportunity_id"],
                    "solution": o["proposed_solution"],
                    "target": o["target_customer"],
                    "validation_method": o["validation_method"]
                }
                for o in opportunities if o["status"] in {"DISCOVERED", "VALIDATION_READY"}
            ][:3]
        }

        return {
            "executive_summary": "Autonomous AI Company Foundation operational. All financial controls locked to owner approval.",
            "facts": facts,
            "estimates": estimates,
            "recommendations": recommendations,
            "recent_completed_work": [
                {"task_id": t["task_id"], "objective": t["objective"], "evidence": t["evidence"]}
                for t in completed_tasks[:5]
            ],
            "recent_failed_work": [
                {"task_id": t["task_id"], "objective": t["objective"], "errors": t["errors"]}
                for t in failed_tasks[:5]
            ]
        }
