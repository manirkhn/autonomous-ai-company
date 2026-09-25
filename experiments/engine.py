"""
Controlled Experiment Engine.
Executes the scientific 8-stage experiment cycle:
1. Research
2. Define hypothesis
3. Define success metric
4. Build minimum viable version (MVP)
5. Launch controlled test
6. Measure results
7. Analyze
8. Continue, modify, or stop

Enforces the corporate rule: Retrying a failed approach requires an explicit explanation.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core.db import get_connection
from core.audit import AuditLogger
from memory.store import CorporateMemory

EXPERIMENT_STATUSES = {
    "DESIGNED", "MVP_BUILD", "TESTING", "ANALYZING", 
    "SUCCESSFUL", "FAILED_STOPPED", "FAILED_ITERATING"
}

class ExperimentEngine:
    @staticmethod
    def create_experiment(
        title: str,
        hypothesis: str,
        success_metric: str,
        mvp_description: str,
        opportunity_id: Optional[str] = None,
        retry_reason: Optional[str] = None,
        creator_agent: str = "EMP-003-PM"
    ) -> str:
        # Check if similar failed experiments exist in memory
        past_failure = CorporateMemory.check_past_failure(title)
        if past_failure and not retry_reason:
            raise ValueError(
                f"RETRIAL GUARD: A past failed approach matches '{title}' ({past_failure['title']}). "
                "You must provide an explicit 'retry_reason' explaining what has changed before re-testing."
            )

        exp_id = f"EXP-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO experiments (
                experiment_id, opportunity_id, title, hypothesis,
                success_metric, mvp_description, status, results, retry_reason,
                created_at, closed_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'DESIGNED', '', ?, ?, NULL)
        """, (
            exp_id, opportunity_id or "", title, hypothesis,
            success_metric, mvp_description, retry_reason or "", now
        ))
        conn.commit()
        conn.close()

        AuditLogger.log(
            agent_id=creator_agent,
            action="EXPERIMENT_CREATED",
            result=f"Experiment {exp_id} launched: {title} (Metric: {success_metric})",
            risk_level="LOW",
            details={"experiment_id": exp_id, "hypothesis": hypothesis}
        )
        return exp_id

    @staticmethod
    def record_results(
        experiment_id: str,
        status: str,  # 'SUCCESSFUL', 'FAILED_STOPPED', 'FAILED_ITERATING'
        results: str,
        lessons_learned: str,
        agent_id: str = "EMP-003-PM"
    ) -> bool:
        if status.upper() not in EXPERIMENT_STATUSES:
            raise ValueError(f"Invalid experiment status: {status}")

        now = datetime.now(timezone.utc).isoformat()
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM experiments WHERE experiment_id = ?", (experiment_id,))
        exp = cursor.fetchone()
        if not exp:
            conn.close()
            raise ValueError(f"Experiment {experiment_id} not found.")

        cursor.execute("""
            UPDATE experiments SET status = ?, results = ?, closed_at = ? WHERE experiment_id = ?
        """, (status.upper(), results, now, experiment_id))
        conn.commit()
        conn.close()

        # Commit to Corporate Memory
        memory_category = "SUCCESSFUL_APPROACH" if "SUCCESS" in status.upper() else "FAILED_APPROACH"
        CorporateMemory.store_memory(
            category=memory_category,
            title=f"Experiment Result: {exp['title']}",
            content=f"Results:\n{results}\n\nLessons Learned:\n{lessons_learned}",
            metadata={"experiment_id": experiment_id, "final_status": status},
            tags=["experiment", status.lower()],
            author_agent=agent_id
        )

        AuditLogger.log(
            agent_id=agent_id,
            action="EXPERIMENT_CONCLUDED",
            result=f"Experiment {experiment_id} finalized with status: {status}",
            risk_level="LOW"
        )
        return True

    @staticmethod
    def get_experiments(status: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM experiments WHERE status = ? ORDER BY created_at DESC", (status.upper(),))
        else:
            cursor.execute("SELECT * FROM experiments ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
