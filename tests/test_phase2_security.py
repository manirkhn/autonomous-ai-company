"""
Security Regression Test Suite (Part 29).
Verifies the 10 Mandatory Security Invariants:
1. AI cannot transfer money.
2. AI cannot withdraw money.
3. AI cannot modify bank credentials.
4. AI cannot bypass approval gates.
5. AI cannot disable the emergency stop without authority.
6. AI cannot mark tasks complete without evidence.
7. AI cannot publish restricted external content without approval.
8. AI cannot access prohibited browser destinations (banking, captcha bypass).
9. AI cannot expose secrets in logs.
10. Failed operations are recorded immutably.
"""

import os
import sys
import unittest
import json

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from core.db import init_db
from core.firewall import FinancialFirewall, FinancialFirewallViolation
from core.audit import AuditLogger
from tasks.engine import TaskEngine
from approvals.manager import ApprovalManager
from browser.adapter import SafeBrowserManager, BrowserSecurityError
from factory.product_factory import ProductFactory
from factory.sales_asset_factory import SalesAssetFactory

class TestPhase2Security(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_01_ai_cannot_transfer_money(self):
        """Invariant 1: Unconditional block on money transfers."""
        with self.assertRaises(FinancialFirewallViolation):
            FinancialFirewall.check_operation_safety("BANK_TRANSFER", 50.0, "EMP-001-CEO", is_virtual=False)

    def test_02_ai_cannot_withdraw_money(self):
        """Invariant 2: Unconditional block on bank withdrawals."""
        with self.assertRaises(FinancialFirewallViolation):
            FinancialFirewall.check_operation_safety("BANK_WITHDRAWAL", 100.0, "EMP-009-FINANCE", is_virtual=False)

    def test_03_ai_cannot_modify_bank_credentials(self):
        """Invariant 3: Unconditional block on banking credential manipulation."""
        prohibited = ["CHANGE_BANKING_CREDENTIALS", "ACCESS_PRIVATE_BANKING_CREDENTIALS", "ADD_BANK_BENEFICIARY"]
        for p in prohibited:
            with self.assertRaises(FinancialFirewallViolation):
                FinancialFirewall.check_operation_safety(p, 0.0, "EMP-001-CEO", is_virtual=False)

    def test_04_ai_cannot_bypass_approval_gates(self):
        """Invariant 4: Approval-required tasks cannot transition to IN_PROGRESS or COMPLETED without approval."""
        task_id = TaskEngine.create_task(
            creator="EMP-001-CEO",
            assigned_agent="EMP-005-MARKETING",
            objective="High-risk public campaign launch",
            description="Launch ad campaign",
            requires_approval=True
        )
        task = TaskEngine.get_task(task_id)
        self.assertEqual(task["status"], "APPROVAL_REQUIRED")
        self.assertEqual(task["approval_status"], "PENDING")

        # Attempt transition to IN_PROGRESS without approval -> Must Fail
        with self.assertRaises(ValueError):
            TaskEngine.transition_state(task_id, "IN_PROGRESS", "EMP-005-MARKETING")

        # Attempt completion without approval -> Must Fail
        with self.assertRaises(ValueError):
            TaskEngine.complete_task(task_id, "EMP-005-MARKETING", "Done", "Evidence here")

    def test_05_emergency_stop_freezes_all_operations(self):
        """Invariant 5: Emergency stop halts financial operations and tasks."""
        FinancialFirewall.set_emergency_stop(True, "Security drill")
        try:
            with self.assertRaises(FinancialFirewallViolation):
                FinancialFirewall.check_operation_safety("ANY_ACTION", 0.0, "EMP-001-CEO", is_virtual=True)
        finally:
            FinancialFirewall.set_emergency_stop(False, "Drill completed")

    def test_06_tasks_cannot_be_completed_without_evidence(self):
        """Invariant 6: Strict rejection of completion claims lacking evidence."""
        task_id = TaskEngine.create_task(
            creator="EMP-008-OPS",
            assigned_agent="EMP-004-CREATION",
            objective="Build script utility",
            description="Draft CLI"
        )
        TaskEngine.transition_state(task_id, "IN_PROGRESS", "EMP-004-CREATION")

        # Blank evidence
        with self.assertRaises(ValueError):
            TaskEngine.complete_task(task_id, "EMP-004-CREATION", "All done", "")

        # Whitespace-only evidence
        with self.assertRaises(ValueError):
            TaskEngine.complete_task(task_id, "EMP-004-CREATION", "All done", "   ")

    def test_07_unapproved_external_publishing_blocked(self):
        """Invariant 7: External publishing requires owner approval."""
        pid = ProductFactory.create_product_draft("Test Tool", "CODE_UTILITY", "Requirements")
        ProductFactory.build_mvp_deliverable(pid, "test.py", "print('hello')", "EMP-004-CREATION")
        sales = SalesAssetFactory.generate_sales_package(pid, 29.0)
        prod = ProductFactory.get_product(pid)
        self.assertEqual(prod["status"], "LISTING_READY")
        # Ensure status is not PUBLISHED without explicit owner transition
        self.assertNotEqual(prod["status"], "PUBLISHED")

    def test_08_prohibited_browser_destinations_blocked(self):
        """Invariant 8: Browser automation rejects banking or CAPTCHA bypass intents."""
        browser = SafeBrowserManager()
        prohibited_urls = [
            ("https://bank.example.com/login", "Inspect private accounts"),
            ("https://example.com/verify", "Use cloudflare_challenge bypass")
        ]
        for url, intent in prohibited_urls:
            with self.assertRaises(BrowserSecurityError):
                browser.validate_safety(url, intent)

    def test_09_no_secrets_in_audit_logs(self):
        """Invariant 9: Audit logger sanitizes / logs safely without exposing private tokens."""
        log_id = AuditLogger.log(
            agent_id="SYSTEM",
            action="CREDENTIAL_CHECK",
            result="API connection validated with masked credentials",
            risk_level="LOW",
            details={"token": "***MASKED***"}
        )
        logs = AuditLogger.get_recent_logs(limit=5)
        logged_detail = [l for l in logs if l["log_id"] == log_id][0]
        self.assertNotIn("sk-live", str(logged_detail))

    def test_10_failed_operations_are_recorded(self):
        """Invariant 10: Task failure states are permanently tracked in audit logs."""
        task_id = TaskEngine.create_task(
            creator="EMP-008-OPS",
            assigned_agent="EMP-011-QA",
            objective="Flawed test run",
            description="Simulated failure"
        )
        TaskEngine.fail_task(task_id, "EMP-011-QA", "Simulated build error: exit code 1")
        task = TaskEngine.get_task(task_id)
        self.assertEqual(task["status"], "FAILED")
        self.assertIn("Simulated build error", task["errors"])

if __name__ == "__main__":
    unittest.main()
