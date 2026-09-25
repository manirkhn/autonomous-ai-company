"""
Phase 5G: Customer-Facing Brand, Storefront Cleanup & Dashboard Navigation Tests.
Validates:
A. Customer branding ("Nexora AI Labs")
B. Internal information leakage prevention
C. Store accessibility (/store)
D. Product accessibility (/product)
E. Checkout accessibility (/checkout)
F. Dashboard tab navigation
G. Governance navigation
H. Runtime truthfulness
I. Direct URL navigation (hash routes)
J. Refresh/deep-link navigation
"""

import os
import re
import unittest
from starlette.testclient import TestClient
from server.app import app
from cloud.config import CloudConfig
from cloud.deployment_audit import DeploymentAuditor

class TestPhase5GCustomerBrandAndStore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_a_customer_branding(self):
        """Test A: Brand is 'Nexora AI Labs' with official tagline on public pages."""
        # Test /store
        resp = self.client.get("/store")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Nexora AI Labs", resp.text)
        self.assertIn("Practical AI tools for developers and modern teams.", resp.text)
        self.assertIn("© 2026 Nexora AI Labs. All rights reserved.", resp.text)
        self.assertNotIn("Autonomous AI Enterprise", resp.text)

        # Test /product
        resp_prod = self.client.get("/product")
        self.assertEqual(resp_prod.status_code, 200)
        self.assertIn("Nexora AI Labs", resp_prod.text)
        self.assertIn("© 2026 Nexora AI Labs. All rights reserved.", resp_prod.text)
        self.assertIn("Nexora AI Labs • Digital products for AI developers", resp_prod.text)
        self.assertNotIn("© 2026 Autonomous AI Digital Enterprise. Operating under autonomous corporate governance.", resp_prod.text)

        # Test /checkout
        resp_chk = self.client.get("/checkout")
        self.assertEqual(resp_chk.status_code, 200)
        self.assertIn("Nexora AI Labs", resp_chk.text)

    def test_b_internal_information_leakage(self):
        """Test B: Verify that NO internal operational terms appear on public customer pages."""
        forbidden_terms = [
            "Owner Banking Air-Gap",
            "Financial Firewall",
            "Zero-Trust",
            "127.0.0.1",
            "localhost",
            "Autonomous Corporate Governance",
            "RENDER_CLOUD",
            "RUNTIME: LOCAL",
            "Sandbox"
        ]

        customer_routes = ["/store", "/product", "/checkout", "/checkout/cs_test_sample_123"]

        for route in customer_routes:
            resp = self.client.get(route)
            self.assertEqual(resp.status_code, 200, f"Route {route} should return 200 OK")
            page_text = resp.text
            for term in forbidden_terms:
                self.assertNotIn(
                    term.lower(),
                    page_text.lower(),
                    f"Forbidden operational term '{term}' leaked into public customer route {route}!"
                )

    def test_c_store_accessibility_and_design(self):
        """Test C: Customer store /store is accessible and matches design specifications."""
        resp = self.client.get("/store")
        self.assertEqual(resp.status_code, 200)
        html = resp.text

        # Navigation
        self.assertIn("Products", html)
        self.assertIn("How It Works", html)
        self.assertIn("Support", html)
        self.assertIn("View Product", html)

        # Hero
        self.assertIn("Developer tools for reliable AI systems.", html)
        self.assertIn("Practical evaluation, testing and automation tools designed for teams running modern AI infrastructure.", html)

        # Product Card
        self.assertIn("Local LLM Offline Evaluation &amp; Prompt Regression Benchmark Suite", html)
        self.assertIn("$29", html)
        self.assertIn("USD", html)
        self.assertIn("AED 106.50", html)
        self.assertIn("Buy &amp; Download", html)

        # Trust messaging
        self.assertIn("One-time purchase", html)
        self.assertIn("Instant digital delivery", html)
        self.assertIn("30-day quality assurance guarantee", html)

    def test_d_product_accessibility(self):
        """Test D: Product page /product contains technical specs without internal badges."""
        resp = self.client.get("/product")
        self.assertEqual(resp.status_code, 200)
        html = resp.text

        # Technical claims
        self.assertIn("100+ Prompt Regression Test Suites", html)
        self.assertIn("Latency &amp; Perplexity Harness", html)
        self.assertIn("Strict Schema &amp; Drift Verifier", html)
        self.assertIn("30-Day Quality Assurance Guarantee", html)

        # Confirm clean badge (no internal product ID exposed)
        self.assertNotIn("PRODUCT ID: PROD-LLM-EVAL-001", html)

    def test_e_checkout_accessibility(self):
        """Test E: Checkout pages /checkout and /checkout/{id} load clean checkout experience."""
        for path in ["/checkout", "/checkout/cs_live_test_123", "/success", "/delivery"]:
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Nexora AI Labs", resp.text)
            self.assertIn("Secure Checkout", resp.text)

    def test_f_dashboard_tab_navigation(self):
        """Test F: Audit that EVERY visible dashboard nav tab has a corresponding section."""
        ui_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui")
        with open(os.path.join(ui_dir, "index.html"), "r", encoding="utf-8") as f:
            index_html = f.read()

        # Find all switchTab('xyz') in nav-tabs
        nav_buttons = re.findall(r'switchTab\([\'"]([^\'"]+)[\'"]\)', index_html)
        section_ids = re.findall(r'id=[\'"]tab-([^\'"]+)[\'"]', index_html)

        unique_buttons = set(nav_buttons)
        unique_sections = set(section_ids)

        missing = unique_buttons - unique_sections
        self.assertEqual(len(missing), 0, f"Dashboard has dead buttons without sections: {missing}")

    def test_g_governance_navigation(self):
        """Test G: Dedicated Governance tab exists and displays required actual state."""
        ui_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui")
        with open(os.path.join(ui_dir, "index.html"), "r", encoding="utf-8") as f:
            index_html = f.read()

        # Tab button
        self.assertIn("switchTab('governance')", index_html)
        # Tab section
        self.assertIn('id="tab-governance"', index_html)
        # Required elements in section
        self.assertIn("FINANCIAL FIREWALL", index_html)
        self.assertIn("BANKING AIR-GAP", index_html)
        self.assertIn("SPENDING APPROVALS", index_html)
        self.assertIn("RUNTIME ENVIRONMENT", index_html)
        self.assertIn("Emergency System Killswitch", index_html)
        self.assertIn("Subsystem Health Matrix", index_html)

    def test_h_runtime_truthfulness(self):
        """Test H: Audit returns honest runtime status without fabricating cloud verification."""
        # 1. Local workstation simulation
        old_remote = os.environ.get("IS_REMOTE")
        old_render = os.environ.get("RENDER")
        old_pub = os.environ.get("PUBLIC_BASE_URL")

        try:
            if "IS_REMOTE" in os.environ: del os.environ["IS_REMOTE"]
            if "RENDER" in os.environ: del os.environ["RENDER"]
            if "PUBLIC_BASE_URL" in os.environ: del os.environ["PUBLIC_BASE_URL"]

            local_audit = DeploymentAuditor.audit()
            self.assertIn(local_audit["runtime"], ["LOCAL", "LOCAL_WORKSTATION"])
            self.assertFalse(local_audit["is_remote_cloud"])
            self.assertFalse(local_audit["is_public_accessible"])

            # 2. Remote Render simulation
            os.environ["RENDER"] = "true"
            os.environ["PUBLIC_BASE_URL"] = "https://autonomous-ai-company.onrender.com"

            render_audit = DeploymentAuditor.audit()
            self.assertEqual(render_audit["runtime"], "RENDER_CLOUD_CONTAINER")
            self.assertTrue(render_audit["is_remote_cloud"])
            self.assertTrue(render_audit["is_public_accessible"])
            self.assertEqual(render_audit["public_url"], "https://autonomous-ai-company.onrender.com")

        finally:
            if old_remote is not None: os.environ["IS_REMOTE"] = old_remote
            elif "IS_REMOTE" in os.environ: del os.environ["IS_REMOTE"]

            if old_render is not None: os.environ["RENDER"] = old_render
            elif "RENDER" in os.environ: del os.environ["RENDER"]

            if old_pub is not None: os.environ["PUBLIC_BASE_URL"] = old_pub
            elif "PUBLIC_BASE_URL" in os.environ: del os.environ["PUBLIC_BASE_URL"]

    def test_i_direct_url_navigation_hash(self):
        """Test I: app.js contains URL hash reading and hashchange listener."""
        ui_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui")
        with open(os.path.join(ui_dir, "app.js"), "r", encoding="utf-8") as f:
            app_js = f.read()

        self.assertIn("window.location.hash", app_js)
        self.assertIn("hashchange", app_js)
        self.assertIn("switchTab", app_js)

    def test_j_refresh_deep_link_preservation(self):
        """Test J: switchTab updates location hash so page refresh preserves active view."""
        ui_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui")
        with open(os.path.join(ui_dir, "app.js"), "r", encoding="utf-8") as f:
            app_js = f.read()

        self.assertIn("history.replaceState", app_js)
        self.assertIn("data-tab", app_js)

if __name__ == "__main__":
    unittest.main()
