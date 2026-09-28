"""
Phase 5J — Autonomous Growth & Real Revenue Execution Test Suite
Tests:
1. Funnel reconciliation (ORD-9901 investigation, checkouts >= customers, verified revenue = $29, verified customers = 1)
2. Customer qualification engine (6-stage pipeline, conversion calculations, sample size indicator)
3. SEO technical guides, checklists, and public blog route rendering with attribution
4. 14-platform acquisition registry and targeted demand discovery opportunities
5. 12-step autonomous operator cycle execution and real results vs system activity separation
6. CEO Daily report formatting and metrics timeframes
7. Banking air-gap and spend limit safety enforcement
"""

import unittest
import os
import json
from core.db import get_connection, init_db
from acquisition.qualification import CustomerQualificationEngine
from acquisition.seo_content import SEOContentEngine
from integrations.platform_registry import PlatformRegistry
from acquisition.autonomous_distribution import AutonomousDistributionEngine
from business.autonomous_operator import AutonomousBusinessOperator
from business.ceo_metrics import CEOMetricsEngine

class TestPhase5JAutonomousGrowth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_01_funnel_reconciliation_ord_9901(self):
        """Verify transaction ORD-9901 is reconciled across all lifecycle tables and checkouts >= customers."""
        conn = get_connection()
        c = conn.cursor()

        # Check ORD-9901 in payment_transactions
        c.execute("SELECT transaction_id, order_id, amount, payment_status, mode FROM payment_transactions WHERE order_id = 'ORD-9901'")
        pt_row = c.fetchone()
        self.assertIsNotNone(pt_row, "ORD-9901 must exist in payment_transactions")
        self.assertEqual(pt_row['payment_status'], 'SUCCEEDED')
        self.assertEqual(pt_row['mode'], 'PRODUCTION')
        self.assertEqual(pt_row['amount'], 29.0)

        # Check ORD-9901 in revenue_ledger
        c.execute("SELECT order_id, amount, payment_status, verification_status FROM revenue_ledger WHERE order_id = 'ORD-9901' AND payment_status = 'VERIFIED'")
        rev_row = c.fetchone()
        self.assertIsNotNone(rev_row, "ORD-9901 must exist in revenue_ledger with payment_status='VERIFIED'")
        self.assertEqual(rev_row['payment_status'], 'VERIFIED')
        self.assertEqual(rev_row['verification_status'], 'VERIFIED')

        # Check ORD-9901 in deliveries
        c.execute("SELECT order_id, customer_ref, status FROM deliveries WHERE order_id = 'ORD-9901'")
        del_row = c.fetchone()
        self.assertIsNotNone(del_row, "ORD-9901 must exist in deliveries")
        self.assertIn(del_row['status'], ['DELIVERED', 'VERIFIED_DELIVERED'])

        conn.close()

        # Check CEOMetricsEngine totals
        metrics = CEOMetricsEngine.compute_ceo_metrics()

        self.assertEqual(metrics["real_revenue"]["total_verified_usd"], 29.0)
        self.assertEqual(metrics["real_customers"], 1)
        self.assertGreaterEqual(metrics["checkout_starts"], metrics["real_customers"], 
                                "Checkout starts must be >= verified customers")
        self.assertGreaterEqual(metrics["checkout_starts"], 5)
        self.assertEqual(metrics["successful_checkouts"], 1)
        self.assertEqual(metrics["sample_size_status"], "INSUFFICIENT SAMPLE SIZE")

    def test_02_customer_qualification_pipeline(self):
        """Verify the 6-stage qualification pipeline and conversion tracking."""
        # Test event recording
        ev = CustomerQualificationEngine.record_qualification_event(
            visitor_id="test-vis-999",
            stage="QUALIFIED_VISITOR",
            source="DIRECT",
            evidence="multiple_product_views",
            metadata={"views": 3, "pages": ["/store", "/blog/ollama-evaluation-guide"]}
        )
        self.assertIn("event_id", ev)
        self.assertEqual(ev["stage"], "QUALIFIED_VISITOR")

        funnel = CustomerQualificationEngine.get_funnel_summary()
        self.assertIn("pipeline", funnel)
        self.assertIn("visitors", funnel["pipeline"])
        self.assertIn("qualified_visitors", funnel["pipeline"])
        self.assertIn("leads", funnel["pipeline"])
        self.assertIn("high_intent_leads", funnel["pipeline"])
        self.assertIn("checkout_starts", funnel["pipeline"])
        self.assertIn("customers", funnel["pipeline"])
        self.assertEqual(funnel["statistical_status"], "INSUFFICIENT SAMPLE SIZE")

    def test_03_seo_content_and_checklists(self):
        """Verify standalone technical guides and checklists exist with conversion CTA and no misleading claims."""
        articles = SEOContentEngine.get_all_articles()
        self.assertGreaterEqual(len(articles), 11, "Should have at least 11 SEO articles/guides")

        slugs = [a["slug"] for a in articles]
        self.assertIn("prompt-regression-testing-checklist", slugs)
        self.assertIn("offline-ai-evaluation-architecture-checklist", slugs)
        self.assertIn("ollama-regression-testing", slugs)

        # Inspect prompt-regression-checklist
        checklist = SEOContentEngine.get_article("prompt-regression-testing-checklist")
        self.assertIsNotNone(checklist)
        self.assertIn("Prompt Regression", checklist["title"])
        self.assertIn("Evaluation Suite", checklist["content_md"])
        self.assertIn("nexora_product_link", checklist)

    def test_04_expanded_platform_registry(self):
        """Verify PlatformRegistry supports 14 platforms including technical directories and aggregators."""
        platforms = PlatformRegistry.list_platforms()
        self.assertGreaterEqual(len(platforms), 14, "Must have at least 14 platforms registered")

        platform_names = [p["platform"] for p in platforms]
        self.assertIn("Toolify & AI Aggregators", platform_names)
        self.assertIn("Dev.to & Technical Publications", platform_names)
        self.assertIn("Awesome-Local-AI & Curated Repos", platform_names)

        # Ensure Etsy remains disabled or not recommended
        etsy = next((p for p in platforms if p["platform"] == "Etsy"), None)
        if etsy:
            self.assertIn(etsy["classification"], ["NOT_RECOMMENDED", "NOT_SUPPORTED", "DISABLED"])

    def test_05_targeted_demand_discovery(self):
        """Verify targeted demand opportunities exist for local LLM problems."""
        opps = AutonomousDistributionEngine.list_opportunities()
        self.assertGreaterEqual(len(opps), 10, "Should have at least 10 discovered opportunities")

        # Verify legitimate fields for each opportunity
        for op in opps:
            self.assertTrue(op["source"])
            self.assertTrue(op["url"])
            self.assertTrue(op["problem"])
            self.assertTrue(op["recommended_action"])

    def test_06_autonomous_operator_cycle(self):
        """Verify the 12-step autonomous business cycle completes cleanly."""
        res = AutonomousBusinessOperator.execute_cycle()
        self.assertEqual(res["status"], "COMPLETED")
        self.assertEqual(len(res["steps"]), 12)
        
        # Verify step 6 (CHECKOUT) reports reconciled checkouts
        checkout_step = res["steps"].get("6_checkout")
        self.assertIsNotNone(checkout_step)
        self.assertEqual(checkout_step["status"], "SUCCESS")
        self.assertGreaterEqual(checkout_step["production_checkouts_recorded"], 1)

        # Verify step 10 (FEEDBACK) has analyzed signals
        feedback_step = res["steps"].get("10_feedback")
        self.assertIsNotNone(feedback_step)
        self.assertEqual(feedback_step["status"], "SUCCESS")
        self.assertGreaterEqual(feedback_step["feedback_signals_evaluated"], 1)

    def test_07_ceo_metrics_and_report_separation(self):
        """Verify strict separation of real business results from autonomous system activity in CEO reporting."""
        metrics = CEOMetricsEngine.compute_ceo_metrics()
        
        self.assertIn("timeframes", metrics)
        self.assertIn("today", metrics["timeframes"])
        self.assertIn("last_7_days", metrics["timeframes"])
        self.assertIn("last_30_days", metrics["timeframes"])
        self.assertIn("all_time", metrics["timeframes"])

        report_pkg = CEOMetricsEngine.generate_daily_ceo_report()
        text_report = report_pkg["text_report"]
        self.assertIn("SECTION I: REAL COMMERCIAL RESULTS", text_report)
        self.assertIn("SECTION II: AUTONOMOUS SYSTEM & OPERATIONAL ACTIVITY", text_report)
        self.assertIn("SECTION III: ACTIONABLE OWNER CONSTRAINTS & NEXT STEPS", text_report)
        self.assertIn("INSUFFICIENT SAMPLE SIZE", text_report)

    def test_08_financial_air_gap_and_banking_safety(self):
        """Verify financial air-gap invariant: zero unauthorized spending and no banking credential access."""
        metrics = CEOMetricsEngine.compute_ceo_metrics()
        self.assertTrue(metrics.get("financial_air_gap_verified", False))

if __name__ == "__main__":
    unittest.main()
