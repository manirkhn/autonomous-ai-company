"""
Phase 5H Test Suite: Multi-Channel Customer Acquisition & Marketplace Sales Engine
Verifies:
- Acquisition channel registry (all 9 channels)
- Marketplace status & specs (Etsy, Gumroad, Lemon Squeezy)
- Etsy compliance audit (ETSY_STATUS = NOT_RECOMMENDED_FOR_THIS_PRODUCT)
- Gumroad integration state and transaction verification rule
- Lemon Squeezy integration state and owner KYC action requirement
- Developer discovery engine, opportunity qualification, and anti-spam gates
- Technical SEO content engine (all 9 required topics) and draft-review-approval workflow
- Full-funnel UTM tracking and source attribution to verified payment and fulfillment
- Channel performance view with strict 0 / N/A / Unknown semantics and mode separation
- 7-Stage business conversion funnel tracking
- Product expansion opportunity queue with evidence-based ranking
- Owner Action Center with explicit non-fabricated actions
- Acquisition automation schedules
- API endpoints via TestClient
"""

import os
import unittest
from starlette.testclient import TestClient

from core.db import init_db, get_connection
from acquisition.channels import ChannelRegistry
from acquisition.etsy import EtsyMarketplaceEngine
from acquisition.gumroad import GumroadMarketplaceEngine
from acquisition.lemonsqueezy import LemonSqueezyMarketplaceEngine
from acquisition.discovery import DeveloperDiscoveryEngine
from acquisition.seo_content import SEOContentEngine
from acquisition.attribution import AttributionEngine
from acquisition.funnel import MultiChannelFunnelEngine
from acquisition.expansion import ProductExpansionQueue
from acquisition.owner_actions import OwnerActionCenter
from acquisition.automation import AcquisitionAutomationEngine
from server.app import app


class TestPhase5HAcquisition(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def test_01_channel_registry_initialization(self):
        """Test 1: Channel registry contains all 9 required channels with required schema fields."""
        channels = ChannelRegistry.get_all_channels()
        self.assertGreaterEqual(len(channels), 9)

        channel_names = [c["channel_name"] for c in channels]
        required_channels = [
            "Etsy", "Gumroad", "Lemon Squeezy", "GitHub", 
            "Reddit", "Hacker News", "Product Hunt", "Google/SEO", 
            "Nexora AI Labs website"
        ]
        for rc in required_channels:
            self.assertIn(rc, channel_names)

        # Check required fields on every channel
        required_fields = [
            "channel_name", "channel_type", "url", "audience", "product_fit",
            "account_status", "listing_status", "publication_method", "approval_required",
            "traffic_tracking", "sales_tracking", "revenue_tracking", "policy_status",
            "last_checked", "next_action"
        ]
        for c in channels:
            for field in required_fields:
                self.assertIn(field, c, f"Missing field '{field}' in channel '{c['channel_name']}'")

    def test_02_etsy_compliance_audit(self):
        """Test 2: Etsy audit returns NOT_RECOMMENDED_FOR_THIS_PRODUCT with documented evidence."""
        audit = EtsyMarketplaceEngine.audit_compliance()
        self.assertEqual(audit["etsy_status"], "NOT_RECOMMENDED_FOR_THIS_PRODUCT")
        self.assertFalse(audit["compliant_for_marketplace"])
        self.assertIn("misaligned", audit["documented_reason"].lower())

        # Check fallback compliant listing package exists
        pkg = audit["listing_package"]
        self.assertIn("Local LLM", pkg["title"])
        self.assertEqual(pkg["pricing"]["amount"], 29.0)
        self.assertIn("disclosure_requirements", pkg)
        self.assertIn("buyer_instructions", pkg)

    def test_03_gumroad_integration_state(self):
        """Test 3: Gumroad channel specification and verified transaction requirement."""
        pkg = GumroadMarketplaceEngine.get_listing_package()
        self.assertIn("Local LLM Offline Evaluation", pkg["title"])
        self.assertEqual(pkg["pricing"]["price_usd"], 29.0)
        self.assertIn("30-day", pkg["refund_guarantee"].lower())
        self.assertIn("Nexora AI Labs", pkg["branding"]["brand_name"])

        # Check fake transaction rejection rule
        status = GumroadMarketplaceEngine.get_channel_status()
        self.assertTrue(status["strict_revenue_verification"])
        self.assertEqual(status["verified_sales_count"], 0)
        self.assertEqual(status["verified_net_revenue"], 0.0)

    def test_04_lemonsqueezy_integration_state(self):
        """Test 4: Lemon Squeezy integration state requires owner KYC action."""
        status = LemonSqueezyMarketplaceEngine.get_channel_status()
        self.assertEqual(status["role"], "Merchant of Record (MoR)")
        self.assertFalse(status["activation_status"]["kyc_completed"])
        self.assertTrue(status["activation_status"]["owner_action_required"])

        # Verify owner action item exists in registry
        actions = OwnerActionCenter.get_pending_actions()
        action_ids = [a["action_id"] for a in actions]
        self.assertIn("ACT-002-LEMONSQUEEZY-KYC", action_ids)

    def test_05_developer_discovery_and_anti_spam(self):
        """Test 5: Developer discovery discovers real problem discussions and enforces anti-spam gates."""
        DeveloperDiscoveryEngine.run_discovery_scan()
        opps = DeveloperDiscoveryEngine.get_opportunities()
        self.assertGreaterEqual(len(opps), 3)

        # Check fields
        first = opps[0]
        self.assertIn("source", first)
        self.assertIn("customer_problem", first)
        self.assertIn("recommended_response", first)
        self.assertIn("approval_status", first)

        # Verify educational, not spammy
        self.assertTrue("autonomous-ai-company" in first["recommended_response"] or "Nexora" in first["recommended_response"])
        self.assertTrue(
            "regression" in first["recommended_response"].lower() or 
            "benchmark" in first["recommended_response"].lower() or
            "schema" in first["recommended_response"].lower()
        )

        # Test approval and rejection gates
        test_id = first["opportunity_id"]
        approved = DeveloperDiscoveryEngine.approve_opportunity(test_id)
        self.assertEqual(approved["approval_status"], "APPROVED")

        rejected = DeveloperDiscoveryEngine.reject_opportunity(test_id)
        self.assertEqual(rejected["approval_status"], "REJECTED")

    def test_06_seo_content_workflow_and_metadata(self):
        """Test 6: SEO Content Engine contains all 9 required topics and enforces review workflow."""
        articles = SEOContentEngine.get_all_articles()
        self.assertEqual(len(articles), 9)

        slugs = [a["slug"] for a in articles]
        required_slugs = [
            "how-to-test-local-llm-upgrades",
            "how-to-detect-prompt-regressions",
            "ollama-regression-testing",
            "vllm-evaluation-guide",
            "llama-cpp-benchmark-testing",
            "json-schema-regression-testing-local-llms",
            "local-llm-latency-benchmarking",
            "how-to-build-a-deterministic-llm-regression-suite",
            "local-llm-evaluation-without-cloud-apis"
        ]
        for rs in required_slugs:
            self.assertIn(rs, slugs)

        # Test article approval
        approved_art = SEOContentEngine.approve_article("ART-001-LOCAL-LLM-UPGRADES")
        self.assertEqual(approved_art["new_status"], "PUBLISHED")

    def test_07_source_attribution_and_utm_tracking(self):
        """Test 7: UTM tracking captures touchpoint, links to checkout session, payment, and fulfillment."""
        # Record touchpoint
        tp = AttributionEngine.record_touchpoint(
            source="reddit",
            medium="community",
            campaign="llm_regression",
            content="post_001",
            landing_path="/store",
            client_ip="127.0.0.1"
        )
        self.assertIsNotNone(tp["touchpoint_id"])
        self.assertEqual(tp["utm_source"], "reddit")

        # Link checkout session
        cs_id = "cs_test_phase5h_attr"
        linked_cs = AttributionEngine.link_checkout_session(tp["touchpoint_id"], cs_id)
        self.assertEqual(linked_cs["checkout_session_id"], cs_id)

        # Link order payment and fulfillment
        order_id = "ORD-PHASE5H-001"
        payment_ref = "ch_test_phase5h_payment"
        linked_pay = AttributionEngine.link_order_payment(
            checkout_session_id=cs_id,
            order_id=order_id,
            payment_reference=payment_ref,
            amount_usd=29.0,
            channel="Reddit"
        )
        self.assertIsNotNone(linked_pay)
        self.assertEqual(linked_pay["order_id"], order_id)
        self.assertEqual(linked_pay["fulfillment_status"], "FULFILLED")

    def test_08_channel_performance_truth_and_mode_separation(self):
        """Test 8: Channel performance respects production separation and strict 0 / N/A / Unknown rules."""
        for mode in ["PRODUCTION", "TEST", "SANDBOX"]:
            perf = ChannelRegistry.get_channel_performance(mode=mode)
            self.assertEqual(perf["mode"], mode)
            self.assertGreaterEqual(len(perf["channels"]), 9)

            for c in perf["channels"]:
                # Visitors must be numeric string or 'Unknown' or 'N/A'
                self.assertTrue(
                    isinstance(c["visitors"], int) or 
                    c["visitors"] in ["Unknown", "N/A"] or 
                    str(c["visitors"]).isdigit()
                )
                # Revenue must have 'USD', 'N/A', or 'Unknown'
                self.assertTrue(
                    "USD" in str(c["revenue"]) or 
                    c["revenue"] in ["N/A", "Unknown"]
                )

    def test_09_seven_stage_funnel_tracking(self):
        """Test 9: 7-Stage Business Conversion Funnel computes stages and diagnostic insights."""
        funnel = MultiChannelFunnelEngine.get_funnel_metrics(mode="PRODUCTION")
        stages = [s["stage"] for s in funnel["stages"]]
        expected_stages = [
            "DISCOVERY", "VISIT", "PRODUCT_VIEW", 
            "CHECKOUT", "PAYMENT", "CUSTOMER", "FULFILLMENT"
        ]
        self.assertEqual(stages, expected_stages)
        self.assertIn("funnel_insight", funnel)

    def test_10_product_expansion_queue(self):
        """Test 10: Product expansion queue ranks opportunities by documented evidence."""
        queue = ProductExpansionQueue.get_ranked_queue()
        self.assertGreaterEqual(len(queue), 5)

        # Check ranking order
        ranks = [q["rank"] for q in queue]
        self.assertEqual(ranks, sorted(ranks))

        # Check fields
        top = queue[0]
        self.assertIn("product_family", top)
        self.assertIn("observed_problem", top)
        self.assertIn("search_demand", top)
        self.assertIn("composite_score", top)
        self.assertIn("approval_status", top)

    def test_11_owner_action_center(self):
        """Test 11: Owner action center registers required actions without faking completion."""
        all_actions = OwnerActionCenter.list_actions()
        self.assertGreaterEqual(len(all_actions), 4)

        # Check required high-priority actions
        titles = [a["title"] for a in all_actions]
        self.assertTrue(any("Gumroad" in t for t in titles))
        self.assertTrue(any("Lemon Squeezy" in t for t in titles))
        self.assertTrue(any("Reddit" in t for t in titles))

        # Test marking action completed
        actions = OwnerActionCenter.get_pending_actions()
        if actions:
            first = actions[0]
            updated = OwnerActionCenter.complete_action(first["action_id"])
            self.assertEqual(updated["status"], "COMPLETED")

    def test_12_acquisition_automation_cycles(self):
        """Test 12: Acquisition automation engine runs hourly, 4-hour, and daily background cycles."""
        hourly = AcquisitionAutomationEngine.run_hourly_cycle()
        self.assertEqual(hourly["cycle"], "hourly")
        self.assertTrue(hourly["metrics_updated"])

        four_hour = AcquisitionAutomationEngine.run_four_hour_cycle()
        self.assertEqual(four_hour["cycle"], "every_4_hours")
        self.assertTrue(four_hour["opportunities_analyzed"])

        daily = AcquisitionAutomationEngine.run_daily_cycle()
        self.assertEqual(daily["cycle"], "daily")
        self.assertIn("revenue_analysis", daily)
        self.assertIn("acquisition_bottleneck", daily)

    def test_13_api_endpoints(self):
        """Test 13: All acquisition API endpoints respond properly via TestClient."""
        # 1. Channels
        resp = self.client.get("/api/acquisition/channels")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("channels", resp.json())

        # 2. Performance
        resp = self.client.get("/api/acquisition/performance?mode=PRODUCTION")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["mode"], "PRODUCTION")

        # 3. Funnel
        resp = self.client.get("/api/acquisition/funnel?mode=PRODUCTION")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["stages"]), 7)

        # 4. Marketplaces
        resp = self.client.get("/api/acquisition/etsy")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["etsy_status"], "NOT_RECOMMENDED_FOR_THIS_PRODUCT")

        resp = self.client.get("/api/acquisition/gumroad")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["pricing"]["price_usd"], 29.0)

        resp = self.client.get("/api/acquisition/lemonsqueezy")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["role"], "Merchant of Record (MoR)")

        # 5. Opportunities
        resp = self.client.get("/api/acquisition/opportunities")
        self.assertEqual(resp.status_code, 200)
        self.assertGreater(len(resp.json()["opportunities"]), 0)

        # 6. SEO Content
        resp = self.client.get("/api/acquisition/content")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["articles"]), 9)

        # 7. Owner actions
        resp = self.client.get("/api/acquisition/owner-actions")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("actions", resp.json())

        # 8. Expansion
        resp = self.client.get("/api/acquisition/expansion")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("queue", resp.json())


if __name__ == "__main__":
    unittest.main()
