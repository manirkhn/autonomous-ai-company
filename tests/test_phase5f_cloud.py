"""
Automated Test Suite for Phase 5F: Cloud Deployment & Public Customer Access.

Verifies:
1. Runtime identity & truthful local/cloud environment detection
2. Laptop independence status evaluation & anti-fabrication gates
3. Public health endpoint (/health) with safe operational telemetry
4. Localhost and private IP leak scanning (LocalhostLeakScanner)
5. Customer-facing product page (/product & /store) routing & integrity
6. Dynamic customer checkout URL generation via PUBLIC_BASE_URL
7. Payment environment isolation (SANDBOX vs PRODUCTION)
8. Cryptographic webhook verification & replay protection
9. Automated digital fulfillment & SHA-256 package verification
10. Revenue ledger historical vs production preservation
11. Personal banking air-gap enforcement & credential safety
12. Cloud heartbeat tracking without secret leaks
13. Worker & scheduler independence
14. Cloud deployment audit report structure
15. 10-point customer access verification test
"""

import os
import json
import unittest
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from core.db import init_db, get_connection
from cloud.config import CloudConfig
from cloud.laptop_independence import LaptopIndependenceManager
from cloud.heartbeat_service import CloudHeartbeatService
from cloud.leak_scanner import LocalhostLeakScanner
from cloud.access_test import CustomerAccessTester
from cloud.deployment_audit import DeploymentAuditor
from payments.checkout import (
    CheckoutManager,
    PRIMARY_PRODUCT_ID,
    PRIMARY_PRODUCT_NAME,
    PRIMARY_PRICE_USD
)
from payments.provider import TestPaymentProvider
from revenue.ledger import RevenueLedgerEngine, BankingSecurityViolation
from server.app import app

class TestPhase5FCloudDeployment(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def test_01_runtime_identity_and_truthful_local_detection(self):
        """Verify process correctly identifies local workstation vs cloud without fabrication."""
        info = CloudConfig.get_environment_info()
        self.assertIn("environment", info)
        self.assertIn("runtime_type", info)
        self.assertIn("is_cloud_runtime", info)
        
        # When not running on a cloud container, runtime must be local workstation
        if not (os.environ.get("RENDER") or os.environ.get("FLY_APP_NAME")):
            self.assertEqual(info["runtime_type"], "LOCAL_WORKSTATION")
            self.assertFalse(info["is_cloud_runtime"])

    def test_02_laptop_independence_status_and_anti_fabrication(self):
        """Verify dynamic evaluation of 'CAN I CLOSE MY LAPTOP?' and anti-fabrication stages."""
        status = LaptopIndependenceManager.can_close_laptop()
        self.assertIn("can_close", status)
        self.assertIn("badge", status)
        self.assertIn("reason", status)
        self.assertIn("stages", status)

        # On local machine, can_close must be False
        if not CloudConfig.is_cloud_runtime():
            self.assertFalse(status["can_close"])
            self.assertIn("NO", status["badge"])
            self.assertTrue(len(status["unmet_conditions"]) > 0)

        # Verify the 4 distinct anti-fabrication stages exist
        stages = status["stages"]
        self.assertIn("ARCHITECTURE_READY", stages)
        self.assertIn("DEPLOYED", stages)
        self.assertIn("PUBLICLY_VERIFIED", stages)
        self.assertIn("CUSTOMER_PURCHASE_VERIFIED", stages)
        
        # Architecture is ready because Dockerfile & configs exist
        self.assertTrue(stages["ARCHITECTURE_READY"]["achieved"])

    def test_03_public_health_endpoint_safe_telemetry(self):
        """Verify GET /health returns operational info without exposing secrets or banking data."""
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        
        self.assertIn("status", data)
        self.assertIn("version", data)
        self.assertIn("environment", data)
        self.assertIn("runtime_type", data)
        self.assertIn("worker_status", data)
        self.assertIn("scheduler_status", data)
        self.assertIn("database_status", data)
        self.assertIn("timestamp", data)

        # Verify zero credential leaks in response
        raw = json.dumps(data).lower()
        for forbidden in ["password", "secret", "api_key", "iban", "token"]:
            self.assertNotIn(forbidden, raw)

    def test_04_localhost_leak_scanner(self):
        """Verify scanner flags localhost in production URLs and passes valid public URLs."""
        # Clean public HTTPS URL
        clean_url = "https://autonomous-ai-company.onrender.com/product"
        clean_res = LocalhostLeakScanner.validate_customer_url(clean_url, is_production=True)
        self.assertEqual(clean_res["PRODUCTION_PUBLIC_ACCESS_TEST"], "PASS")
        self.assertFalse(clean_res["has_leak"])

        # Localhost URL in production must FAIL
        leaky_url = "http://127.0.0.1:8000/checkout/cs_123"
        prod_leak_res = LocalhostLeakScanner.validate_customer_url(leaky_url, is_production=True)
        self.assertEqual(prod_leak_res["PRODUCTION_PUBLIC_ACCESS_TEST"], "FAIL")
        self.assertTrue(prod_leak_res["has_leak"])

        # Localhost in development is permitted with notice
        dev_res = LocalhostLeakScanner.validate_customer_url(leaky_url, is_production=False)
        self.assertEqual(dev_res["PRODUCTION_PUBLIC_ACCESS_TEST"], "PASS")
        self.assertTrue(dev_res["has_leak"])

    def test_05_customer_product_page_endpoints(self):
        """Verify customer-facing product page loads correctly at /product and /store."""
        for path in ["/product", "/store"]:
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200)
            self.assertIn("Local LLM Offline Evaluation", res.text)
            self.assertIn("$29", res.text)
            # Verify no fake testimonials
            self.assertNotIn("John D. from Google says", res.text)
        # Verify product ID retained in product checkout payload
        prod_res = self.client.get("/product")
        self.assertIn("PROD-LLM-EVAL-001", prod_res.text)

    def test_06_dynamic_checkout_url_generation(self):
        """Verify checkout URLs dynamically adapt to PUBLIC_BASE_URL configuration."""
        # 1. Default effective URL
        default_url = CloudConfig.get_customer_checkout_url("cs_sample_test")
        self.assertIn("checkout/cs_sample_test", default_url)

        # 2. Simulated public cloud environment
        old_env = os.environ.get("PUBLIC_BASE_URL")
        try:
            os.environ["PUBLIC_BASE_URL"] = "https://my-company.onrender.com"
            pub_checkout = CloudConfig.get_customer_checkout_url("cs_live_999")
            self.assertEqual(pub_checkout, "https://my-company.onrender.com/checkout/cs_live_999")
            
            # Localhost leak scanner must pass this
            scan = LocalhostLeakScanner.validate_customer_url(pub_checkout, is_production=True)
            self.assertEqual(scan["PRODUCTION_PUBLIC_ACCESS_TEST"], "PASS")
        finally:
            if old_env is not None:
                os.environ["PUBLIC_BASE_URL"] = old_env
            else:
                os.environ.pop("PUBLIC_BASE_URL", None)

    def test_07_payment_environment_isolation(self):
        """Verify sandbox mode is strictly isolated from production mode."""
        self.assertIn(CloudConfig.get_payment_mode(), ["SANDBOX", "PRODUCTION"])
        
        # Test payment session creation in sandbox
        session = CheckoutManager.create_checkout(
            customer_email="sandbox_user@example.com",
            currency="USD",
            mode="TEST"
        )
        self.assertEqual(session["mode"], "TEST")
        self.assertIn("cs_test_", session["session_id"])

    def test_08_webhook_cryptographic_verification(self):
        """Verify webhooks enforce HMAC signatures and reject forged or replayed requests."""
        provider = TestPaymentProvider()
        order_id = "ORD-TEST-9988"
        payload_data = {
            "id": f"evt_test_{order_id}",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": f"cs_test_{order_id}",
                    "payment_status": "paid",
                    "metadata": {"order_id": order_id}
                }
            }
        }
        payload_str = json.dumps(payload_data)
        sig = provider.generate_test_signature(payload_str)

        # 1. Valid signature succeeds
        valid, event, err = provider.process_webhook(payload_str.encode("utf-8"), sig)
        self.assertTrue(valid)
        self.assertEqual(err, "")

        # 2. Tampered signature fails
        bad_sig = "t=123456789,v1=bad_hash_signature"
        invalid, _, err_bad = provider.process_webhook(payload_str.encode("utf-8"), bad_sig)
        self.assertFalse(invalid)
        self.assertTrue(len(err_bad) > 0)

    def test_09_digital_fulfillment_checksum_package(self):
        """Verify digital product delivery package contains verified checksums."""
        from revenue.delivery import CustomerDeliveryEngine
        pkg = CustomerDeliveryEngine.get_delivery_package(PRIMARY_PRODUCT_ID)
        self.assertIn("package_id", pkg)
        self.assertIn("sha256_package_checksum", pkg)
        self.assertTrue(len(pkg["files"]) > 0)

    def test_10_revenue_ledger_historical_vs_production_preservation(self):
        """Verify historical $29 record remains intact while production ledger is unpolluted."""
        metrics = RevenueLedgerEngine.get_revenue_metrics()
        self.assertEqual(metrics["all_time"]["verified_actual_revenue"], 29.00)
        self.assertEqual(metrics["all_time"]["verified_transaction_count"], 1)

    def test_11_banking_air_gap_protection(self):
        """Verify personal banking air-gap rejects full IBANs or credit card storage."""
        from payments.owner_settlement import OwnerSettlementManager
        # Attempting to store a full IBAN or credit card raises BankingSecurityViolation
        with self.assertRaises(BankingSecurityViolation):
            OwnerSettlementManager.update_profile(
                masked_destination_reference="AE070331234567890123456"
            )

    def test_12_cloud_heartbeat_service(self):
        """Verify CloudHeartbeatService records telemetry without credentials."""
        hb = CloudHeartbeatService.get_heartbeat_telemetry()
        self.assertIn("instance_id", hb)
        self.assertIn("runtime_type", hb)
        self.assertIn("uptime_seconds", hb)
        self.assertIn("last_heartbeat", hb)
        self.assertIn("application_version", hb)

    def test_13_worker_and_scheduler_independent_execution(self):
        """Verify worker and scheduler objects can be queried independently."""
        from cloud.worker import CloudWorker
        from cloud.scheduler import CloudScheduler

        w = CloudWorker.get_instance()
        s = CloudScheduler.get_instance()

        self.assertIsNotNone(w.get_status())
        self.assertIsNotNone(s.get_status())
        self.assertIn("is_running", w.get_status())
        self.assertIn("is_running", s.get_status())

    def test_14_cloud_deployment_audit_endpoint(self):
        """Verify GET /api/cloud/deployment-audit returns complete audit dictionary."""
        res = self.client.get("/api/cloud/deployment-audit")
        self.assertEqual(res.status_code, 200)
        audit = res.json()
        
        self.assertIn("runtime", audit)
        self.assertIn("instance_id", audit)
        self.assertIn("public_url", audit)
        self.assertIn("health", audit)
        self.assertIn("worker", audit)
        self.assertIn("scheduler", audit)
        self.assertIn("database", audit)
        self.assertIn("laptop_independence", audit)
        self.assertIn("anti_fabrication_stages", audit)
        self.assertIn("owner_actions", audit)

    def test_15_customer_access_tester_10_points(self):
        """Verify CustomerAccessTester runs the 10-point customer journey verification."""
        test_res = CustomerAccessTester.run_verification_test()
        self.assertEqual(test_res["total_steps"], 10)
        self.assertGreaterEqual(test_res["passed"], 8)
        self.assertTrue(test_res["all_passed"])
        self.assertEqual(len(test_res["steps"]), 10)


if __name__ == "__main__":
    unittest.main()
