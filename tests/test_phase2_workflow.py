"""
End-to-End Workflow & Business Pipeline Test Suite (Phase 2).
Tests:
- Opportunity Discovery & Multi-Attribute Scoring
- Automated Agent Handoff Pipeline
- Product Factory & Quality Control
- Sales Pipeline, Verified Delivery & Customer Feedback Loop
- Owner Time Minimization Metrics & Reinvestment Preparation
"""

import os
import sys
import unittest
import json

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from core.db import init_db
from discovery.engine import OpportunityDiscoveryEngine
from factory.product_factory import ProductFactory
from factory.quality_control import QualityControlEngine
from factory.sales_asset_factory import SalesAssetFactory
from sales.pipeline import SalesPipelineEngine
from sales.delivery import DeliveryEngine
from feedback.engine import CustomerFeedbackEngine
from orchestration.loop import OrchestrationLoop
from core.owner_metrics import OwnerMetricsEngine
from finance.analytics import FinanceEngine

class TestPhase2Workflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        OpportunityDiscoveryEngine.seed_initial_researched_opportunities()

    def test_01_opportunity_scoring_and_ranking(self):
        """Verify opportunity scoring incorporates evidence quality, margins, and automation."""
        opps = OpportunityDiscoveryEngine.get_opportunities()
        self.assertGreaterEqual(len(opps), 3)

        top_opp = opps[0]
        self.assertIn("name", top_opp)
        self.assertIn("composite_score", top_opp)
        self.assertGreater(top_opp["composite_score"], 60.0)
        self.assertIn(top_opp["evidence_classification"], ["DIRECT_EVIDENCE", "INDIRECT_EVIDENCE"])

    def test_02_automated_handoff_pipeline(self):
        """Verify end-to-end autonomous handoff from Opportunity to MVP, QA, and Approval Request."""
        opps = OpportunityDiscoveryEngine.get_opportunities()
        opp_id = opps[0]["opportunity_id"]

        result = OrchestrationLoop.run_automated_handoff_pipeline(opp_id)
        self.assertEqual(result["status"], "AWAITING_OWNER_APPROVAL")
        self.assertIn("product_id", result)
        self.assertIn("approval_id", result)
        self.assertEqual(len(result["handoff_steps"]), 7)

        # Verify MVP deliverable exists on disk
        product = ProductFactory.get_product(result["product_id"])
        self.assertIsNotNone(product)
        self.assertEqual(product["qa_status"], "PASSED")
        self.assertTrue(len(product["listing_copy"]) > 0)

    def test_03_qa_engine_catches_flaws(self):
        """Verify QA engine rejects deliverables with placeholders or syntax errors."""
        pid = ProductFactory.create_product_draft("Flawed Script", "CODE_UTILITY", "Test requirements")
        # Build deliverable with forbidden TODO placeholder
        ProductFactory.build_mvp_deliverable(pid, "flawed.py", "def test():\n    # TODO: write code\n    pass", "EMP-004-CREATION")
        
        report = QualityControlEngine.inspect_and_verify_product(pid)
        self.assertEqual(report["verdict"], "FAILED")
        self.assertTrue(any("PLACEHOLDERS_DETECTED" in f for f in report["checks_failed"]))

    def test_04_sales_pipeline_and_delivery(self):
        """Verify sales pipeline lead registration, order fulfillment, and delivery proof."""
        # 1. Register Lead
        lead_id = SalesPipelineEngine.create_lead(
            source="Developer Forum Discussion",
            customer_type="Indie Developer",
            problem="Needs automated security guardrails",
            contact_method="Public Comment Response",
            consent_basis="Direct user inquiry in public thread asking for recommendations"
        )
        self.assertTrue(lead_id.startswith("LED-"))

        # 2. Advance Lead to Purchased
        SalesPipelineEngine.advance_lead_stage(lead_id, "PURCHASED", outcome="Purchased 1 license at $29.00")

        # 3. Create a valid product deliverable for delivery test
        pid = ProductFactory.create_product_draft("Delivery Test Asset", "TEMPLATE", "Requirements")
        ProductFactory.build_mvp_deliverable(pid, "template.md", "# Clean Verified Template", "EMP-004-CREATION")

        # 4. Fulfill order with delivery engine
        delivery = DeliveryEngine.process_order_and_deliver(
            order_id="ORD-9901",
            product_id=pid,
            customer_ref="customer@example.com",
            payment_verified=True
        )
        self.assertEqual(delivery["status"], "DELIVERED")
        self.assertIn("Verified checksum", delivery["evidence"])

    def test_05_customer_feedback_loop(self):
        """Verify customer feedback is captured and routed to corporate memory."""
        unique_pid = f"PRD-TEST-{os.urandom(4).hex()}"
        fid = CustomerFeedbackEngine.record_feedback(
            product_id=unique_pid,
            customer_ref="user@test.com",
            feedback_type="FEATURE_REQUEST",
            content="Please add TypeScript support in addition to Python.",
            resolution="Logged as potential v1.1 enhancement for Product Manager"
        )
        self.assertTrue(fid.startswith("FDB-"))
        feedbacks = CustomerFeedbackEngine.get_feedback(product_id=unique_pid)
        self.assertEqual(len(feedbacks), 1)

    def test_06_owner_metrics_and_reinvestment_policy(self):
        """Verify owner time tracking and zero-reinvestment default policy."""
        metrics = OwnerMetricsEngine.get_metrics()
        self.assertIn("owner_minutes_week", metrics)
        self.assertIn("automated_tasks_count", metrics)

        finances = FinanceEngine.get_financial_summary()
        policy = finances["reinvestment_policy"]
        self.assertEqual(policy["reinvestment_percentage"], 0.0) # Part 23
        self.assertTrue(policy["owner_approval_required"])

if __name__ == "__main__":
    unittest.main()
