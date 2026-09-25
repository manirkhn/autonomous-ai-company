"""
Cloud Heartbeat & Public Health Service (Phase 5F, Sections 9 & 10).
Provides safe operational health endpoint (GET /health) and tracks
instance lifecycle, worker, scheduler, and database heartbeats without
exposing secrets, credentials, or private banking details.
"""

import time
import socket
import platform
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from cloud.config import CloudConfig
from cloud.remote_proof import CloudInstanceIdentity
from core.db import get_connection

class CloudHeartbeatService:
    """
    Heartbeat and public health service tracking instance uptime, worker status,
    and database availability.
    """
    _start_timestamp: float = time.time()
    _last_heartbeat_iso: Optional[str] = None
    _deployment_version: str = "5.6.0-phase5f"

    @classmethod
    def record_heartbeat(cls) -> Dict[str, Any]:
        """
        Records an active heartbeat pulse.
        """
        cls._last_heartbeat_iso = datetime.now(timezone.utc).isoformat()
        return cls.get_heartbeat_telemetry()

    @classmethod
    def get_heartbeat_telemetry(cls) -> Dict[str, Any]:
        """
        Returns full cloud heartbeat metrics for dashboard and audit.
        """
        identity = CloudInstanceIdentity.get_identity()
        now_iso = datetime.now(timezone.utc).isoformat()
        if not cls._last_heartbeat_iso:
            cls._last_heartbeat_iso = now_iso

        # Check worker status
        from cloud.worker import CloudWorker
        worker = CloudWorker.get_instance()
        worker_status = worker.get_status()

        # Check scheduler status
        from cloud.scheduler import CloudScheduler
        scheduler = CloudScheduler.get_instance()
        scheduler_status = scheduler.get_status()

        return {
            "instance_id": identity.get("instance_id", "INST-LOCAL-001"),
            "runtime_type": CloudConfig.get_runtime_type(),
            "is_remote_cloud": CloudConfig.is_cloud_runtime(),
            "environment": CloudConfig.get_environment(),
            "start_time": datetime.fromtimestamp(cls._start_timestamp, timezone.utc).isoformat(),
            "uptime_seconds": round(time.time() - cls._start_timestamp, 1),
            "last_heartbeat": cls._last_heartbeat_iso,
            "worker_heartbeat": worker_status.get("last_poll_time") or cls._last_heartbeat_iso,
            "worker_active": worker_status.get("is_running", False),
            "scheduler_heartbeat": scheduler_status.get("last_run_timestamp") or cls._last_heartbeat_iso,
            "scheduler_active": scheduler_status.get("is_running", False),
            "application_version": identity.get("app_version", "5.6.0-phase5f"),
            "deployment_version": cls._deployment_version
        }

    @classmethod
    def get_safe_health_status(cls) -> Dict[str, Any]:
        """
        Safe public health payload for GET /health (Section 9).
        Guarantees zero exposure of API keys, DB passwords, or banking details.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        
        # Test DB connection
        db_healthy = False
        db_msg = "CONNECTED"
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            conn.close()
            db_healthy = True
        except Exception as e:
            db_healthy = False
            db_msg = f"ERROR: {type(e).__name__}"

        from cloud.worker import CloudWorker
        from cloud.scheduler import CloudScheduler
        worker_active = CloudWorker.get_instance().is_running
        scheduler_active = CloudScheduler.get_instance().is_running

        app_status = "HEALTHY" if (db_healthy and worker_active and scheduler_active) else "DEGRADED"
        if not db_healthy:
            app_status = "UNHEALTHY"

        return {
            "status": app_status,
            "version": cls._deployment_version,
            "environment": CloudConfig.get_environment(),
            "runtime_type": CloudConfig.get_runtime_type(),
            "worker_status": "RUNNING" if worker_active else "STOPPED",
            "scheduler_status": "RUNNING" if scheduler_active else "STOPPED",
            "database_status": db_msg,
            "timestamp": now_iso
        }
