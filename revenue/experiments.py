"""
Revenue Experiment Engine (Phase 4, Parts 19, 20 & 26).
Manages measurable, time-bounded revenue experiments with explicit success and failure criteria.
Records empirical learning logs into corporate memory.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from core.db import get_connection
from memory.store import CorporateMemory
from revenue.discovery import RevenueDiscoveryEngine

class FirstRevenueExperimentEngine:
    """
    Orchestrates the 7-day, $0 budget First Customer Experiment.
    """

    @classmethod
    def launch_first_customer_experiment(
        cls,
        opportunity_id: str = "OPP-P4-001",
        target_customer_count: int = 1,
        experiment_duration_days: int = 7
    ) -> Dict[str, Any]:
        """
        Initializes the First Customer Experiment with $0 budget and measurable KPIs.
        """
        opp = RevenueDiscoveryEngine.get_candidate(opportunity_id)
        if not opp:
            raise ValueError(f"Opportunity {opportunity_id} not found.")

        now = datetime.now(timezone.utc)
        deadline = now + timedelta(days=experiment_duration_days)
        exp_id = f"EXP-P4-{int(now.timestamp())}"

        hypothesis = (
            f"Offering '{opp['name']}' to {opp['target_customer']} at ${opp['estimated_price']} "
            f"via zero-cost organic distribution will acquire at least {target_customer_count} "
            f"verified paying customer within {experiment_duration_days} days without paid ads."
        )

        success_criteria = [
            f"At least {target_customer_count} verified paying customer ($ {opp['estimated_price'] * target_customer_count:.2f} revenue)",
            "100% positive QA validation and verified delivery receipt",
            "Zero chargebacks or disputed payments"
        ]

        failure_criteria = [
            f"Zero paying customers after {experiment_duration_days} days",
            "Customer acquisition cost exceeds $0.00 unapproved spending limit",
            "Excessive owner manual involvement (> 2 hours total)"
        ]

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO experiments (
            experiment_id, opportunity_id, title, hypothesis,
            success_metric, mvp_description, status, results,
            retry_reason, created_at, closed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            exp_id, opportunity_id, f"First Customer Validation: {opp['name']}", hypothesis,
            "; ".join(success_criteria), f"Functional Python CLI toolkit ({opp['name']})",
            "ACTIVE", None, None, now.isoformat(), None
        ))
        conn.commit()
        conn.close()

        # Update corporate memory
        CorporateMemory.store_memory(
            category="EXPERIMENTS",
            title=f"First Customer Revenue Experiment Initialized: {exp_id}",
            content=f"Hypothesis: {hypothesis}\nBudget: $0.00\nDuration: {experiment_duration_days} days.",
            tags=["revenue", "experiment", "phase4", "zero_capital"]
        )

        return {
            "experiment_id": exp_id,
            "opportunity_id": opportunity_id,
            "target": f"{target_customer_count} verified paying customer",
            "duration_days": experiment_duration_days,
            "budget_usd": 0.0,
            "hypothesis": hypothesis,
            "success_criteria": success_criteria,
            "failure_criteria": failure_criteria,
            "status": "ACTIVE",
            "deadline": deadline.isoformat()
        }

    @classmethod
    def record_experiment_outcome(
        cls,
        experiment_id: str,
        outcome_status: str, # "SUCCESS" or "FAILED"
        verified_sales_count: int,
        verified_revenue: float,
        lessons_learned: str,
        next_action: str
    ) -> Dict[str, Any]:
        """
        Closes an experiment, stores verifiable results, and preserves learning.
        """
        now = datetime.now(timezone.utc).isoformat()
        conn = get_connection()
        cursor = conn.cursor()

        results_data = {
            "outcome": outcome_status,
            "verified_sales": verified_sales_count,
            "verified_revenue": verified_revenue,
            "lessons_learned": lessons_learned,
            "next_action": next_action,
            "completed_at": now
        }

        cursor.execute("""
        UPDATE experiments
        SET status = ?, results = ?, closed_at = ?
        WHERE experiment_id = ?
        """, (outcome_status, str(results_data), now, experiment_id))
        conn.commit()
        conn.close()

        # Log into memory
        CorporateMemory.store_memory(
            category="EXPERIMENTS",
            title=f"Experiment Outcome: {experiment_id} ({outcome_status})",
            content=f"Sales: {verified_sales_count}, Revenue: ${verified_revenue:.2f}\nLessons: {lessons_learned}\nNext: {next_action}",
            tags=["experiment_result", outcome_status.lower(), "learning"]
        )

        return results_data
