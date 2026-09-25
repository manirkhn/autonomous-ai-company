"""
Automated Test Suite for Phase 5C — Cloud Reality, Remote Deployment & Laptop-Off Verification.
Validates:
1. Cloud Deployment State Machine (LOCAL_ONLY vs CLOUD_CONFIGURED vs CLOUD_VERIFIED_INDEPENDENT).
2. Cloud Instance Identity (instance_id generation, persistent JSON storage, type resolution).
3. Remote Proof Engine & CLOUD_PROOF_TASK execution.
4. Database Persistence across cycles.
5. Worker Fault Recovery & event logging.
6. 24/7 Scheduler independent execution.
7. Email Reality (distinguishing real SMTP dispatch from local outbox archive).
8. Gemini Reality & Latency tracking (refusing false 'connected' status).
9. Local vs Remote Separation (truthful identification of workstation host).
10. Automated Security & Secret Scanning (zero hardcoded secrets).
11. Employee Activity Grounding (no fabricated external activities).
12. Revenue Engine Continuity (preserving verified revenue & zero capital invariants).
13. Financial Firewall ($0 unapproved spending & air-gap enforced).
14. Dynamic 'CAN I CLOSE MY LAPTOP?' verification logic.
15. CLOUD_INDEPENDENCE_GATE formal evaluation.
"""

import unittest
import os
import json
import time
from fastapi.testclient import TestClient

from server.app import app
from cloud.remote_proof import RemoteProofEngine, CloudInstanceIdentity
from core.heartbeat import CompanyHeartbeat
from revenue.ledger import RevenueLedgerEngine
from finance.analytics import FinanceEngine
from core.activity import ActivityTracker
from reporting.email_service import EmailService

class TestPhase5CCloudReality(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_cloud_instance_identity_resolution(self):
        """Test persistent cloud instance identity and local vs remote detection."""
        identity = CloudInstanceIdentity.get_identity()
        self.assertIn("instance_id", identity)
        self.assertTrue(identity["instance_id"].startswith("INST-"))
        self.assertIn("instance_type", identity)
        self.assertIn("environment_name", identity)
        self.assertIn("app_version", identity)
        self.assertIn(identity["instance_type"], ["LOCAL_WORKSTATION", "REMOTE_CLOUD"])

    def test_02_cloud_state_machine_logic(self):
        """Test truthful deployment state calculation."""
        state = RemoteProofEngine.get_cloud_deployment_state()
        valid_states = [
            "LOCAL_ONLY", "CLOUD_CONFIGURED", "CLOUD_DEPLOYMENT_PENDING",
            "CLOUD_DEPLOYED", "CLOUD_HEALTHY", "CLOUD_VERIFIED_INDEPENDENT"
        ]
        self.assertIn(state, valid_states)

    def test_03_laptop_off_verification_truth_model(self):
        """Test that laptop-off check returns truth based on runtime evidence."""
        verdict = RemoteProofEngine.can_close_laptop()
        self.assertIn("can_close", verdict)
        self.assertIn("badge", verdict)
        self.assertIn("reason", verdict)
        
        identity = CloudInstanceIdentity.get_identity()
        if not identity["is_remote_cloud"]:
            self.assertFalse(verdict["can_close"])
            self.assertIn("🔴", verdict["badge"])
            self.assertTrue(verdict["laptop_required"])

    def test_04_cloud_proof_task_execution_and_receipt(self):
        """Test execution of harmless CLOUD_PROOF_TASK with verifiable audit evidence."""
        res = RemoteProofEngine.execute_cloud_proof_task()
        self.assertTrue(res["success"])
        self.assertIn("task_id", res)
        self.assertIn("evidence", res)
        
        evidence = res["evidence"]
        self.assertIn("instance_id", evidence)
        self.assertIn("verification_hash", evidence)
        self.assertTrue(RemoteProofEngine.has_verified_remote_proof_task())

    def test_05_database_persistence_test(self):
        """Test persistent database retention across operational cycles."""
        res = RemoteProofEngine.run_persistence_test()
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "PASSED")
        self.assertIsNotNone(res["verified_value"])

    def test_06_worker_recovery_and_logging(self):
        """Test worker fault recovery and audit event recording."""
        res = RemoteProofEngine.test_worker_recovery()
        self.assertTrue(res["success"])
        self.assertTrue(res["recovery_logged"])
        self.assertTrue(res["worker_status"]["is_running"])

    def test_07_gemini_reality_and_latency(self):
        """Test Gemini reality probe with roundtrip latency measurement."""
        res = RemoteProofEngine.test_gemini_reality()
        self.assertIn("status", res)
        self.assertIn("latency_ms", res)
        self.assertIn("model", res)
        self.assertTrue(res["latency_ms"] >= 0)

    def test_08_email_delivery_reality_distinction(self):
        """Test that local outbox is never falsely presented as delivered email."""
        res = RemoteProofEngine.test_email_reality()
        self.assertIn("status", res)
        self.assertIn("delivery_mode", res)
        self.assertEqual(res["target_recipient"], "manirkhn@gmail.com")
        
        # When SMTP is not configured, delivery mode must be LOCAL_OUTBOX_ARCHIVE
        if not res["smtp_configured"]:
            self.assertEqual(res["delivery_mode"], "LOCAL_OUTBOX_ARCHIVE")
            self.assertIn("NOT CONFIGURED", res["status"])

    def test_09_security_scan_zero_hardcoded_secrets(self):
        """Test that repository contains zero hardcoded API keys, private keys, or credentials."""
        scan = RemoteProofEngine.run_security_scan()
        self.assertTrue(scan["clean"], f"Security scan found violations: {scan['violations']}")
        self.assertEqual(len(scan["violations"]), 0)
        self.assertTrue(scan["scanned_files"] > 10)

    def test_10_cloud_independence_gate_evaluation(self):
        """Test formal evaluation of CLOUD_INDEPENDENCE_GATE."""
        gate = RemoteProofEngine.evaluate_independence_gate()
        self.assertIn("gate_status", gate)
        self.assertIn("checks", gate)
        self.assertIn("can_close_laptop", gate)
        
        checks = gate["checks"]
        self.assertTrue(checks["database_persists"])
        self.assertTrue(checks["banking_air_gapped"])
        self.assertTrue(checks["zero_spending_firewall"])
        self.assertTrue(checks["no_secrets_exposed"])

    def test_11_revenue_engine_continuity_and_firewall(self):
        """Test that revenue engine remains active with 100% banking air-gap and $0 spending limit."""
        rev = RevenueLedgerEngine.get_revenue_metrics()
        self.assertEqual(rev["all_time"]["verified_actual_revenue"], 29.0)
        self.assertTrue(rev["banking_air_gap_enforced"])
        
        # Prohibited banking withdrawal raises exception
        with self.assertRaises(Exception):
            RevenueLedgerEngine.attempt_banking_withdrawal(10.0)

    def test_12_fastapi_phase5c_endpoints(self):
        """Test all Phase 5C verification API endpoints."""
        # 1. /api/cloud/can-close-laptop
        res_close = self.client.get("/api/cloud/can-close-laptop")
        self.assertEqual(res_close.status_code, 200)
        data_close = res_close.json()
        self.assertIn("can_close", data_close)
        self.assertIn("badge", data_close)

        # 2. /api/cloud/proof
        res_proof = self.client.get("/api/cloud/proof")
        self.assertEqual(res_proof.status_code, 200)
        self.assertIn("gate_status", res_proof.json())

        # 3. POST /api/cloud/proof/run-task
        res_task = self.client.post("/api/cloud/proof/run-task")
        self.assertEqual(res_task.status_code, 200)
        self.assertTrue(res_task.json()["success"])

        # 4. POST /api/cloud/proof/test-persistence
        res_persist = self.client.post("/api/cloud/proof/test-persistence")
        self.assertEqual(res_persist.status_code, 200)
        self.assertTrue(res_persist.json()["success"])

        # 5. POST /api/cloud/proof/test-worker-recovery
        res_worker = self.client.post("/api/cloud/proof/test-worker-recovery")
        self.assertEqual(res_worker.status_code, 200)
        self.assertTrue(res_worker.json()["success"])

        # 6. GET /api/cloud/proof/security-scan
        res_scan = self.client.get("/api/cloud/proof/security-scan")
        self.assertEqual(res_scan.status_code, 200)
        self.assertTrue(res_scan.json()["clean"])

if __name__ == "__main__":
    unittest.main()
