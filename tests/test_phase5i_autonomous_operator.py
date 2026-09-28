"""
Test Suite for Phase 5I: Universal Autonomous Business Operator.

Validates:
1. Platform Integration Registry & Classification (Autonomous, Partial, Owner Required, Not Recommended)
2. Tangible Product Physical Verification (Physical Deliverables Exist)
3. 12-Step Autonomous Commercial Operating Loop
4. Autonomous Distribution & Demand Discovery (Zero-spam guardrails)
5. Autonomous Support Grounding & Escalation
6. Real Truth-Grounded CEO Metrics & Daily Report Dispatch to manirkhn@gmail.com
7. Owner Action Center Justification Schema (7 required fields)
8. API Endpoints for Operator, Platforms, Support, and CEO Metrics
9. Financial Air-Gap Enforcement
"""

import os
import json
import unittest
from starlette.testclient import TestClient

from server.app import app
from integrations.platform_registry import PlatformRegistry
from business.autonomous_operator import AutonomousBusinessOperator
from business.ceo_metrics import CEOMetricsEngine
from acquisition.autonomous_distribution import AutonomousDistributionEngine
from acquisition.owner_actions import OwnerActionCenter
from support.autonomous_support import AutonomousSupportEngine
from revenue.ledger import RevenueLedgerEngine, BankingSecurityViolation

class TestPhase5IAutonomousOperator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_1_platform_registry_and_classification(self):
        """Test 1: Platforms are tracked with factual APIs, OAuth, and compliance classifications."""
        platforms = PlatformRegistry.sync_all_platforms()
        self.assertGreaterEqual(len(platforms), 9)

        summary = PlatformRegistry.get_summary()
        self.assertIn("autonomous", summary)
        self.assertIn("owner_action_required", summary)
        self.assertIn("operating_channels", summary)
        self.assertGreater(summary["operating_channels"], 0)

        # Check Gumroad
        gumroad = PlatformRegistry.get_platform("Gumroad")
        self.assertIsNotNone(gumroad)
        self.assertEqual(gumroad["classification"], "PARTIALLY_AUTONOMOUS")
        self.assertEqual(gumroad["requires_owner_action"], 1)
        self.assertIn("Gumroad", gumroad["owner_action_reason"])

        # Check Lemon Squeezy
        ls = PlatformRegistry.get_platform("Lemon Squeezy")
        self.assertIsNotNone(ls)
        self.assertEqual(ls["classification"], "PARTIALLY_AUTONOMOUS")
        self.assertEqual(ls["requires_owner_action"], 1)
        self.assertIn("KYC", ls["owner_action_reason"])

        # Check Etsy
        etsy = PlatformRegistry.get_platform("Etsy")
        self.assertIsNotNone(etsy)
        self.assertEqual(etsy["classification"], "NOT_RECOMMENDED")

    def test_2_physical_product_verification(self):
        """Test 2: Products must physically exist on disk with valid checksums before registration."""
        prod = AutonomousBusinessOperator.verify_and_register_flagship_product()
        self.assertEqual(prod["product_id"], "PROD-OPP-P4-001")
        self.assertEqual(prod["creation_status"], "COMPLETED_AND_VERIFIED")
        self.assertEqual(prod["sales_status"], "READY_FOR_PURCHASE")
        self.assertGreaterEqual(prod["verified_files_count"], 3)

        # Confirm ZIP file physically exists
        zip_path = AutonomousBusinessOperator.FLAGSHIP_ZIP_PATH
        self.assertTrue(os.path.exists(zip_path))
        self.assertGreater(os.path.getsize(zip_path), 0)

    def test_3_twelve_step_autonomous_operator_loop(self):
        """Test 3: Full 12-step commercial cycle executes non-blocking and successfully."""
        cycle_result = AutonomousBusinessOperator.execute_cycle()
        self.assertEqual(cycle_result["status"], "COMPLETED")
        self.assertIn("steps", cycle_result)
        steps = cycle_result["steps"]

        expected_steps = [
            "1_opportunity", "2_product", "3_distribution", "4_traffic",
            "5_lead", "6_checkout", "7_sale", "8_delivery",
            "9_support", "10_feedback", "11_improvement", "12_next_opportunity"
        ]
        for step in expected_steps:
            self.assertIn(step, steps, f"Step {step} missing from operator cycle!")
            self.assertEqual(steps[step]["status"], "SUCCESS", f"Step {step} failed: {steps[step]}")

    def test_4_autonomous_distribution_and_demand(self):
        """Test 4: Customer acquisition finds demand across genuine sources without spamming."""
        opps = AutonomousDistributionEngine.discover_customer_demand()
        self.assertGreaterEqual(len(opps), 4)

        stats = AutonomousDistributionEngine.get_acquisition_stats()
        self.assertIn("total_opportunities", stats)
        self.assertIn("sources", stats)
        self.assertIn("GitHub", stats["sources"])
        self.assertIn("Reddit", stats["sources"])

    def test_5_autonomous_support_engine(self):
        """Test 5: Routine questions resolved autonomously; refunds escalated to owner."""
        # Routine question
        res_routine = AutonomousSupportEngine.handle_customer_inquiry(
            customer_email="dev@example.com",
            product_id="PROD-OPP-P4-001",
            question="Does this tool work completely offline without sending telemetry?"
        )
        self.assertEqual(res_routine["status"], "RESOLVED")
        self.assertGreaterEqual(res_routine["confidence"], 0.85)
        self.assertIn("offline", res_routine["answer"].lower())

        # Refund escalation
        res_refund = AutonomousSupportEngine.handle_customer_inquiry(
            customer_email="buyer@example.com",
            product_id="PROD-OPP-P4-001",
            question="I want to request a full refund for my order."
        )
        self.assertEqual(res_refund["status"], "OWNER_ACTION_REQUIRED")
        self.assertIn("escalated", res_refund["answer"].lower())

    def test_6_ceo_metrics_and_daily_report(self):
        """Test 6: Truthful CEO metrics computed and daily report dispatched to manirkhn@gmail.com."""
        metrics = CEOMetricsEngine.compute_ceo_metrics()
        self.assertIn("real_revenue", metrics)
        self.assertIn("real_customers", metrics)
        self.assertIn("active_products", metrics)
        self.assertIn("current_bottleneck", metrics)
        self.assertTrue(metrics["financial_air_gap_verified"])

        # Test daily report generation
        report_res = CEOMetricsEngine.generate_daily_ceo_report()
        self.assertIn("report_id", report_res)
        self.assertEqual(report_res["recipient"], "manirkhn@gmail.com")
        self.assertTrue(report_res["delivery"]["success"])

    def test_7_owner_action_seven_field_schema(self):
        """Test 7: Owner actions contain all 7 required justification fields."""
        actions = OwnerActionCenter.list_actions(status="ACTION_REQUIRED")
        self.assertGreater(len(actions), 0)

        required_fields = [
            "why", "what_is_blocked", "exact_action", "estimated_time",
            "platform", "security_impact", "what_antigravity_will_do_after_completion"
        ]
        for a in actions:
            for field in required_fields:
                self.assertIn(field, a, f"Owner action {a.get('action_id')} missing field {field}")
                self.assertNotEqual(a[field], "", f"Owner action {a.get('action_id')} has empty field {field}")

    def test_8_api_endpoints_phase5i(self):
        """Test 8: REST endpoints return valid telemetry for dashboard cockpit."""
        # 1. Operator status
        r_status = self.client.get("/api/operator/status")
        self.assertEqual(r_status.status_code, 200)
        self.assertEqual(r_status.json()["operator_state"], "ACTIVE_RUNNING")

        # 2. Operator pulse
        r_pulse = self.client.post("/api/operator/pulse")
        self.assertEqual(r_pulse.status_code, 200)
        self.assertEqual(r_pulse.json()["status"], "COMPLETED")

        # 3. Integrations platforms
        r_plat = self.client.get("/api/integrations/platforms")
        self.assertEqual(r_plat.status_code, 200)
        self.assertIn("platforms", r_plat.json())

        # 4. CEO metrics
        r_ceo = self.client.get("/api/business/ceo-metrics")
        self.assertEqual(r_ceo.status_code, 200)
        self.assertIn("real_revenue", r_ceo.json())

        # 5. CEO report send
        r_rep = self.client.post("/api/business/ceo-report/send")
        self.assertEqual(r_rep.status_code, 200)
        self.assertEqual(r_rep.json()["recipient"], "manirkhn@gmail.com")

        # 6. Support submit
        r_supp = self.client.post("/api/support/submit", json={
            "customer_email": "api_test@example.com",
            "question": "What Python versions are supported?"
        })
        self.assertEqual(r_supp.status_code, 200)
        self.assertIn("Python", r_supp.json()["answer"])

    def test_9_financial_air_gap(self):
        """Test 9: AI is strictly prohibited from banking withdrawals or transfers."""
        with self.assertRaises(BankingSecurityViolation):
            RevenueLedgerEngine.attempt_banking_withdrawal(100.0)

if __name__ == "__main__":
    unittest.main()
