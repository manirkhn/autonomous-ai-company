"""
Automated Test Suite for Phase 5B — Gemini-Powered 24/7 Cloud Company + Daily CEO Report.
Validates:
1. LLM Provider abstraction & Gemini status reporting (Requirement 2, 4, 6).
2. 9-Point Heartbeat monitoring across all services (Requirement 12).
3. Section 34 Truth Check: strict validation against SQLite ledger before delivery.
4. Report archiving to markdown and JSON (Requirement 31).
5. Email Service delivery to manirkhn@gmail.com and local outbox fallback (Requirements 17, 18, 35).
6. 24/7 CloudScheduler & Dubai timezone handling (Requirement 16).
7. Employee activity tracking & context recording (Requirements 14, 15, 21, 29).
8. FastAPI /api/cloud/* endpoints.
"""

import unittest
import os
import json
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from server.app import app
from providers.llm import LLMManager, GeminiProvider, DeterministicFallbackProvider
from core.heartbeat import CompanyHeartbeat
from reporting.daily_ceo_report import DailyCEOReportGenerator, ReportTruthCheckError, TARGET_RECIPIENT
from reporting.email_service import EmailService
from cloud.scheduler import CloudScheduler
from cloud.worker import CloudWorker
from core.activity import ActivityTracker
from revenue.ledger import RevenueLedgerEngine
from core.db import get_connection

class TestPhase5BCloudAndGemini(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_llm_provider_abstraction_and_health(self):
        """Test LLM Provider abstraction, fallback behavior, and credentials sanitization."""
        status = LLMManager.get_status()
        self.assertIn("status", status)
        self.assertIn("status_text", status)
        self.assertIn("configured_model", status)
        self.assertIn("fallback_provider", status)
        self.assertIn("api_key_configured", status)
        
        # Verify no secret key is exposed in the output string
        status_str = json.dumps(status)
        self.assertNotIn("AIza", status_str) # Standard Gemini key prefix
        
        # Verify text generation fallback
        res = LLMManager.generate("Please summarize the daily executive report.")
        self.assertIn("text", res)
        self.assertTrue(len(res["text"]) > 20)
        self.assertIn("provider", res)

    def test_02_company_heartbeat_probes_nine_components(self):
        """Test that company heartbeat probes all 9 required operational components."""
        heartbeat = CompanyHeartbeat.check_heartbeat()
        self.assertIn("overall_status", heartbeat)
        self.assertIn("components", heartbeat)
        comps = heartbeat["components"]
        
        required_components = [
            "database", "revenue_system", "gemini", "task_queue",
            "cloud_server", "worker", "scheduler", "email_service", "ai_office"
        ]
        for comp in required_components:
            self.assertIn(comp, comps, f"Missing component in heartbeat: {comp}")
            self.assertIn("status", comps[comp])
            self.assertIn("label", comps[comp])

    def test_03_activity_tracker_records_genuine_context(self):
        """Test recording of employee activity without fabricating external platforms."""
        act = ActivityTracker.record_activity(
            employee_id="EMP-001-CEO",
            employee_name="Chief Executive Officer",
            role="Chief Executive Officer",
            task_id="TSK-TEST-001",
            action="Executed Daily Strategic Portfolio Evaluation",
            status="COMPLETED",
            project="OPP-P4-001",
            experiment="EXP-P4-1790269597",
            module="reporting/daily_ceo_report.py"
        )
        self.assertIsNotNone(act["activity_id"])
        self.assertEqual(act["status"], "COMPLETED")

        # Verify summary table contains this employee
        summary_table = ActivityTracker.get_employee_summary_table(timeframe="today")
        ceo_entry = next((e for e in summary_table if e["employee_id"] == "EMP-001-CEO"), None)
        self.assertIsNotNone(ceo_entry)
        self.assertTrue(ceo_entry["total_tasks"] >= 1)

    def test_04_daily_ceo_report_generation_and_truth_check(self):
        """Test report compilation and automated Section 34 truth check against SQLite ledger."""
        report = DailyCEOReportGenerator.generate_report()
        self.assertIn("report_id", report)
        self.assertEqual(report["recipient"], "manirkhn@gmail.com")
        self.assertIn("facts", report)
        
        facts = report["facts"]
        finances = facts["finances"]
        
        # Verify ledger consistency
        ledger_metrics = RevenueLedgerEngine.get_revenue_metrics()
        self.assertEqual(finances["verified_revenue_usd"], ledger_metrics["all_time"]["verified_actual_revenue"])
        self.assertEqual(finances["verified_profit_usd"], round(finances["verified_revenue_usd"] - finances["verified_expenses_usd"], 2))
        
        # Verify archives were created
        self.assertTrue(os.path.exists(report["md_path"]))
        self.assertTrue(os.path.exists(report["json_path"]))

    def test_05_truth_check_aborts_on_financial_tampering(self):
        """Test that Section 34 Truth Check strictly aborts if numbers do not match database ledger."""
        corrupted_facts = DailyCEOReportGenerator.get_ground_truth_facts()
        # Intentionally tamper with revenue to simulate hallucination or data corruption
        corrupted_facts["finances"]["verified_revenue_usd"] = 999999.00
        
        is_valid, errors = DailyCEOReportGenerator.validate_truth_check(corrupted_facts)
        self.assertFalse(is_valid)
        self.assertTrue(any("Revenue mismatch" in err for err in errors))

    def test_06_email_service_targets_exact_recipient(self):
        """Test that EmailService strictly delivers to manirkhn@gmail.com and records outbox."""
        delivery = EmailService.send_daily_report(
            report_id="RPT-TEST-001",
            subject="🏢 AI Company — Daily CEO Progress Report — Test",
            body_text="Test Content",
            recipient="manirkhn@gmail.com"
        )
        self.assertTrue(delivery.success)
        self.assertIn(delivery.status, ["DELIVERED", "QUEUED_LOCAL_OUTBOX"])
        
        # Verify outbox tracking
        deliveries = EmailService.get_recent_deliveries(limit=5)
        self.assertTrue(len(deliveries) > 0)
        self.assertEqual(deliveries[0]["recipient"], "manirkhn@gmail.com")

    def test_07_scheduler_dubai_timezone_calculation(self):
        """Test 24/7 CloudScheduler target schedule and Asia/Dubai timezone conversion."""
        scheduler = CloudScheduler.get_instance()
        status = scheduler.get_status()
        self.assertIn("Asia/Dubai", status["target_schedule"])
        self.assertIn("next_run_estimated", status)
        self.assertIn("dubai_time_current", status)

    def test_08_fastapi_cloud_endpoints(self):
        """Test all Phase 5B REST API endpoints."""
        # 1. Cloud Status
        res = self.client.get("/api/cloud/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["owner_laptop_required"])
        self.assertIn("heartbeat", data)
        self.assertIn("scheduler", data)

        # 2. Gemini Status
        res_gemini = self.client.get("/api/cloud/gemini")
        self.assertEqual(res_gemini.status_code, 200)
        self.assertIn("status", res_gemini.json())
        self.assertIn("configured_model", res_gemini.json())

        # 3. Heartbeat
        res_hb = self.client.get("/api/cloud/heartbeat")
        self.assertEqual(res_hb.status_code, 200)
        self.assertIn("overall_status", res_hb.json())

        # 4. Daily Reports List
        res_reports = self.client.get("/api/cloud/reports/daily")
        self.assertEqual(res_reports.status_code, 200)
        self.assertTrue(isinstance(res_reports.json(), list))

        # 5. Activities List
        res_acts = self.client.get("/api/cloud/activities?timeframe=today")
        self.assertEqual(res_acts.status_code, 200)

        # 6. Activities Summary Table
        res_summary = self.client.get("/api/cloud/activities/summary?timeframe=today")
        self.assertEqual(res_summary.status_code, 200)
        self.assertTrue(len(res_summary.json()) >= 12)

if __name__ == "__main__":
    unittest.main()
