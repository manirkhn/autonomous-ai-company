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
        """Test A: Brand is 'Nexora AI Labs' on all public customer-facing pages."""
        # Test /store
        resp = self.client.get("/store")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Nexora AI Labs", resp.text)
        self.assertIn("© 2026 Nexora AI Labs. Digital tools for AI developers.", resp.text)
        self.assertNotIn("Autonomous AI Enterprise", resp.text)
        self.assertNotIn("Autonomous AI Digital Enterprise", resp.text)

        # Test /product
        resp_prod = self.client.get("/product")
        self.assertEqual(resp_prod.status_code, 200)
        self.assertIn("Nexora AI Labs", resp_prod.text)
        self.assertIn("© 2026 Nexora AI Labs. Digital tools for AI developers.", resp_prod.text)
        self.assertNotIn("Autonomous AI Digital Enterprise", resp_prod.text)

        # Test /checkout
        resp_chk = self.client.get("/checkout")
        self.assertEqual(resp_chk.status_code, 200)
        self.assertIn("Nexora AI Labs", resp_chk.text)
        self.assertIn("© 2026 Nexora AI Labs. Digital tools for AI developers.", resp_chk.text)

    def test_b_internal_information_leakage(self):
        """Test B: Verify that NO internal operational or governance terms appear on public customer pages."""
        forbidden_terms = [
            "OFFLINE LOCAL LLM TOOLING",
            "PROD-LLM-EVAL-001",
            "Autonomous AI Digital Enterprise",
            "Autonomous AI Enterprise",
            "autonomous corporate governance",
            "Owner Banking Air-Gap",
            "Zero-Trust",
            "Financial Firewall",
            "127.0.0.1",
            "localhost",
            "RENDER_CLOUD",
            "RENDER_CLOUD_CONTAINER",
            "RUNTIME: LOCAL",
            "certified payment gateway",
            "256-bit SSL encryption",
            "256-bit SSL",
            "certified regression-free"
        ]

        customer_routes = ["/store", "/product", "/checkout", "/checkout/cs_test_sample_123", "/success", "/delivery"]

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
        """Test C: Customer store /store matches required Phase 5G.1 structure and design."""
        resp = self.client.get("/store")
        self.assertEqual(resp.status_code, 200)
        html = resp.text

        # 1. Brand/header
        self.assertIn("Nexora AI Labs", html)
        # 2. Product title
        self.assertIn("Local LLM Offline Evaluation &amp; Prompt Regression Benchmark Suite", html)
        # 3. Short one-sentence value proposition
        self.assertIn("A deterministic offline benchmarking and regression testing toolkit", html)
        # 4. Price
        self.assertIn("$29", html)
        self.assertIn("USD", html)
        # 5. One-time purchase • Lifetime baseline updates
        self.assertIn("One-Time Purchase", html)
        self.assertIn("Lifetime baseline updates", html)
        # 6. Primary CTA
        self.assertIn("Buy &amp; Download — $29", html)
        # 7. Product overview
        self.assertIn("Product Overview", html)
        # 8. What is included
        self.assertIn("What Is Included", html)
        # 9. Supported environments
        self.assertIn("Ollama", html)
        self.assertIn("vLLM", html)
        self.assertIn("llama.cpp", html)
        self.assertIn("OpenAI-Compatible", html)
        # 10. How it works
        self.assertIn("How It Works", html)
        # 11. Example benchmark output explicitly labeled as example
        self.assertIn("Example Benchmark Output", html)
        self.assertIn("Example output", html)
        # 12. 30-Day Quality Assurance Guarantee
        self.assertIn("30-Day Quality Assurance Guarantee", html)
        # 13. FAQ
        self.assertIn("Frequently Asked Questions", html)
        # 14. Professional footer
        self.assertIn("© 2026 Nexora AI Labs. Digital tools for AI developers.", html)

    def test_d_product_accessibility(self):
        """Test D: Product page /product contains technical specs without internal leakage."""
        resp = self.client.get("/product")
        self.assertEqual(resp.status_code, 200)
        html = resp.text

        # Technical claims
        self.assertIn("100+ Prompt Regression Test Suites", html)
        self.assertIn("Latency &amp; Perplexity Harness", html)
        self.assertIn("Strict Schema &amp; Drift Verifier", html)
        self.assertIn("30-Day Quality Assurance Guarantee", html)

        # Confirm clean badge (no internal product ID exposed)
        self.assertNotIn("PROD-LLM-EVAL-001", html)
        self.assertNotIn("OFFLINE LOCAL LLM TOOLING", html)

    def test_e_checkout_accessibility(self):
        """Test E: Checkout pages /checkout, /success, /delivery render clean experience."""
        for path in ["/checkout", "/checkout/cs_live_test_123", "/success", "/delivery"]:
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Nexora AI Labs", resp.text)
            self.assertIn("Secure Checkout", resp.text)
            self.assertNotIn("PROD-LLM-EVAL-001", resp.text)
            self.assertNotIn("256-bit", resp.text.lower())

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

    def test_k_phase5g1_comprehensive_checklist(self):
        """Test K: Validate all 16 checklist items of Phase 5G.1."""
        # 1-5. Verify /store, /product, /checkout, /success, /delivery all return 200
        public_routes = ["/store", "/product", "/checkout", "/success", "/delivery"]
        for route in public_routes:
            res = self.client.get(route)
            self.assertEqual(res.status_code, 200, f"Route {route} did not return 200")

        # 6. 'Nexora AI Labs' appears on /store
        store_res = self.client.get("/store")
        self.assertIn("Nexora AI Labs", store_res.text)

        # 7. $29 appears on /store
        self.assertIn("$29", store_res.text)

        # 8. Buy/checkout CTA exists
        self.assertIn("Buy &amp; Download — $29", store_res.text)

        # 9. CTA points to the real checkout flow
        self.assertIn("/api/payments/checkout", store_res.text)

        # 10. Internal banking/governance terminology is absent from public routes
        # 11. localhost/127.0.0.1 is absent from public routes
        # 12. RENDER_CLOUD_CONTAINER is absent from public routes
        # 13. internal Product ID is absent from public routes
        # 14. fabricated payment certification language is absent
        # 15. internal footer text is absent
        forbidden_terms = [
            "Owner Banking Air-Gap",
            "Zero-Trust Spending Ceiling",
            "Zero-Trust",
            "Financial Firewall",
            "autonomous corporate governance",
            "Autonomous AI Digital Enterprise",
            "Autonomous AI Enterprise",
            "127.0.0.1",
            "localhost",
            "RENDER_CLOUD",
            "RENDER_CLOUD_CONTAINER",
            "PROD-LLM-EVAL-001",
            "OFFLINE LOCAL LLM TOOLING",
            "certified payment gateway",
            "256-bit SSL encryption",
            "256-bit SSL",
            "Operating under autonomous corporate governance"
        ]

        for route in public_routes:
            html = self.client.get(route).text
            for term in forbidden_terms:
                self.assertNotIn(
                    term.lower(),
                    html.lower(),
                    f"Forbidden term '{term}' leaked into public route {route}"
                )

        # 16. Example benchmark output is explicitly identified as an example
        self.assertIn("Example output", store_res.text)
        prod_res = self.client.get("/product")
        self.assertIn("Example output", prod_res.text)

if __name__ == "__main__":
    unittest.main()
