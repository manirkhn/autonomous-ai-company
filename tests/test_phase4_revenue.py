"""
Automated Test Suite for Phase 4: First Revenue Engine, Customer Acquisition & Autonomous Revenue.
Verifies all 40 requirements, zero-capital architecture, anti-fraud controls,
launch gates, verified revenue truth invariants, and Phase 1-3 security protections.
"""

import unittest
import os
import json
from core.db import init_db, get_connection
from revenue.discovery import RevenueDiscoveryEngine
from revenue.evaluator import OpportunityEvaluator
from revenue.offers import SalesAssetFactory
from revenue.products import RevenueProductFactory, ProductQAEvalError
from revenue.acquisition import CustomerAcquisitionEngine, AcquisitionPolicyError
from revenue.pipeline import SalesPipelineEngine
from revenue.ledger import RevenueLedgerEngine, BankingSecurityViolation
from revenue.delivery import CustomerDeliveryEngine
from revenue.support import CustomerSupportEngine
from revenue.refunds import RefundProcessingEngine
from revenue.bottlenecks import RevenueBottleneckEngine
from revenue.experiments import FirstRevenueExperimentEngine
from revenue.daily_loop import DailyRevenueLoop
from revenue.launch_gate import LaunchGateEngine, LaunchGateViolation
from core.firewall import FinancialFirewall
from tools.abstractions import VoiceSafetyGuard

class TestPhase4RevenueEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()

    # 1. Discovery & 10 Candidates (Parts 2, 3, 4, 5)
    def test_at_least_10_opportunities_researched(self):
        candidates = RevenueDiscoveryEngine.research_and_store_all()
        self.assertGreaterEqual(len(candidates), 10, "Must research at least 10 candidate opportunities.")
        for opp in candidates:
            self.assertIn("opportunity_id", opp)
            self.assertIn("name", opp)
            self.assertIn("problem", opp)
            self.assertIn("target_customer", opp)
            self.assertIn("competitors", opp)
            self.assertIn("estimated_price", opp)
            self.assertIn("evidence_sources", opp)
            self.assertIn("evidence_type", opp)
            self.assertEqual(opp["capital_required"], 0.0, "Zero-capital default required.")
            self.assertGreaterEqual(opp["automation_percentage"], 0.80)

    # 2. Evaluation & Selection (Parts 6 & 7)
    def test_opportunity_evaluation_and_ranking(self):
        ranked = OpportunityEvaluator.rank_all_candidates()
        self.assertGreaterEqual(len(ranked), 10)
        self.assertIn("composite_score", ranked[0])
        self.assertGreater(ranked[0]["composite_score"], 0.70)

        selection = OpportunityEvaluator.select_experiment_candidates()
        self.assertIsNotNone(selection["primary"])
        self.assertIsNotNone(selection["backup_1"])
        self.assertIsNotNone(selection["backup_2"])

        proposal = OpportunityEvaluator.generate_owner_approval_proposal()
        self.assertIn("approval_id", proposal)
        self.assertEqual(proposal["requested_spending"], 0.0)

    # 3. Product Factory & QA Hard Gate (Parts 8, 9, 10)
    def test_product_factory_and_qa_gate(self):
        manifest = RevenueProductFactory.create_product_package("OPP-P4-001")
        self.assertTrue(os.path.exists(manifest["package_path"]))

        qa = RevenueProductFactory.run_product_qa(manifest)
        self.assertEqual(qa["verdict"], "PASSED")
        self.assertTrue(qa["can_be_sold"])
        self.assertEqual(qa["checks"]["security"], "PASS")
        self.assertEqual(qa["checks"]["privacy"], "PASS")

        # Corrupted product test
        bad_manifest = dict(manifest)
        bad_manifest["package_path"] = "non_existent_dir_xyz"
        with self.assertRaises(ProductQAEvalError):
            RevenueProductFactory.run_product_qa(bad_manifest)

    # 4. Sales Asset Factory & Anti-Fraud (Part 11 & Part 32)
    def test_sales_assets_anti_fraud(self):
        assets = SalesAssetFactory.generate_sales_assets("OPP-P4-001")
        self.assertIn("landing_page_markdown", assets)
        self.assertIn("faq", assets)
        self.assertIn("outreach_template", assets)
        self.assertEqual(len(assets["testimonials"]), 0, "Fake testimonials strictly prohibited.")
        self.assertEqual(len(assets["customer_reviews"]), 0, "Fake reviews strictly prohibited.")
        self.assertTrue(assets["anti_fraud_audit"]["compliance_verified"])

    # 5. Customer Acquisition & Outreach Governance (Parts 12, 13, 14)
    def test_acquisition_and_outreach_governance(self):
        # Disallow deceptive marketing claims
        with self.assertRaises(AcquisitionPolicyError):
            CustomerAcquisitionEngine.create_campaign(
                target_definition="Local AI engineers",
                source="GitHub",
                consent_or_legal_basis="Legitimate interest",
                message="Earn 100% profit with guaranteed income!",
                frequency_limit="1 message per week",
                opt_out_method="Reply unsubscribe"
            )

        # Compliant campaign
        camp = CustomerAcquisitionEngine.create_campaign(
            target_definition="Local AI engineers",
            source="GitHub",
            consent_or_legal_basis="Legitimate developer interest",
            message="Check out our open-source benchmark tool.",
            frequency_limit="1 message max",
            opt_out_method="Reply unsubscribe"
        )
        self.assertIn("campaign_id", camp)
        self.assertEqual(camp["status"], "PENDING_APPROVAL")

        # Opt-out suppression
        CustomerAcquisitionEngine.record_opt_out(camp["campaign_id"], "developer@test.com")
        self.assertTrue(CustomerAcquisitionEngine.is_suppressed(camp["campaign_id"], "developer@test.com"))
        self.assertFalse(CustomerAcquisitionEngine.is_suppressed(camp["campaign_id"], "other@test.com"))

    # 6. Sales Pipeline 13 Stages (Part 15)
    def test_sales_pipeline_stages(self):
        lead_id = SalesPipelineEngine.create_lead(
            product_id="PROD-OPP-P4-001",
            customer_ref="lead_user_42",
            source="GITHUB_COMMUNITY",
            customer_type="INDIE_DEV",
            problem="Local LLM prompt degradation"
        )
        self.assertTrue(lead_id.startswith("LEAD-"))

        adv = SalesPipelineEngine.advance_stage(lead_id, "QUALIFIED", "Developer verified local Ollama setup")
        self.assertEqual(adv["current_stage"], "QUALIFIED")

        adv_paid = SalesPipelineEngine.advance_stage(lead_id, "PAID", "Customer checkout completed")
        self.assertEqual(adv_paid["current_stage"], "PAID")

        summary = SalesPipelineEngine.get_pipeline_summary()
        self.assertGreaterEqual(summary["paid_customers"], 1)

    # 7. Revenue Ledger Truth & Verification (Part 17 & Part 41)
    def test_revenue_ledger_verified_truth(self):
        # 1. Unverified / Pending transaction
        tx_pending = RevenueLedgerEngine.record_transaction(
            customer_id="cust_001",
            product_id="PROD-OPP-P4-001",
            order_id="ORD-9901",
            amount=29.0,
            payment_status="PENDING",
            verification_evidence=""
        )
        self.assertEqual(tx_pending["payment_status"], "PENDING")

        # Verified transactions require evidence
        with self.assertRaises(ValueError):
            RevenueLedgerEngine.record_transaction(
                customer_id="cust_002",
                product_id="PROD-OPP-P4-001",
                order_id="ORD-9902",
                amount=29.0,
                payment_status="VERIFIED",
                verification_evidence="" # Missing evidence
            )

        # 2. Legitimate verification
        tx_verified = RevenueLedgerEngine.verify_payment(tx_pending["revenue_id"], "stripe_pi_3Nxyz123")
        self.assertEqual(tx_verified["payment_status"], "VERIFIED")

        metrics = RevenueLedgerEngine.get_revenue_metrics()
        self.assertGreaterEqual(metrics["all_time"]["verified_actual_revenue"], 29.0)

    # 8. Owner Banking Air-Gap Invariant (Part 16 & Part 33)
    def test_owner_banking_air_gap(self):
        with self.assertRaises(BankingSecurityViolation):
            RevenueLedgerEngine.attempt_banking_withdrawal(100.0)

    # 9. Customer Delivery & Support (Parts 21 & 22)
    def test_customer_delivery_and_support(self):
        manifest = RevenueProductFactory.create_product_package("OPP-P4-001")
        deliv = CustomerDeliveryEngine.deliver_product(
            order_id="ORD-9901",
            customer_ref="cust_001",
            product_id=manifest["product_id"],
            package_source_dir=manifest["package_path"]
        )
        self.assertEqual(deliv["status"], "DELIVERED")
        self.assertTrue(os.path.exists(deliv["download_path"]))

        # Automated support FAQ
        ticket_faq = CustomerSupportEngine.submit_inquiry(
            customer_ref="cust_001",
            issue_type="TECHNICAL",
            content="What python version do I need?",
            order_id="ORD-9901"
        )
        self.assertEqual(ticket_faq["status"], "RESOLVED")
        self.assertIn("Python 3.8", ticket_faq["resolution"])

        # Escalation for refund
        ticket_esc = CustomerSupportEngine.submit_inquiry(
            customer_ref="cust_001",
            issue_type="BILLING",
            content="I need a refund please",
            order_id="ORD-9901"
        )
        self.assertTrue(ticket_esc["escalated_to_owner"])

    # 10. Refunds System (Part 23)
    def test_refund_system(self):
        req = RefundProcessingEngine.request_refund(
            order_id="ORD-9901",
            customer_id="cust_001",
            product_id="PROD-OPP-P4-001",
            amount=29.0,
            reason="Tool incompatible with legacy Python 3.6 setup"
        )
        self.assertEqual(req["status"], "REQUESTED")

        proc = RefundProcessingEngine.process_refund(req["refund_id"])
        self.assertEqual(proc["status"], "PROCESSED")
        self.assertEqual(proc["amount_refunded"], 29.0)

    # 11. Bottleneck Detection Engine (Part 25)
    def test_bottleneck_detection_engine(self):
        analysis = RevenueBottleneckEngine.analyze_bottlenecks()
        self.assertIn("current_bottleneck", analysis)
        self.assertIn("recommended_action", analysis)
        self.assertIn(analysis["current_bottleneck"], ["DEMAND", "TRAFFIC", "QUALIFICATION", "CONVERSION", "PAYMENT"])

    # 12. First Revenue Experiment & Learning (Parts 19, 20, 26)
    def test_first_revenue_experiment(self):
        exp = FirstRevenueExperimentEngine.launch_first_customer_experiment(
            opportunity_id="OPP-P4-001",
            target_customer_count=1,
            experiment_duration_days=7
        )
        self.assertEqual(exp["budget_usd"], 0.0)
        self.assertEqual(exp["status"], "ACTIVE")

        outcome = FirstRevenueExperimentEngine.record_experiment_outcome(
            experiment_id=exp["experiment_id"],
            outcome_status="SUCCESS",
            verified_sales_count=1,
            verified_revenue=29.0,
            lessons_learned="Direct developer outreach with privacy guarantee converts well.",
            next_action="Scale organic distribution on GitHub."
        )
        self.assertEqual(outcome["verified_sales"], 1)

    # 13. Daily Revenue Loop & CEO Report (Parts 24 & 31)
    def test_daily_revenue_loop_and_ceo_report(self):
        loop_res = DailyRevenueLoop.execute_daily_cycle()
        self.assertEqual(loop_res["status"], "COMPLETED")
        self.assertTrue(loop_res["firewall_active"])

        report = DailyRevenueLoop.generate_ceo_weekly_revenue_report()
        self.assertIn("financial_facts", report)
        self.assertIn("operational_estimates", report)
        self.assertIn("reinvestment_proposals", report)

    # 14. Real-World Launch Gate (Part 34)
    def test_launch_gate_hard_stop(self):
        readiness = LaunchGateEngine.generate_launch_readiness_report("OPP-P4-001")
        self.assertEqual(readiness["product_readiness"], "READY")
        self.assertTrue(readiness["launch_blocked_pending_approval"])

        # Attempting launch without owner approval must fail
        with self.assertRaises(LaunchGateViolation):
            LaunchGateEngine.attempt_launch(readiness["report_id"])

    # 15. Security Regressions (Part 33)
    def test_security_regressions_phase1_to_3(self):
        # Financial Firewall limits intact
        firewall = FinancialFirewall.get_settings()
        self.assertEqual(firewall["max_single_expense"], 0.0)
        self.assertEqual(firewall["max_daily_expense"], 0.0)

        # Voice Safety mass calling block
        voice_res = VoiceSafetyGuard.evaluate_call_safety(
            recipient_phone="+15550001",
            purpose="Cold telemarketing",
            consent_record=None, # Missing consent
            is_opted_out=False
        )
        self.assertFalse(voice_res["allowed"])

if __name__ == "__main__":
    unittest.main()
