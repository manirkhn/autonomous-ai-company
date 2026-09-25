"""
Automated Test Suite for Phase 5E: Sales, Marketing & Customer Acquisition Command Center.

Verifies:
1. What We Are Selling product display (name, id, prices, problem solved, target persona, checkout active)
2. Strict separation of Historical Verified Results from New Production Results (zero metric inflation)
3. Zero fake metrics rule: Display '0 VERIFIED' or exact ground-truth count, never estimated numbers
4. Free-first architecture & Financial Firewall enforcement ($0 unapproved spending ceiling for campaigns)
5. MarketingActivityManager: real activity logging, statuses (DRAFTED, APPROVED, PUBLISHED, etc.), local/remote tags
6. 'Where Did We Market' dashboard summary: only displays channels with verified activities
7. 'What Did The AI Do Today?' chronological activity timeline
8. 12-stage visual customer acquisition funnel
9. CustomerPersonaEngine: strict separation of VERIFIED_SIGNAL vs HYPOTHESIS
10. MarketingContentEngine: grounded technical guides without fabricated testimonials or benchmarks
11. MoneyPipelineDiagnostics: empirical bottleneck identification and plain-English diagnostics
12. MarketingExperimentEngine: autonomous experiment lifecycle & governance
13. ProductImprovementLoop: Research AI -> Product AI -> CEO AI improvement proposals
14. MarketingCommandCenter: consolidated high-integrity executive payload
15. Daily CEO Report: 10 sections present and Section 34 Truth Check 100% compliant
16. Banking air-gap & zero credential storage invariants
"""

import unittest
import json
import uuid
from datetime import datetime, timezone

from core.db import init_db, get_connection
from core.firewall import FinancialFirewall, FinancialFirewallViolation
from marketing.command_center import MarketingCommandCenter
from marketing.activity import MarketingActivityManager
from marketing.campaigns import CampaignManager
from marketing.personas import CustomerPersonaEngine
from marketing.content import MarketingContentEngine
from marketing.funnel import CustomerAcquisitionFunnelEngine
from marketing.diagnostics import MoneyPipelineDiagnostics
from marketing.experiments import MarketingExperimentEngine
from marketing.product_loop import ProductImprovementLoop
from reporting.daily_ceo_report import DailyCEOReportGenerator


class TestPhase5EMarketingCommandCenter(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()

    def setUp(self):
        # Clean any test rows created during test runs
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM marketing_activities WHERE activity_id LIKE 'TEST-%'")
        cursor.execute("DELETE FROM marketing_campaigns WHERE campaign_id LIKE 'TEST-%'")
        cursor.execute("DELETE FROM marketing_experiments WHERE experiment_id LIKE 'TEST-%'")
        cursor.execute("DELETE FROM product_improvement_proposals WHERE proposal_id LIKE 'TEST-%'")
        conn.commit()
        conn.close()

    def test_01_what_we_are_selling_data_integrity(self):
        """Verifies Section 2: What We Are Selling contains all required CEO-friendly fields."""
        prod = MarketingCommandCenter.get_what_we_are_selling()
        self.assertEqual(prod["product_id"], "PROD-LLM-EVAL-001")
        self.assertIn("Local LLM", prod["product_name"])
        self.assertEqual(prod["price_usd"], 29.0)
        self.assertEqual(prod["price_aed"], 106.50)
        self.assertEqual(prod["product_status"], "ACTIVE")
        self.assertEqual(prod["checkout_status"], "ACTIVE")
        self.assertIn("problem_solved", prod)
        self.assertIn("target_customer", prod)
        self.assertIn("what_customer_receives", prod)
        self.assertIn("delivery_method", prod)
        # Verify verified customer & revenue counts match ground truth
        self.assertGreaterEqual(prod["verified_customers"], 1)
        self.assertGreaterEqual(prod["verified_revenue_usd"], 29.0)

    def test_02_historical_vs_production_revenue_separation(self):
        """Verifies Section 3: Historical verified revenue is strictly separated from new production revenue."""
        funnel_data = CustomerAcquisitionFunnelEngine.get_visual_funnel_data()
        
        # Historical results
        self.assertEqual(funnel_data["historical_verified_customers"], 1)
        self.assertEqual(funnel_data["historical_verified_revenue_usd"], 29.0)
        
        # New production results
        self.assertIn("new_production_verified_customers", funnel_data)
        self.assertIn("new_production_verified_revenue_usd", funnel_data)
        
        # Verification that historical is NEVER conflated with current production sales
        self.assertNotEqual(
            funnel_data["new_production_verified_revenue_usd"],
            funnel_data["lifetime_verified_revenue_usd"],
            "New production revenue must not be conflated with historical revenue"
        )
        self.assertEqual(
            funnel_data["lifetime_verified_revenue_usd"],
            funnel_data["historical_verified_revenue_usd"] + funnel_data["new_production_verified_revenue_usd"]
        )

    def test_03_zero_cost_financial_safety_enforcement(self):
        """Verifies Section 1 & 10: $0.00 spending ceiling is strictly enforced on marketing campaigns."""
        # Attempting to create a campaign with unapproved spend > 0 must raise FinancialFirewallViolation
        with self.assertRaises(FinancialFirewallViolation):
            CampaignManager.create_campaign({
                "campaign_id": "TEST-CAMP-PAID",
                "name": "Paid Ads Experiment",
                "objective": "Lead Gen",
                "product_id": "PROD-LLM-EVAL-001",
                "target_persona": "AI Engineers",
                "channel": "Google Ads",
                "budget": 50.0,  # Violates $0 unapproved limit
                "owner_approval": False
            })

        # Permitted: Free-first campaign with $0.00 budget
        cid = CampaignManager.create_campaign({
            "campaign_id": "TEST-CAMP-FREE",
            "name": "Zero-Cost Organic Developer Docs",
            "objective": "Direct Technical Acquisition",
            "product_id": "PROD-LLM-EVAL-001",
            "target_persona": "Local LLM Developers",
            "channel": "Developer Docs",
            "budget": 0.0,
            "owner_approval": True
        })
        self.assertEqual(cid, "TEST-CAMP-FREE")

    def test_04_marketing_activity_logging_and_statuses(self):
        """Verifies Section 5 & 6: Marketing activity logging, execution statuses, and evidence."""
        act_id = "TEST-ACT-001"
        res_id = MarketingActivityManager.record_activity({
            "activity_id": act_id,
            "campaign_id": "TEST-CAMP-FREE",
            "employee_id": "marketing_ai",
            "channel": "Developer Forum",
            "platform": "HackerNews",
            "target_persona": "Local Model Testers",
            "activity_type": "technical_breakdown",
            "content_reference": "DOC-GUIDE-001",
            "destination_url": "https://company.ai/checkout",
            "execution_status": "DRAFTED",
            "result": "Technical draft authored",
            "evidence_reference": "EVID-DRAFT-99",
            "execution_mode": "LOCAL"
        })
        self.assertEqual(res_id, act_id)

        # Transition status through lifecycle
        updated = MarketingActivityManager.update_activity_status(
            activity_id=act_id,
            new_status="APPROVED",
            result="Approved by CEO AI"
        )
        self.assertTrue(updated)
        act = MarketingActivityManager.get_activity(act_id)
        self.assertEqual(act["execution_status"], "APPROVED")

        # Publish
        MarketingActivityManager.update_activity_status(
            activity_id=act_id,
            new_status="PUBLISHED",
            result="Content published to channel"
        )
        act = MarketingActivityManager.get_activity(act_id)
        self.assertEqual(act["execution_status"], "PUBLISHED")

    def test_05_where_did_we_market_channel_aggregation(self):
        """Verifies Section 5: Channels only appear after verified activities are performed."""
        # Record an activity on a specific channel
        test_plat = f"Platform-{uuid.uuid4().hex[:6]}"
        MarketingActivityManager.record_activity({
            "activity_id": f"TEST-ACT-{uuid.uuid4().hex[:6]}",
            "employee_id": "marketing_ai",
            "channel": "Community",
            "platform": test_plat,
            "target_persona": "Engineers",
            "activity_type": "post",
            "execution_status": "PUBLISHED",
            "result": "Published benchmark breakdown",
            "evidence_reference": "EVID-PUB-01"
        })

        summary = MarketingActivityManager.get_where_we_marketed_summary()
        matched = [c for c in summary if c["platform"] == test_plat]
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0]["channel"], "Community")
        self.assertGreaterEqual(matched[0]["total_activities"], 1)

    def test_06_what_did_the_ai_do_today_timeline(self):
        """Verifies Section 8: Daily activity timeline returns chronological execution logs."""
        timeline = MarketingActivityManager.get_what_did_ai_do_today_timeline()
        self.assertIsInstance(timeline, list)
        for item in timeline:
            self.assertIn("timestamp", item)
            self.assertIn("employee_id", item)
            self.assertIn("activity_type", item)
            self.assertIn("platform", item)
            self.assertIn("execution_status", item)
            self.assertIn("result", item)
            self.assertIn("execution_mode", item)

    def test_07_twelve_stage_customer_acquisition_funnel(self):
        """Verifies Section 4: All 12 funnel stages exist with exact verified numbers (no estimations)."""
        funnel = CustomerAcquisitionFunnelEngine.get_visual_funnel_data()
        stages = funnel["funnel_stages"]
        
        required_stages = [
            "researched_opportunities",
            "target_prospects",
            "marketing_outreach_attempts",
            "responses",
            "qualified_leads",
            "checkout_visits",
            "checkout_starts",
            "payment_attempts",
            "verified_payments",
            "customers",
            "delivered_products",
            "repeat_referral_customers"
        ]
        
        for stage in required_stages:
            self.assertIn(stage, stages)
            self.assertIsInstance(stages[stage], int)
            self.assertGreaterEqual(stages[stage], 0)

        # Verification of conversion rates dictionary
        self.assertIn("conversion_rates", funnel)
        self.assertEqual(funnel["data_quality"], "VERIFIED")

    def test_08_customer_persona_engine_evidence_classification(self):
        """Verifies Section 11: Customer personas clearly distinguish VERIFIED_SIGNAL from HYPOTHESIS."""
        personas = CustomerPersonaEngine.get_all_personas()
        self.assertGreaterEqual(len(personas), 3)

        for p in personas:
            self.assertIn(p["signal_type"], ["VERIFIED_SIGNAL", "HYPOTHESIS"])
            self.assertIn("problem", p)
            self.assertIn("likely_use_case", p)
            self.assertIn("relevant_channel", p)
            self.assertIn("acquisition_method", p)
            self.assertIn("potential_offer_angle", p)

    def test_09_marketing_content_engine_grounding(self):
        """Verifies Section 13: Content assets are grounded in actual product specifications without fabrication."""
        assets = MarketingContentEngine.get_all_content_assets()
        self.assertGreaterEqual(len(assets), 2)

        for a in assets:
            self.assertEqual(a["grounded_product_id"], "PROD-LLM-EVAL-001")
            self.assertEqual(a["verified_claims_only"], True)
            self.assertEqual(a["zero_fabricated_benchmarks"], True)
            self.assertIn(a["content_type"], ["technical_guide", "faq", "comparison_matrix"])

    def test_10_money_pipeline_diagnostics(self):
        """Verifies Section 17: Empirical identification of bottlenecks in the money pipeline."""
        diag = MoneyPipelineDiagnostics.run_money_pipeline_diagnostics()
        self.assertIn("primary_bottleneck", diag)
        self.assertIn("bottleneck_stage", diag)
        self.assertIn("plain_english_diagnosis", diag)
        self.assertIn("evidence", diag)
        self.assertIn("recommended_remedy", diag)
        self.assertIn("pipeline_stages", diag)
        # Should detect top-of-funnel or qualification bottleneck from real telemetry
        self.assertIn(diag["bottleneck_stage"], ["TRAFFIC", "OUTREACH", "QUALIFICATION", "CHECKOUT", "PAYMENT"])

    def test_11_autonomous_marketing_experiments(self):
        """Verifies Section 18: Creation and tracking of marketing experiments with governance decisions."""
        exp_id = "TEST-EXP-001"
        created_id = MarketingExperimentEngine.create_experiment({
            "experiment_id": exp_id,
            "hypothesis": "Publishing offline prompt regression guide on dev forum generates 50 organic visits",
            "problem": "Lack of top-of-funnel developer discovery",
            "channel": "Developer Forum",
            "action": "Educational markdown breakdown",
            "expected_measurable_signal": "50 unique checkout clicks",
            "spend": 0.0,
            "status": "ACTIVE"
        })
        self.assertEqual(created_id, exp_id)

        # Update outcome with decision
        updated = MarketingExperimentEngine.record_experiment_result(
            experiment_id=exp_id,
            actual_result="Generated 18 verified visits, 0 checkouts",
            decision="MODIFY",
            status="COMPLETED"
        )
        self.assertTrue(updated)
        exps = MarketingExperimentEngine.list_experiments()
        saved = next(e for e in exps if e["experiment_id"] == exp_id)
        self.assertEqual(saved["decision"], "MODIFY")
        self.assertEqual(saved["status"], "COMPLETED")

    def test_12_product_improvement_loop(self):
        """Verifies Section 24: Research AI -> Product AI -> CEO AI proposal loop."""
        prop_id = "TEST-PROP-001"
        created_id = ProductImprovementLoop.create_proposal({
            "proposal_id": prop_id,
            "customer_problem": "Developers request support for Ollama custom prompt templates",
            "evidence": "Observed in 3 local developer discussions",
            "proposed_change": "Add ollama template formatter to benchmark runner",
            "expected_benefit": "Reduces onboarding friction for local model engineers",
            "originator_ai": "research_ai"
        })
        self.assertEqual(created_id, prop_id)

        # CEO approves proposal
        updated = ProductImprovementLoop.update_proposal_status(
            proposal_id=prop_id,
            status="APPROVED",
            actual_outcome="Scheduled for v1.1 update"
        )
        self.assertTrue(updated)
        props = ProductImprovementLoop.list_proposals()
        saved = next(p for p in props if p["proposal_id"] == prop_id)
        self.assertEqual(saved["status"], "APPROVED")

    def test_13_marketing_command_center_full_payload(self):
        """Verifies consolidated MarketingCommandCenter payload includes all Phase 5E components."""
        payload = MarketingCommandCenter.get_full_command_center_payload()
        self.assertIn("what_we_are_selling", payload)
        self.assertIn("customer_acquisition_funnel", payload)
        self.assertIn("where_did_we_market", payload)
        self.assertIn("marketing_employee_desks", payload)
        self.assertIn("what_did_ai_do_today_timeline", payload)
        self.assertIn("campaigns", payload)
        self.assertIn("customer_personas", payload)
        self.assertIn("marketing_content_assets", payload)
        self.assertIn("money_pipeline_diagnostics", payload)
        self.assertIn("autonomous_experiments", payload)
        self.assertIn("next_24_hours", payload)
        self.assertEqual(payload["data_quality"], "VERIFIED")

    def test_14_daily_ceo_report_phase5e_integration_and_truth_check(self):
        """Verifies Section 19: Daily CEO Report contains all 10 sections and passes Section 34 Truth Check."""
        report = DailyCEOReportGenerator.generate_report()
        self.assertEqual(report["validation_status"], "PASSED")
        
        md = report["content_md"]
        # Verify all 10 required sections from Section 19 are rendered in markdown
        self.assertIn("1. WHAT WE ARE SELLING", md)
        self.assertIn("2. HOW MANY PEOPLE BOUGHT", md)
        self.assertIn("3. MONEY", md)
        self.assertIn("4. MARKETING TODAY", md)
        self.assertIn("5. SALES TODAY", md)
        self.assertIn("6. FUNNEL BOTTLENECK", md)
        self.assertIn("7. EMPLOYEE ACTIVITY", md)
        self.assertIn("8. FAILED EXPERIMENTS", md)
        self.assertIn("9. NEXT 24 HOURS", md)
        self.assertIn("10. OWNER ACTION REQUIRED", md)

        # Verify separation of historical vs production results in CEO report
        self.assertIn("HISTORICAL VERIFIED RESULTS", md)
        self.assertIn("CURRENT PRODUCTION RESULTS", md)

    def test_15_security_banking_air_gap_preservation(self):
        """Verifies Section 1: Sensitive banking credentials and account numbers are strictly barred."""
        # Try recording an activity with a banking IBAN or credit card
        with self.assertRaises(ValueError):
            MarketingActivityManager.record_activity({
                "activity_id": "TEST-ACT-LEAK",
                "employee_id": "marketing_ai",
                "channel": "Direct",
                "platform": "Email",
                "activity_type": "outreach",
                "result": "Sent IBAN AE070331234567890123456 to client",  # Banking leak attempt
                "execution_status": "DRAFTED"
            })


if __name__ == "__main__":
    unittest.main()
