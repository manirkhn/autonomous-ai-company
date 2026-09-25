"""
Phase 5A Automated Tests: AI Virtual Office & Employee Desk Experience.
Tests grounded employee state aggregation, financial truth separation,
security invariants, and office API endpoints.
"""

import unittest
from fastapi.testclient import TestClient

from server.app import app
from server.office import OfficeStateEngine, SAFE_GLOSSARY
from agents.registry import EmployeeRegistry
from tasks.engine import TaskEngine
from core.firewall import FinancialFirewall
from revenue.ledger import RevenueLedgerEngine

class TestPhase5AVirtualOffice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_office_state_api_structure(self):
        """Verify GET /api/office/state returns complete grounded structure."""
        res = self.client.get("/api/office/state")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Required root keys
        self.assertIn("company_status", data)
        self.assertIn("financials", data)
        self.assertIn("today", data)
        self.assertIn("next_actions", data)
        self.assertIn("ceo_focus", data)
        self.assertIn("departments", data)
        self.assertIn("employees", data)
        self.assertIn("handoffs", data)
        self.assertIn("glossary", data)

    def test_02_all_registered_employees_present_and_no_fake_employees(self):
        """Verify only registered agents appear, matching the database registry."""
        res = self.client.get("/api/office/state")
        data = res.json()
        employees = data["employees"]
        emp_ids = [e["employee_id"] for e in employees]

        # All 12 core founding agents must be present
        core_12 = [
            "EMP-001-CEO", "EMP-002-RESEARCH", "EMP-003-PM", "EMP-004-CREATION",
            "EMP-005-MARKETING", "EMP-006-SALES", "EMP-007-SUPPORT", "EMP-008-OPS",
            "EMP-009-FINANCE", "EMP-010-COMPLIANCE", "EMP-011-QA", "EMP-012-AUTOMATION"
        ]
        for core_id in core_12:
            self.assertIn(core_id, emp_ids, f"Core agent {core_id} must be present in Virtual Office.")

        # Ensure no arbitrary fabricated employee ID exists
        self.assertNotIn("EMP-FAKE-001", emp_ids)
        self.assertNotIn("EMP-UNREGISTERED", emp_ids)

    def test_03_status_determination_derived_from_actual_tasks(self):
        """Verify employee working/waiting/blocked status strictly reflects task state."""
        res = self.client.get("/api/office/state")
        data = res.json()
        emp_map = {e["employee_id"]: e for e in data["employees"]}

        # EMP-004-CREATION has an active IN_PROGRESS task in DB -> must be WORKING
        creation_emp = emp_map.get("EMP-004-CREATION")
        self.assertIsNotNone(creation_emp)
        self.assertEqual(creation_emp["status"], "WORKING")
        self.assertEqual(creation_emp["status_label"], "Working")

        # EMP-005-MARKETING has an APPROVAL_REQUIRED task in DB -> must be BLOCKED
        mkt_emp = emp_map.get("EMP-005-MARKETING")
        self.assertIsNotNone(mkt_emp)
        self.assertEqual(mkt_emp["status"], "BLOCKED")
        self.assertEqual(mkt_emp["status_label"], "Waiting for your approval")

        # Idle agents without active tasks -> must be WAITING
        ceo_emp = emp_map.get("EMP-001-CEO")
        self.assertIsNotNone(ceo_emp)
        self.assertEqual(ceo_emp["status"], "WAITING")
        self.assertEqual(ceo_emp["status_label"], "Waiting for work")

    def test_04_financial_truth_separation_in_office(self):
        """Verify verified real cash is strictly segregated from estimates and treasury."""
        res = self.client.get("/api/office/state")
        data = res.json()
        finances = data["financials"]

        # Verified cash must be exactly $29.00
        self.assertEqual(finances["verified_real_revenue"], 29.0)
        self.assertEqual(finances["real_profit"], 29.0)
        self.assertEqual(finances["real_expenses"], 0.0)
        self.assertEqual(finances["verified_customers"], 1)

        # Breakdown categories must be distinctly separated
        breakdown = finances["breakdown"]
        self.assertEqual(breakdown["verified_real"], 29.0)
        self.assertEqual(breakdown["pending"], 0.0)
        self.assertEqual(breakdown["estimated"], 0.0)
        self.assertEqual(breakdown["virtual_treasury"], 500.0)
        self.assertEqual(breakdown["test_simulation"], 0.0)

    def test_05_ceo_focus_spotlight_populated_with_facts(self):
        """Verify CEO view displays real objective, decision, priority, and bottleneck."""
        res = self.client.get("/api/office/state")
        data = res.json()
        ceo = data["ceo_focus"]

        self.assertEqual(ceo["name"], "Marcus Vance")
        self.assertIn("Convert qualified developer traffic", ceo["current_objective"])
        self.assertIn("Local LLM Offline Benchmark Suite", ceo["current_decision"])
        self.assertIn("First Customer Revenue Validation", ceo["company_priority"])

    def test_06_departments_floor_plan_structure(self):
        """Verify 10 departments exist with workstations correctly routed."""
        res = self.client.get("/api/office/state")
        data = res.json()
        depts = data["departments"]
        self.assertEqual(len(depts), 10)

        dept_ids = [d["id"] for d in depts]
        expected_depts = [
            "ceo-office", "research-desk", "product-desk", "engineering-desk",
            "marketing-desk", "sales-desk", "customer-desk", "finance-desk",
            "operations-desk", "strategy-desk"
        ]
        for exp in expected_depts:
            self.assertIn(exp, dept_ids)

    def test_07_employee_detail_endpoint(self):
        """Verify GET /api/office/employees/{employee_id} returns workstation detail."""
        res = self.client.get("/api/office/employees/EMP-004-CREATION")
        self.assertEqual(res.status_code, 200)
        detail = res.json()

        self.assertEqual(detail["employee_id"], "EMP-004-CREATION")
        self.assertEqual(detail["name"], "Devon Miller")
        self.assertIn("current_work", detail)
        self.assertIn("recent_work", detail)
        self.assertIn("performance", detail)
        self.assertIn("permissions", detail)
        self.assertIn("technical_details", detail)

        # Check human-readable permission constraints
        cannot = detail["permissions"]["cannot"]
        self.assertTrue(any("banking" in c.lower() for c in cannot))
        self.assertTrue(any("withdraw" in c.lower() or "transfer" in c.lower() for c in cannot))
        self.assertTrue(any("$0.00" in c for c in cannot))

    def test_08_employee_detail_nonexistent_returns_404(self):
        """Verify query for nonexistent employee properly returns 404."""
        res = self.client.get("/api/office/employees/EMP-NONEXISTENT-999")
        self.assertEqual(res.status_code, 404)

    def test_09_glossary_endpoint_returns_safe_definitions(self):
        """Verify GET /api/office/glossary returns accurate, safe explanations."""
        res = self.client.get("/api/office/glossary")
        self.assertEqual(res.status_code, 200)
        glossary = res.json()

        self.assertIn("qualification", glossary)
        self.assertIn("financial_firewall", glossary)
        self.assertIn("banking_air_gap", glossary)
        self.assertIn("verified_revenue", glossary)
        self.assertIn("emergency_stop", glossary)

        # Check content accuracy
        self.assertIn("$0.00", glossary["financial_firewall"])
        self.assertIn("zero access to bank accounts", glossary["banking_air_gap"])

    def test_10_security_firewall_and_emergency_stop_intact(self):
        """Verify financial firewall remains enforced ($0 spend ceiling) and killswitch functional."""
        settings = FinancialFirewall.get_settings()
        self.assertEqual(settings["max_single_expense"], 0.0)
        self.assertEqual(settings["max_daily_expense"], 0.0)

        # Toggle emergency stop on and off to verify it updates company_status
        FinancialFirewall.set_emergency_stop(True, "Phase 5A test pause")
        state_paused = OfficeStateEngine.get_office_state()
        self.assertFalse(state_paused["company_status"]["is_running"])
        self.assertIn("PAUSED", state_paused["company_status"]["status_text"])

        # Resume
        FinancialFirewall.set_emergency_stop(False, "Phase 5A test resume")
        state_running = OfficeStateEngine.get_office_state()
        self.assertTrue(state_running["company_status"]["is_running"])
        self.assertEqual(state_running["company_status"]["status_text"], "Company Running")

if __name__ == "__main__":
    unittest.main()
