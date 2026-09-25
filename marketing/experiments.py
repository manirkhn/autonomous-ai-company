"""
Marketing Experiment Engine & Bottleneck Resolution (Phase 5E, Section 18).

When a bottleneck is identified (e.g. Traffic, Call-to-Action, Value Prop),
the system creates measurable, zero-cost customer acquisition experiments.

Decisions:
  CONTINUE | MODIFY | STOP | SCALE_WITH_APPROVAL
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from core.db import get_connection

VALID_DECISIONS = {"CONTINUE", "MODIFY", "STOP", "SCALE_WITH_APPROVAL"}


class MarketingExperimentEngine:
    """
    Tracks and evaluates customer acquisition experiments.
    """

    @classmethod
    def create_experiment(
        cls,
        payload_or_hypothesis: Union[Dict[str, Any], str],
        **kwargs
    ) -> str:
        """
        Creates a new marketing experiment. Free-First mode enforces $0.00 spend.
        Returns the experiment_id.
        """
        if isinstance(payload_or_hypothesis, dict):
            data = payload_or_hypothesis
        else:
            data = {"hypothesis": payload_or_hypothesis}
            data.update(kwargs)

        experiment_id = data.get("experiment_id") or f"MKT-EXP-{int(datetime.now(timezone.utc).timestamp())}"
        hypothesis = data.get("hypothesis", "Free-first acquisition experiment")
        problem = data.get("problem", "Customer discovery bottleneck")
        channel = data.get("channel", "Community")
        action = data.get("action", "Publish educational benchmark guide")
        expected_signal = data.get("expected_measurable_signal") or data.get("expected_signal", "At least 5 checkout sessions within 7 days")
        spend = float(data.get("spend", 0.0))
        outcome = data.get("outcome", "RUNNING")
        status = data.get("status") or outcome
        decision = data.get("decision", "CONTINUE")
        now = datetime.now(timezone.utc).isoformat()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO marketing_experiments (
            experiment_id, hypothesis, problem, channel, action,
            expected_signal, actual_result, start_date, spend,
            outcome, status, decision, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            experiment_id, hypothesis, problem, channel, action,
            expected_signal, "Experiment in progress. Awaiting signal data.",
            now, spend, outcome, status, decision, now
        ))
        conn.commit()
        conn.close()

        return experiment_id

    @classmethod
    def get_experiments(cls, limit: int = 50) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM marketing_experiments ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = []
        for r in cursor.fetchall():
            d = dict(r)
            if "status" not in d or not d["status"]:
                d["status"] = d.get("outcome", "RUNNING")
            rows.append(d)
        conn.close()
        return rows

    @classmethod
    def list_experiments(cls, limit: int = 50) -> List[Dict[str, Any]]:
        return cls.get_experiments(limit)

    @classmethod
    def update_experiment_decision(
        cls,
        experiment_id: str,
        actual_result: str,
        decision: str,
        outcome: str = "COMPLETED"
    ) -> Dict[str, Any]:
        if decision not in VALID_DECISIONS:
            raise ValueError(f"Invalid decision: {decision}. Allowed: {VALID_DECISIONS}")

        now = datetime.now(timezone.utc).isoformat()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE marketing_experiments
        SET actual_result = ?, decision = ?, outcome = ?, status = ?, end_date = ?
        WHERE experiment_id = ?
        """, (actual_result, decision, outcome, outcome, now, experiment_id))
        conn.commit()

        cursor.execute("SELECT * FROM marketing_experiments WHERE experiment_id = ?", (experiment_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise ValueError(f"Experiment {experiment_id} not found.")
        d = dict(row)
        if "status" not in d or not d["status"]:
            d["status"] = d.get("outcome", outcome)
        return d

    @classmethod
    def record_experiment_result(
        cls,
        experiment_id: str,
        actual_result: str,
        decision: str,
        status: str = "COMPLETED"
    ) -> bool:
        """Helper that updates result and decision and returns boolean success."""
        res = cls.update_experiment_decision(
            experiment_id=experiment_id,
            actual_result=actual_result,
            decision=decision,
            outcome=status
        )
        return res is not None
