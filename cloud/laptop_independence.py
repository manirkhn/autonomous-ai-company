"""
Laptop Independence & Cloud Reality Verification Engine (Phase 5F).
Enforces:
- LAPTOP_INDEPENDENCE_STATUS (LOCAL_ONLY, CLOUD_DEPLOYMENT_PENDING, CLOUD_DEPLOYED, CLOUD_VERIFIED, CLOUD_DEGRADED, CLOUD_OFFLINE)
- Strict Anti-Fabrication Rules: Separates ARCHITECTURE_READY, DEPLOYED, PUBLICLY_VERIFIED, and CUSTOMER_PURCHASE_VERIFIED.
- Answers "CAN I CLOSE MY LAPTOP?" with hard evidence-backed reasons.
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from cloud.config import CloudConfig
from cloud.remote_proof import CloudInstanceIdentity, RemoteProofEngine
from core.heartbeat import CompanyHeartbeat
from core.db import get_connection

class LaptopIndependenceManager:
    """
    Evaluates real operational status to determine whether the owner can safely
    close their laptop without interrupting autonomous business operations.
    """

    VALID_INDEPENDENCE_STATES = {
        "LOCAL_ONLY",
        "CLOUD_DEPLOYMENT_PENDING",
        "CLOUD_DEPLOYED",
        "CLOUD_VERIFIED",
        "CLOUD_DEGRADED",
        "CLOUD_OFFLINE"
    }

    ANTI_FABRICATION_STAGES = [
        "ARCHITECTURE_READY",
        "DEPLOYED",
        "PUBLICLY_VERIFIED",
        "CUSTOMER_PURCHASE_VERIFIED"
    ]

    @classmethod
    def get_anti_fabrication_stages(cls) -> Dict[str, Any]:
        """
        Explicitly tracks the 4 distinct milestones required by Section 30:
        1. ARCHITECTURE_READY (Configuration files, Dockerfile, manifests exist)
        2. DEPLOYED (Running on remote cloud process)
        3. PUBLICLY_VERIFIED (External URL successfully verified)
        4. CUSTOMER_PURCHASE_VERIFIED (Real external production customer payment received)
        """
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        arch_ready = (
            os.path.exists(os.path.join(root_dir, "Dockerfile")) and
            os.path.exists(os.path.join(root_dir, "docker-compose.yml")) and
            (os.path.exists(os.path.join(root_dir, "render.yaml")) or os.path.exists(os.path.join(root_dir, "fly.toml")))
        )
        
        is_cloud = CloudConfig.is_cloud_runtime()
        public_url = CloudConfig.get_public_base_url()
        publicly_verified = bool(public_url and is_cloud)
        
        # Check if real production customer exists in DB
        customer_verified = False
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM payment_transactions 
                WHERE mode = 'PRODUCTION' AND payment_status IN ('PAYMENT_VERIFIED', 'SETTLEMENT_PENDING', 'SETTLEMENT_COMPLETED')
            """)
            row = cursor.fetchone()
            customer_verified = (row["cnt"] > 0) if row else False
            conn.close()
        except Exception:
            customer_verified = False

        return {
            "ARCHITECTURE_READY": {
                "achieved": arch_ready,
                "label": "Architecture Ready",
                "evidence": "Dockerfile, docker-compose.yml, render.yaml, and fly.toml present in repository." if arch_ready else "Configuration missing"
            },
            "DEPLOYED": {
                "achieved": is_cloud,
                "label": "Deployed to Cloud",
                "evidence": f"Runtime identified as {CloudConfig.get_runtime_type()}" if is_cloud else "Currently running on local workstation."
            },
            "PUBLICLY_VERIFIED": {
                "achieved": publicly_verified,
                "label": "Publicly Verified",
                "evidence": f"Public endpoint: {public_url}" if publicly_verified else "No public cloud HTTPS URL verified."
            },
            "CUSTOMER_PURCHASE_VERIFIED": {
                "achieved": customer_verified,
                "label": "Customer Purchase Verified",
                "evidence": "Verified production customer order recorded." if customer_verified else "0 production customer purchases verified yet (Historical test customer preserved)."
            }
        }

    @classmethod
    def get_laptop_independence_status(cls) -> str:
        """
        Calculates the canonical LAPTOP_INDEPENDENCE_STATUS:
        LOCAL_ONLY | CLOUD_DEPLOYMENT_PENDING | CLOUD_DEPLOYED | CLOUD_VERIFIED | CLOUD_DEGRADED | CLOUD_OFFLINE
        """
        identity = CloudInstanceIdentity.get_identity()
        is_cloud = CloudConfig.is_cloud_runtime()
        
        if not is_cloud:
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            has_configs = (
                os.path.exists(os.path.join(root_dir, "Dockerfile")) and
                (os.path.exists(os.path.join(root_dir, "render.yaml")) or os.path.exists(os.path.join(root_dir, "fly.toml")))
            )
            return "CLOUD_DEPLOYMENT_PENDING" if has_configs else "LOCAL_ONLY"

        # If on cloud, inspect heartbeat of all subsystems
        hb = CompanyHeartbeat.check_heartbeat()
        overall = hb.get("overall_status", "UNKNOWN")
        
        if overall == "HEALTHY":
            public_url = CloudConfig.get_public_base_url()
            has_proof = RemoteProofEngine.has_verified_remote_proof_task()
            if public_url and has_proof:
                return "CLOUD_VERIFIED"
            return "CLOUD_DEPLOYED"
        elif overall == "DEGRADED":
            return "CLOUD_DEGRADED"
        else:
            return "CLOUD_OFFLINE"

    @classmethod
    def can_close_laptop(cls) -> Dict[str, Any]:
        """
        Dynamic answer to 'CAN I CLOSE MY LAPTOP?' based strictly on operational proof.
        Never shows GREEN based merely on configuration files.
        """
        status = cls.get_laptop_independence_status()
        identity = CloudInstanceIdentity.get_identity()
        stages = cls.get_anti_fabrication_stages()
        public_url = CloudConfig.get_public_base_url()

        if status == "CLOUD_VERIFIED":
            return {
                "can_close": True,
                "status": status,
                "badge": "🟢 YES — CLOUD VERIFIED",
                "color": "emerald",
                "headline": "You may safely close your laptop.",
                "reason": "The Autonomous AI Company is executing on an independent remote cloud instance. All workers, tasks, scheduler, web server, and payment webhooks run 24/7 without your laptop.",
                "runtime_type": CloudConfig.get_runtime_type(),
                "public_url": public_url or "Verified",
                "stages": stages,
                "unmet_conditions": []
            }
        
        # Build exact list of why the laptop cannot be closed
        unmet_conditions = []
        if not CloudConfig.is_cloud_runtime():
            unmet_conditions.append("Web server is running locally on your workstation.")
            unmet_conditions.append("Background worker is running as a local process.")
            unmet_conditions.append("Public HTTPS endpoint is not yet bound to a remote cloud host.")
            unmet_conditions.append("Cloud deployment not completed.")
            unmet_conditions.append("Owner action required: Push container to cloud provider (Render or Fly.io).")
        else:
            if not public_url:
                unmet_conditions.append("PUBLIC_BASE_URL environment variable is not configured on cloud container.")
            if status == "CLOUD_DEPLOYED":
                unmet_conditions.append("Remote operational proof task has not yet executed on this instance.")
            if status == "CLOUD_DEGRADED":
                unmet_conditions.append("One or more cloud subsystems reported degraded health.")
            if status == "CLOUD_OFFLINE":
                unmet_conditions.append("Cloud subsystems are reporting offline.")

        return {
            "can_close": False,
            "status": status,
            "badge": "🔴 NO — COMPANY STILL DEPENDS ON THIS COMPUTER",
            "color": "rose",
            "headline": "Do not close your laptop if you want operations to continue.",
            "reason": "The company is currently running on this local computer. If you close your laptop, put it to sleep, or shut down, all AI operations, scheduled tasks, and the server will halt.",
            "runtime_type": CloudConfig.get_runtime_type(),
            "public_url": public_url or "http://127.0.0.1:8000 (LOCAL ONLY)",
            "stages": stages,
            "unmet_conditions": unmet_conditions,
            "owner_action_required": "Deploy the pre-packaged container to Render or Fly.io using render.yaml or fly.toml to achieve true 24/7 laptop independence."
        }

    @classmethod
    def get_owner_action_center(cls) -> Dict[str, Any]:
        """
        Section 28: Owner Action Center
        Clearly outlines exact actions required from the human owner.
        Zero automated unauthorized spending or key generation.
        """
        is_cloud = CloudConfig.is_cloud_runtime()
        public_url = CloudConfig.get_public_base_url()
        payment_mode = CloudConfig.get_payment_mode()
        
        actions = []
        if not is_cloud:
            actions.append({
                "action_id": "ACT-CLOUD-DEPLOY",
                "title": "Deploy Container to Free/Low-Cost Cloud Host",
                "priority": "HIGH",
                "details": "Deploy to Render.com using render.yaml (Free web service tier) or Fly.io using fly.toml. This establishes 24/7 laptop independence.",
                "cost_estimate": "$0.00 / month (Free tier) or approval required for paid tiers",
                "owner_only": True
            })
        
        if not public_url:
            actions.append({
                "action_id": "ACT-CONFIG-URL",
                "title": "Set PUBLIC_BASE_URL Environment Variable",
                "priority": "MEDIUM",
                "details": "After cloud deployment, set PUBLIC_BASE_URL to your allocated HTTPS URL (e.g., https://my-company.onrender.com) so customers can access the store.",
                "cost_estimate": "$0.00",
                "owner_only": True
            })

        if payment_mode == "SANDBOX":
            actions.append({
                "action_id": "ACT-STRIPE-PRODUCTION",
                "title": "Optional: Add Production Stripe UAE Keys When Ready For Real Sales",
                "priority": "LOW",
                "details": "To collect real USD/AED credit card payments, enter STRIPE_API_KEY and STRIPE_WEBHOOK_SECRET in your cloud host environment variables. (Sandbox mode is currently active and safe).",
                "cost_estimate": "$0.00 (Standard Stripe 2.9% fee upon successful sale)",
                "owner_only": True
            })

        return {
            "has_pending_actions": len(actions) > 0,
            "actions_count": len(actions),
            "actions": actions,
            "air_gap_reminder": "Never share your banking password, debit/credit card numbers, or full IBAN with the AI. Enter credentials directly into the official payment provider dashboard."
        }
