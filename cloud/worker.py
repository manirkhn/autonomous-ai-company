"""
24/7 Cloud Autonomous Worker (Phase 5B, Requirements 10, 13, 14, 15).
Executes AI employee work routines continuously in the cloud independent of the owner's laptop.
Maintains state, tracks genuine activity contexts, and provides automatic recovery on transient errors.
"""

import time
import threading
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from tasks.engine import TaskEngine
from agents.registry import EmployeeRegistry
from core.activity import ActivityTracker
from core.audit import AuditLogger

logger = logging.getLogger("CloudWorker")

class CloudWorker:
    _instance: Optional["CloudWorker"] = None
    _thread: Optional[threading.Thread] = None
    _stop_event = threading.Event()

    def __init__(self, poll_interval_seconds: int = 10):
        self.poll_interval = poll_interval_seconds
        self.is_running = False
        self.tasks_processed = 0
        self.last_poll_time: Optional[str] = None
        self.last_action_desc: Optional[str] = None

    @classmethod
    def get_instance(cls) -> "CloudWorker":
        if cls._instance is None:
            cls._instance = CloudWorker()
        return cls._instance

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_running": self.is_running,
            "poll_interval_seconds": self.poll_interval,
            "tasks_processed": self.tasks_processed,
            "last_poll_time": self.last_poll_time,
            "last_action": self.last_action_desc
        }

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="24_7_CloudWorker")
        self._thread.start()
        AuditLogger.log(
            agent_id="EMP-001-CEO",
            action="WORKER_STARTED",
            result="24/7 Cloud autonomous worker loop engaged",
            risk_level="LOW"
        )

    def stop(self):
        self._stop_event.set()
        self.is_running = False

    def _run_loop(self):
        logger.info("24/7 CloudWorker execution loop engaged.")
        while not self._stop_event.is_set():
            try:
                self.last_poll_time = datetime.now(timezone.utc).isoformat()
                self._process_routine()
            except Exception as e:
                logger.error(f"Error in CloudWorker loop (auto-recovering): {e}")

            time.sleep(self.poll_interval)

    def _process_routine(self):
        # 1. Query actionable tasks
        active_tasks = TaskEngine.get_tasks(status="IN_PROGRESS", limit=5)
        if not active_tasks:
            # Check for new tasks that don't require approval
            new_tasks = TaskEngine.get_tasks(status="NEW", limit=5)
            for t in new_tasks:
                if not t["approval_requirement"]:
                    try:
                        TaskEngine.transition_state(t["task_id"], "IN_PROGRESS", t["assigned_agent"], "Worker auto-assignment")
                        self.last_action_desc = f"Picked up task {t['task_id']}"
                        self.tasks_processed += 1
                        # Record genuine activity
                        emp = EmployeeRegistry.get_employee(t["assigned_agent"])
                        emp_role = emp["role"] if emp else "Autonomous Agent"
                        emp_name = emp["role"] if emp else "Autonomous Agent"
                        ActivityTracker.record_activity(
                            employee_id=t["assigned_agent"],
                            employee_name=emp_name,
                            role=emp_role,
                            task_id=t["task_id"],
                            action=f"Started working on {t['objective']}",
                            status="IN_PROGRESS",
                            project="OPP-P4-001",
                            experiment="EXP-P4-1790269597",
                            module="tasks/engine.py"
                        )
                    except Exception as err:
                        logger.warning(f"Could not transition task {t['task_id']}: {err}")
                    break
        else:
            self.last_action_desc = f"Monitoring {len(active_tasks)} active operational tasks"

        # Phase 5I: Periodic Autonomous Business Operator Pulse
        self._operator_pulse_counter = getattr(self, "_operator_pulse_counter", 0) + 1
        if self._operator_pulse_counter >= 30:
            self._operator_pulse_counter = 0
            try:
                from business.autonomous_operator import AutonomousBusinessOperator
                AutonomousBusinessOperator.execute_cycle()
            except Exception as e:
                logger.warning(f"Error running autonomous operator pulse in worker: {e}")
