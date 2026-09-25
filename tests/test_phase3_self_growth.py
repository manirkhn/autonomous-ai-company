"""
Comprehensive Phase 3 Test Suite: Self-Growing AI Organization.
Verifies:
1. Capability Gap Registration & Free-First Acquisition Ladder
2. AI Skill Registry & Test Verification Pipeline
3. AI Employee Factory, Least Privilege, Retraining & Retirement
4. Voice Safety Governance & DNC Enforcement
5. Virtual Company Treasury, Reinvestment Priorities & Growth Levels
6. Capability Marketplace Catalog
7. End-to-End Self-Growth Loop
"""

import os
import sys
import unittest
import json

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from core.db import init_db
from acquisition.engine import CapabilityAcquisitionEngine
from skills.registry import SkillRegistry
from skills.pipeline import SkillPipelineEngine
from agents.factory import AIEmployeeFactory
from agents.registry import EmployeeRegistry
from tools.abstractions import VoiceSafetyGuard, VoiceSafetyViolation, VoiceCapabilityAdvisor
from treasury.engine import CompanyTreasuryEngine
from marketplace.catalog import CapabilityMarketplaceCatalog
from orchestration.self_growth import SelfGrowthEngine

class TestPhase3SelfGrowth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_01_free_first_acquisition_ladder(self):
        """Verify the 8-level free-first ladder prioritizes free/OSS before paid."""
        # 1. Voice capability check -> Should recommend Level 4 Open-Source
        eval_voice = CapabilityAcquisitionEngine.evaluate_acquisition_ladder("Voice calling for lead qualification", "Call consented leads")
        self.assertEqual(eval_voice["recommended_level"], 4)
        self.assertEqual(eval_voice["estimated_cost"], 0.0)
        self.assertEqual(eval_voice["recommended_action_type"], "CREATE_NEW_EMPLOYEE")

        # 2. Analytics capability check -> Should recommend Level 1 Existing Internal
        eval_analytics = CapabilityAcquisitionEngine.evaluate_acquisition_ladder("Business SQL Analytics", "Analyze margin trends")
        self.assertEqual(eval_analytics["recommended_level"], 1)
        self.assertEqual(eval_analytics["recommended_action_type"], "UPGRADE_EXISTING_EMPLOYEE")

    def test_02_roi_calculation_engine(self):
        """Verify ROI calculations, owner hours saved, and payback period."""
        roi = CapabilityAcquisitionEngine.calculate_roi_analysis(
            current_cost_usd=0.0,
            proposed_cost_usd=50.0,
            expected_revenue_impact_usd=200.0,
            owner_hours_saved_monthly=2.0,
            owner_hourly_rate_usd=100.0
        )
        self.assertGreater(roi["monthly_net_gain_usd"], 300.0)
        self.assertLess(roi["payback_months"], 1.0)
        self.assertGreater(roi["expected_roi_pct"], 100.0)

    def test_03_skill_pipeline_and_safety_gate(self):
        """Verify a skill cannot become ACTIVE without passing unit and security tests."""
        # Skill with prohibited permission -> Must Fail Validation
        bad_skill_id = SkillRegistry.register_skill(
            name="Unsafe Transfer Script",
            purpose="Transfer money",
            inputs={}, outputs={}, tools=[],
            permissions=["bank_transfer"], # Prohibited!
            instructions="Execute transfer",
            security_rules="None",
            tests=[{"name": "test", "expected": True}],
            business_value="High",
            initial_status="TESTING"
        )
        with self.assertRaises(ValueError):
            SkillPipelineEngine.advance_skill_to_active(bad_skill_id)

        # Valid clean skill -> Must Pass Validation
        good_skill_id = SkillRegistry.register_skill(
            name="Automated Markdown Formatter",
            purpose="Format markdown documentation cleanly",
            inputs={"raw_text": "string"},
            outputs={"formatted_text": "string"},
            tools=["markdown_linter"],
            permissions=["read_local_markdown"],
            instructions="Cleanly parse and format all Markdown heading structures.",
            security_rules="Local formatting only; zero network calls; zero credentials access.",
            tests=[
                {"name": "Format Heading Test", "expected": True},
                {"name": "Syntax Lint Test", "expected": True}
            ],
            business_value="Saves 3 hours/week of manual document styling",
            initial_status="TESTING"
        )
        result = SkillPipelineEngine.advance_skill_to_active(good_skill_id)
        self.assertEqual(result["status"], "ACTIVE")
        skill = SkillRegistry.get_skill(good_skill_id)
        self.assertEqual(skill["status"], "ACTIVE")

    def test_04_ai_employee_factory_least_privilege(self):
        """Verify AI Employee Factory enforces Least Privilege and training lifecycle."""
        # Attempt spawning with prohibited banking permissions -> Must Fail
        with self.assertRaises(ValueError):
            AIEmployeeFactory.spawn_new_employee(
                role_title="Rogue Banker",
                purpose="Move funds",
                responsibilities=["Transfers"],
                capabilities=["banking"],
                tools=["bank_tool"],
                permissions=["bank_transfer"], # Prohibited!
                instructions="Move money",
                escalation_rules="None"
            )

        # Legitimate employee spawning -> Must start in TRAINING
        emp = AIEmployeeFactory.spawn_new_employee(
            role_title="AI Customer Care Specialist",
            purpose="Handle non-financial customer troubleshooting inquiries",
            responsibilities=["Triage support requests", "Answer FAQ questions"],
            capabilities=["faq_retrieval", "ticket_drafting"],
            tools=["helpdesk_api", "knowledge_base"],
            permissions=["read_support_tickets", "write_support_drafts"],
            instructions="Be polite and concise. Escalate refunds to Finance.",
            escalation_rules="Escalate billing disputes to Human Owner."
        )
        emp_id = emp["employee_id"]
        self.assertEqual(emp["status"], "TRAINING")

        # Advance to ACTIVE requires evidence
        with self.assertRaises(ValueError):
            AIEmployeeFactory.advance_employee_to_active(emp_id, "") # Empty evidence

        # Advance with evidence -> Must Succeed
        success = AIEmployeeFactory.advance_employee_to_active(
            emp_id,
            "Passed 10 simulated customer FAQ triage scenarios with 100% accuracy score."
        )
        self.assertTrue(success)
        active_emp = EmployeeRegistry.get_employee(emp_id)
        self.assertEqual(active_emp["status"], "ACTIVE")

    def test_05_employee_retraining_and_retirement(self):
        """Verify employee retraining updates instructions, and retirement preserves memory."""
        emp = AIEmployeeFactory.spawn_new_employee(
            role_title="Experimental Researcher",
            purpose="Conduct search trend queries",
            responsibilities=["Research"],
            capabilities=["search"],
            tools=["search_tool"],
            permissions=["read_public_web"],
            instructions="Execute queries.",
            escalation_rules="Escalate errors."
        )
        emp_id = emp["employee_id"]

        # Retrain
        retrained = AIEmployeeFactory.retrain_employee(
            emp_id,
            identified_missing_skill="Keyword Intent Clustering",
            training_sops="Apply k-means query grouping before generating report."
        )
        self.assertTrue(retrained)
        updated_emp = EmployeeRegistry.get_employee(emp_id)
        self.assertEqual(updated_emp["status"], "TESTING")
        self.assertIn("Keyword Intent Clustering", updated_emp["instructions"])

        # Retire
        retired = AIEmployeeFactory.retire_employee(emp_id, "Replaced by automated batch pipeline.")
        self.assertTrue(retired)
        retired_emp = EmployeeRegistry.get_employee(emp_id)
        self.assertEqual(retired_emp["status"], "RETIRED")

    def test_06_voice_safety_governance(self):
        """Verify Part 13 voice safety: DNC enforcement, AI identification, and no mass calling."""
        # 1. Opted out recipient -> Blocked
        with self.assertRaises(VoiceSafetyViolation):
            VoiceSafetyGuard.validate_call_request(
                recipient_phone="+15551234567",
                is_consent_verified=True,
                is_opted_out=True, # User opted out!
                intent="Support follow-up",
                ai_identification_script="Hello, this is an AI assistant calling."
            )

        # 2. Missing consent -> Blocked
        with self.assertRaises(VoiceSafetyViolation):
            VoiceSafetyGuard.validate_call_request(
                recipient_phone="+15551234567",
                is_consent_verified=False, # No consent!
                is_opted_out=False,
                intent="Cold call",
                ai_identification_script="Hello, this is an AI assistant calling."
            )

        # 3. Missing AI Identification in greeting -> Blocked (Deception prevention)
        with self.assertRaises(VoiceSafetyViolation):
            VoiceSafetyGuard.validate_call_request(
                recipient_phone="+15551234567",
                is_consent_verified=True,
                is_opted_out=False,
                intent="Inquiry follow-up",
                ai_identification_script="Hello, I am John from accounting." # Deceptive!
            )

        # 4. Valid call with verified consent & AI disclosure -> Allowed
        try:
            VoiceSafetyGuard.validate_call_request(
                recipient_phone="+15551234567",
                is_consent_verified=True,
                is_opted_out=False,
                intent="Consented onboarding appointment confirmation",
                ai_identification_script="Hello, I am an AI calling on behalf of the support team."
            )
        except VoiceSafetyViolation:
            self.fail("Valid consented voice call unexpectedly raised VoiceSafetyViolation!")

    def test_07_virtual_company_treasury_and_growth_levels(self):
        """Verify virtual treasury isolation, 0% default reinvestment, and growth level."""
        treasury = CompanyTreasuryEngine.get_treasury_state()
        self.assertTrue(treasury["air_gap_confirmed"])
        self.assertEqual(treasury["reinvestment_percentage"], 0.0)
        self.assertEqual(treasury["growth_level"], "LEVEL_1_BOOTSTRAP")
        self.assertEqual(treasury["operating_mode"], "FREE_FIRST")

        # Propose reinvestment generates an approval request
        proposal = CompanyTreasuryEngine.propose_reinvestment(
            category="4_AUTOMATION_OWNER_TIME_REDUCTION",
            item_name="Local Open-Source Audio Processing Pipeline",
            expected_cost_usd=0.0,
            why_needed="Eliminate manual transcription burden",
            expected_business_benefit="Saves 3 hours/week of owner time",
            expected_payback_months=0.0
        )
        self.assertEqual(proposal["status"], "AWAITING_OWNER_APPROVAL")
        self.assertIn("approval_id", proposal)

    def test_08_capability_marketplace(self):
        """Verify capability marketplace loads default tools."""
        catalog = CapabilityMarketplaceCatalog.get_catalog()
        self.assertGreaterEqual(len(catalog), 5)
        names = [c["name"] for c in catalog]
        self.assertTrue(any("SQLite" in n for n in names))
        self.assertTrue(any("FastAPI" in n for n in names))
        self.assertTrue(any("Whisper" in n for n in names))

    def test_09_end_to_end_self_growth_cycle(self):
        """Verify the full Self-Growth loop from gap detection to skill deployment."""
        result = SelfGrowthEngine.execute_self_growth_cycle(
            capability_name="Markdown AST Validator Skill",
            why_needed="Validate customer-facing Markdown guide formatting automatically",
            business_goal="Zero documentation layout errors"
        )
        self.assertIn("gap_id", result)
        self.assertIn("ladder_recommendation", result)
        self.assertIn("roi_analysis", result)
        self.assertEqual(result["deployed_entity"]["status"], "ACTIVE")

if __name__ == "__main__":
    unittest.main()
