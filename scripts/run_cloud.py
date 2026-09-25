"""
Standalone 24/7 Cloud Company Launcher (Phase 5B).
Used for headless server or container execution where the owner's laptop is disconnected.
Starts database verification, 24/7 background scheduler, background worker, and the web/API server.
"""

import os
import sys
import uvicorn

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db import init_db
from agents.registry import EmployeeRegistry
from cloud.scheduler import CloudScheduler
from cloud.worker import CloudWorker
from core.heartbeat import CompanyHeartbeat

def run_cloud():
    print("=" * 60)
    print("  AUTONOMOUS AI COMPANY: 24/7 CLOUD RUNTIME ENGAGED")
    print("  Independent of Laptop • Continuous Background Operations")
    print("=" * 60)
    
    # 1. Database Initialization & Integrity
    init_db()
    EmployeeRegistry.initialize_default_employees()

    # 2. Start Cloud Background Services
    scheduler = CloudScheduler.get_instance()
    scheduler.start()
    print("✅ Cloud Scheduler: Running (Daily Report Target: 23:00 Asia/Dubai)")

    worker = CloudWorker.get_instance()
    worker.start()
    print("✅ Cloud Worker: Running (Autonomous Task Cycle)")

    # 3. Initial Heartbeat Check
    hb = CompanyHeartbeat.check_heartbeat()
    print(f"✅ Company Heartbeat: {hb['overall_label']}")

    # 4. Web Gateway
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    print(f"🚀 Cloud Gateway listening on http://{host}:{port}")
    print("=" * 60)

    uvicorn.run("server.app:app", host=host, port=port, reload=False, log_level="info")

if __name__ == "__main__":
    run_cloud()
