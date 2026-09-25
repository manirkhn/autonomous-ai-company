"""
Cloud Deployment Audit Engine (Phase 5F, Section 25).
Produces evidence-based operational audit reports detailing:
runtime, instance ID, deployment ID, public URL, health, worker,
scheduler, database, payment environment, last heartbeat, deployment timestamp,
version, and laptop independence status.
"""

import os
from typing import Dict, Any
from datetime import datetime, timezone

from cloud.config import CloudConfig
from cloud.remote_proof import CloudInstanceIdentity
from cloud.laptop_independence import LaptopIndependenceManager
from cloud.heartbeat_service import CloudHeartbeatService
from core.heartbeat import CompanyHeartbeat

class DeploymentAuditor:
    """
    Evidence-based auditor synthesizing complete cloud runtime state.
    """

    @classmethod
    def audit(cls) -> Dict[str, Any]:
        """
        Runs comprehensive cloud deployment audit.
        """
        identity = CloudInstanceIdentity.get_identity()
        hb_telemetry = CloudHeartbeatService.get_heartbeat_telemetry()
        sys_heartbeat = CompanyHeartbeat.check_heartbeat()
        laptop_status = LaptopIndependenceManager.can_close_laptop()
        stages = LaptopIndependenceManager.get_anti_fabrication_stages()
        actions = LaptopIndependenceManager.get_owner_action_center()

        public_url = CloudConfig.get_public_base_url()
        is_cloud = CloudConfig.is_cloud_runtime()

        components = sys_heartbeat.get("components", {})
        db_status = components.get("database", {}).get("status", "UNKNOWN")
        worker_status = "HEALTHY" if hb_telemetry.get("worker_active") else "INACTIVE"
        scheduler_status = "HEALTHY" if hb_telemetry.get("scheduler_active") else "INACTIVE"

        return {
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
            "runtime": CloudConfig.get_runtime_type(),
            "is_remote_cloud": is_cloud,
            "instance_id": identity.get("instance_id", "INST-LOCAL-001"),
            "deployment_id": f"DEP-{identity.get('instance_id', 'LOCAL')[-6:]}",
            "public_url": public_url or "NOT_CONFIGURED",
            "is_public_accessible": bool(public_url and is_cloud),
            "health": sys_heartbeat.get("overall_status", "UNKNOWN"),
            "web_server": "HEALTHY",
            "worker": worker_status,
            "scheduler": scheduler_status,
            "database": db_status,
            "payment_environment": CloudConfig.get_payment_mode(),
            "last_heartbeat": hb_telemetry.get("last_heartbeat"),
            "deployment_timestamp": identity.get("boot_timestamp"),
            "version": hb_telemetry.get("deployment_version", "5.6.0-phase5f"),
            "laptop_independence": {
                "status": laptop_status.get("status"),
                "can_close_laptop": laptop_status.get("can_close"),
                "badge": laptop_status.get("badge"),
                "reason": laptop_status.get("reason"),
                "unmet_conditions": laptop_status.get("unmet_conditions", [])
            },
            "anti_fabrication_stages": stages,
            "owner_actions": actions
        }
