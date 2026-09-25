"""
Unit and Integration Test Suite for Autonomous AI Company Foundation.
Verifies all 20 Part requirements and strict security/financial firewall guardrails.
"""

import os
import sys
import unittest
import json
import sqlite3

# Set import path
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from core.db import init_db, get_connection
from core.firewall import FinancialFirewall, FinancialFirewallViolation
from core.audit import AuditLogger
from core.interventions import InterventionTracker
from agents.registry import EmployeeRegistry
from tasks.engine import TaskEngine
from approvals.manager import ApprovalManager
from memory.store import CorporateMemory
from discovery.engine import OpportunityDiscoveryEngine
from experiments.engine import ExperimentEngine
from finance.analytics import FinanceEngine
from reporting.ceo_report import CEOReportGenerator

class TestCompanyFoundation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        EmployeeRegistry.initialize_default_employees()

    def test_01_employees_roster(self):
        """Verify the 12 founding roles are seeded with explicit permissions."""
        employees = EmployeeRegistry.get_all_employees()
        self.assertGreaterEqual(len(employees), 12)
        
        roles = [e["role"] for e in employees]
        self.assertIn("AI CEO / Managing Director", roles)
        self.assertIn("Research & Intelligence Agent", roles)
        self.assertIn("Compliance & Risk Agent", roles)
        self.assertIn("QA Agent", roles)
        self.assertIn("Finance Analyst", roles)

        # Check permissions and escalation rules
        ceo = EmployeeRegistry.get_employee("EMP-001-CEO")
        self.assertIsNotNone(ceo)
        self.assertIn("request_approvals", ceo["permissions"])
        self.assertTrue(len(ceo["escalation_rules"]) > 0)

    def test_02_dynamic_employee_registration(self):
        """Verify system allows adding new roles dynamically without hardcoded limits."""
        new_emp_id = EmployeeRegistry.register_new_employee(
            role="Specialized Micro-SaaS Architect",
            purpose="Designs modular serverless micro-tools",
            responsibilities=["Build micro-tools"],
            capabilities=["fastapi", "sqlite"],
            tools=["code_runner"],
            permissions=["write_code"],
            instructions="Build cleanly",
            escalation_rules="Escalate on external API failures",
            initial_status="TRAINING"
        )
        emp = EmployeeRegistry.get_employee(new_emp_id)
        self.assertIsNotNone(emp)
        self.assertEqual(emp["status"], "TRAINING")

    def test_03_financial_firewall_prohibited_actions(self):
        """Verify AI is unconditionally prohibited from touching bank accounts or transferring funds."""
        prohibited = [
            "BANK_TRANSFER", "BANK_WITHDRAWAL", "ADD_BANK_BENEFICIARY",
            "CHANGE_BANKING_CREDENTIALS", "ACCESS_PRIVATE_BANKING_CREDENTIALS", "TAKE_LOAN"
        ]
        for action in prohibited:
            with self.assertRaises(FinancialFirewallViolation):
                FinancialFirewall.check_operation_safety(action, 100.0, "EMP-001-CEO", is_virtual=False)

    def test_04_financial_firewall_zero_unapproved_spend(self):
        """Verify unapproved real monetary expenditure is blocked by default."""
        is_allowed, reason = FinancialFirewall.check_operation_safety("SPEND_SOFTWARE", 25.0, "EMP-001-CEO", is_virtual=False)
        self.assertFalse(is_allowed)
        self.assertIn("APPROVAL_REQUIRED", reason)

        # Verify finance engine blocks recording unauthorized real expense
        with self.assertRaises(FinancialFirewallViolation):
            FinanceEngine.record_transaction(
                tx_type="EXPENSE",
                category="SOFTWARE",
                amount=50.0,
                description="Unapproved tool subscription",
                agent_id="EMP-012-AUTOMATION",
                is_virtual=False
            )

    def test_05_emergency_killswitch(self):
        """Verify emergency stop freezes all operations immediately."""
        FinancialFirewall.set_emergency_stop(True, "Automated test trigger")
        settings = FinancialFirewall.get_settings()
        self.assertTrue(settings["emergency_stop"])

        with self.assertRaises(FinancialFirewallViolation):
            FinancialFirewall.check_operation_safety("TEST_ACTION", 0.0, "EMP-001-CEO", is_virtual=True)

        # Deactivate kill switch for subsequent tests
        FinancialFirewall.set_emergency_stop(False, "Test completed")
        settings_after = FinancialFirewall.get_settings()
        self.assertFalse(settings_after["emergency_stop"])

    def test_06_task_evidence_requirement(self):
        """Verify tasks cannot be marked COMPLETED without verifiable evidence."""
        task_id = TaskEngine.create_task(
            creator="EMP-001-CEO",
            assigned_agent="EMP-004-CREATION",
            objective="Generate Landing Page Spec",
            description="Create complete functional spec",
            priority="HIGH"
        )
        self.assertTrue(task_id.startswith("TSK-"))

        # Transition to IN_PROGRESS
        TaskEngine.transition_state(task_id, "IN_PROGRESS", "EMP-004-CREATION")

        # Attempt complete without evidence -> Must Fail
        with self.assertRaises(ValueError):
            TaskEngine.complete_task(
                task_id=task_id,
                agent_id="EMP-004-CREATION",
                result="Done",
                evidence="" # Empty evidence!
            )

        # Complete WITH evidence -> Must Succeed
        success = TaskEngine.complete_task(
            task_id=task_id,
            agent_id="EMP-004-CREATION",
            result="Landing Page Spec written",
            evidence="Specification file at /specs/landing-page-v1.md verified by QA Agent"
        )
        self.assertTrue(success)
        task = TaskEngine.get_task(task_id)
        self.assertEqual(task["status"], "COMPLETED")

    def test_07_human_approval_workflow(self):
        """Verify full lifecycle of Human Approval Request."""
        # Create approval request
        app_id = ApprovalManager.create_approval_request(
            requesting_agent="EMP-005-MARKETING",
            what="Run $20 Google Ads Search Validation Experiment",
            why="Validate keyword intent for Notion productivity templates",
            expected_benefit="30 target leads and CTR metrics",
            expected_cost=20.0,
            risk_level="MEDIUM",
            alternatives="Organic Reddit posting or cold email",
            recommendation="Approve test run capped strictly at $20"
        )
        self.assertTrue(app_id.startswith("APP-"))

        # Check pending list
        pending = ApprovalManager.get_pending_approvals()
        pending_ids = [p["approval_id"] for p in pending]
        self.assertIn(app_id, pending_ids)

        # Owner resolves approval
        ApprovalManager.resolve_approval(app_id, "APPROVE", "Approved test up to $20.")
        
        # Verify it is no longer pending
        pending_after = ApprovalManager.get_pending_approvals()
        pending_after_ids = [p["approval_id"] for p in pending_after]
        self.assertNotIn(app_id, pending_after_ids)

    def test_08_corporate_memory_and_failure_guard(self):
        """Verify failed experiment memory prevents repeated blind retries."""
        # Store a failure
        CorporateMemory.store_memory(
            category="FAILED_APPROACH",
            title="Cold outreach scraping on LinkedIn",
            content="Accounts flagged immediately. High risk, low yield.",
            author_agent="EMP-006-SALES"
        )

        # Check past failure lookup
        failure = CorporateMemory.check_past_failure("LinkedIn")
        self.assertIsNotNone(failure)

        # Creating an experiment with that title without retry_reason must raise error
        with self.assertRaises(ValueError):
            ExperimentEngine.create_experiment(
                title="Cold outreach scraping on LinkedIn",
                hypothesis="We can bypass rate limits",
                success_metric="5 leads",
                mvp_description="Script",
                retry_reason=None # No explanation!
            )

        # With explicit retry_reason -> Succeeds
        exp_id = ExperimentEngine.create_experiment(
            title="Cold outreach scraping on LinkedIn",
            hypothesis="Using official API partnership instead of scraping",
            success_metric="5 leads",
            mvp_description="Official API webhook integration",
            retry_reason="Switching to 100% compliant official LinkedIn developer API"
        )
        self.assertTrue(exp_id.startswith("EXP-"))

    def test_09_opportunity_engine(self):
        """Verify opportunity registration and data points."""
        opp_id = OpportunityDiscoveryEngine.register_opportunity(
            customer_problem="Freelancers spend 4 hours/week preparing invoices manually",
            target_customer="Solo Consultants & Freelancers",
            proposed_solution="Lightweight automated Markdown-to-PDF invoice CLI tool",
            competitors=["Freshbooks", "Wave"],
            demand_evidence="Reddit r/freelance 45 upvotes on invoice frustration thread",
            estimated_price=19.0,
            estimated_costs=0.5,
            estimated_automation_potential=0.95,
            estimated_human_involvement=0.2,
            platform_risks="None",
            legal_compliance="Compliant open-source libraries",
            mvp_requirements="Python CLI generating professional PDF invoices",
            validation_method="Gumroad pre-order page",
            expected_time_to_test="24 hours"
        )
        self.assertTrue(opp_id.startswith("OPP-"))
        opps = OpportunityDiscoveryEngine.get_opportunities()
        self.assertGreaterEqual(len(opps), 1)

    def test_10_weekly_ceo_report_separation(self):
        """Verify CEO Report strictly separates FACTS, ESTIMATES, and AI RECOMMENDATIONS."""
        report = CEOReportGenerator.generate_weekly_report()
        self.assertIn("facts", report)
        self.assertIn("estimates", report)
        self.assertIn("recommendations", report)

        facts = report["facts"]
        self.assertIn("verified_revenue_usd", facts)
        self.assertIn("active_ai_employees_count", facts)

        estimates = report["estimates"]
        self.assertIn("estimated_gross_profit_margin_pct", estimates)
        self.assertIn("simulated_cash_available_for_reinvestment", estimates)

        recs = report["recommendations"]
        self.assertIn("strategic_initiatives_proposed", recs)
        self.assertIn("urgent_owner_decisions_required", recs)

if __name__ == "__main__":
    unittest.main()
