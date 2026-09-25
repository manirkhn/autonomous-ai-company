"""
The Self-Growth Engine & Continuous Learning Loop (Part 20 & 25).
Connects business goals to capability gaps, evaluates the free-first ladder,
calculates ROI, drafts the solution, triggers testing, and updates corporate memory.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
from core.audit import AuditLogger
from core.interventions import InterventionTracker
from memory.store import CorporateMemory
from acquisition.engine import CapabilityAcquisitionEngine
from skills.registry import SkillRegistry
from skills.pipeline import SkillPipelineEngine
from agents.factory import AIEmployeeFactory

class SelfGrowthEngine:
    @staticmethod
    def execute_self_growth_cycle(capability_name: str, why_needed: str, business_goal: str) -> Dict[str, Any]:
        """
        Part 20: Full execution of the Self-Growth Loop.
        From capability gap detection to solution proposal and sandbox testing.
        """
        steps_log = []

        # Step 1: Detect and log gap
        gap_id = CapabilityAcquisitionEngine.register_capability_gap(
            capability_name=capability_name,
            why_required=why_needed,
            business_objective=business_goal,
            detected_by="EMP-012-AUTOMATION"
        )
        steps_log.append({"step": "GAP_DETECTED", "gap_id": gap_id})

        # Step 2: Evaluate Free-First Acquisition Ladder
        ladder_eval = CapabilityAcquisitionEngine.evaluate_acquisition_ladder(capability_name, why_needed)
        steps_log.append({
            "step": "LADDER_EVALUATED",
            "recommended_level": ladder_eval["recommended_level"],
            "solution": ladder_eval["recommended_solution"]
        })

        # Step 3: Calculate ROI Analysis
        roi_analysis = CapabilityAcquisitionEngine.calculate_roi_analysis(
            current_cost_usd=0.0,
            proposed_cost_usd=ladder_eval["estimated_cost"],
            expected_revenue_impact_usd=100.0,
            owner_hours_saved_monthly=4.0
        )
        steps_log.append({
            "step": "ROI_CALCULATED",
            "expected_roi_pct": roi_analysis["expected_roi_pct"],
            "monthly_net_gain": roi_analysis["monthly_net_gain_usd"]
        })

        # Step 4: Propose & Implement Architecture based on evaluation
        action_type = ladder_eval["recommended_action_type"]
        deployed_entity = {}

        if action_type == "CREATE_NEW_EMPLOYEE":
            # Spawn new AI employee in TRAINING status
            role = ladder_eval.get("suggested_role", "AI Voice Communication Specialist")
            emp_result = AIEmployeeFactory.spawn_new_employee(
                role_title=role,
                purpose=why_needed,
                responsibilities=["Execute specialized capability", "Maintain compliance records"],
                capabilities=["voice_synthesis", "verified_calling"],
                tools=["audio_pipeline", "crm_system"],
                permissions=["read_consented_leads", "write_call_records"],
                instructions="Identify clearly as an AI. Never deceive. Respect DNC and opt-out requests instantly.",
                escalation_rules="Escalate customer disputes or legal questions to Compliance."
            )
            deployed_entity = emp_result
            steps_log.append({"step": "AI_EMPLOYEE_SPAWNED", "employee_id": emp_result["employee_id"], "status": "TRAINING"})

        else:
            # Register new skill in Skill Registry
            skill_id = SkillRegistry.register_skill(
                name=capability_name,
                purpose=why_needed,
                inputs={"query": "string"},
                outputs={"result": "object"},
                tools=["local_script_runner"],
                permissions=["read_local_data"],
                instructions=f"Execute {capability_name} in strict adherence to least privilege.",
                security_rules="No external unconsented network requests; no banking credentials.",
                tests=[
                    {"name": "Execution Sanity Test", "expected": True},
                    {"name": "Security Boundary Test", "expected": True}
                ],
                business_value=business_goal,
                initial_status="TESTING"
            )
            # Advance through validation pipeline
            adv_res = SkillPipelineEngine.advance_skill_to_active(skill_id)
            deployed_entity = adv_res
            steps_log.append({"step": "SKILL_VALIDATED_AND_DEPLOYED", "skill_id": skill_id, "status": "ACTIVE"})

        # Step 5: Commit Retrospective to Corporate Memory (Part 25)
        CorporateMemory.store_memory(
            category="LESSONS_LEARNED",
            title=f"Self-Growth Cycle: Acquired {capability_name}",
            content=f"Goal: {business_goal}\nWhy needed: {why_needed}\nLadder Evaluation: Level {ladder_eval['recommended_level']} ({ladder_eval['recommended_solution']})\nEntity: {deployed_entity}",
            author_agent="EMP-012-AUTOMATION"
        )
        steps_log.append({"step": "CORPORATE_MEMORY_UPDATED"})

        AuditLogger.log(
            agent_id="EMP-012-AUTOMATION",
            action="SELF_GROWTH_CYCLE_COMPLETED",
            result=f"Self-growth loop resolved gap '{capability_name}' via {action_type}. Zero capital required.",
            risk_level="LOW"
        )

        return {
            "gap_id": gap_id,
            "capability_name": capability_name,
            "ladder_recommendation": ladder_eval,
            "roi_analysis": roi_analysis,
            "deployed_entity": deployed_entity,
            "growth_steps": steps_log
        }
