"""
Main Entrypoint for the Autonomous AI Digital Company.
Starts the FastAPI application, initializes database and AI employee roster,
and serves the Owner Command Center.
"""

import uvicorn
import os
import sys

# Ensure root directory is on python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.db import init_db
from agents.registry import EmployeeRegistry
from core.audit import AuditLogger

def start():
    print("=" * 60)
    print("  AUTONOMOUS AI COMPANY: FOUNDATION RUNTIME")
    print("=" * 60)
    print("Initializing corporate database...")
    init_db()
    print("Synchronizing 12 founding AI roles...")
    EmployeeRegistry.initialize_default_employees()
    
    AuditLogger.log(
        agent_id="SYSTEM",
        action="ENTERPRISE_SYSTEM_ONLINE",
        result="Autonomous AI Enterprise gateway started successfully. Financial firewall active.",
        risk_level="LOW"
    )

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))

    from cloud.scheduler import CloudScheduler
    from cloud.worker import CloudWorker
    
    print("Engaging 24/7 Autonomous Cloud Scheduler & Operational Worker...")
    CloudScheduler.get_instance().start()
    CloudWorker.get_instance().start()

    print(f"Financial Firewall: ENFORCED (Zero-trust unapproved limit: $0.00)")
    print(f"Owner Command Center launching on http://{host}:{port}")
    print("=" * 60)

    uvicorn.run("server.app:app", host=host, port=port, reload=False, log_level="info")

if __name__ == "__main__":
    start()
