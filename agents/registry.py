"""
AI Employee Registry & Role Governance System.
Maintains the organization of autonomous agents with explicit permissions,
escalation boundaries, cost tracking, and dynamic registration of new roles/skills.
"""

from typing import Dict, Any, List, Optional
import json
import uuid
from datetime import datetime, timezone
from core.db import get_connection
from core.audit import AuditLogger

VALID_STATUSES = {
    "ACTIVE", "PAUSED", "TRAINING", "TESTING", 
    "FAILED", "REVIEW_REQUIRED", "RETIRED"
}

# The Initial 12 Founding Roles
INITIAL_EMPLOYEES = [
    {
        "employee_id": "EMP-001-CEO",
        "role": "AI CEO / Managing Director",
        "purpose": "Coordinates the enterprise, sets strategic priorities, monitors operational flow, reviews performance, and formulates proposals for human owner approval.",
        "responsibilities": [
            "Company-wide coordination and task delegation",
            "Priority setting and resource alignment",
            "Synthesizing weekly executive reports for owner",
            "Submitting formal Human Approval Requests for high-risk actions",
            "Detecting bottlenecks across departments"
        ],
        "capabilities": ["strategy_synthesis", "task_orchestration", "approval_formulation", "bottleneck_detection"],
        "tools": ["task_manager", "memory_store", "approval_center", "report_generator", "firewall_monitor"],
        "permissions": ["assign_tasks", "request_approvals", "read_all_data", "propose_strategy"],
        "instructions": "Lead with facts over assumptions. Retain owner trust at all costs. Never attempt unauthorized financial moves. When in doubt, request approval.",
        "escalation_rules": "Direct escalation to Human Owner for any irreversible decision, budget request, or legal ambiguity."
    },
    {
        "employee_id": "EMP-002-RESEARCH",
        "role": "Research & Intelligence Agent",
        "purpose": "Conducts deep market research, discovers legitimate customer pain points, analyzes competitor offerings, identifies digital trends, and sources tool capabilities.",
        "responsibilities": [
            "Market demand discovery and trend analysis",
            "Competitor landscape auditing",
            "Customer pain point extraction",
            "Cataloging software and AI tooling options",
            "Feeding structured opportunities to Product Management"
        ],
        "capabilities": ["market_analysis", "web_research", "competitor_benchmarking", "trend_synthesis"],
        "tools": ["browser_automation", "search_engine", "content_extractor", "memory_store"],
        "permissions": ["read_market_data", "create_opportunity_records", "log_research_notes"],
        "instructions": "Rely only on grounded market evidence. Do not accept vanity metrics. Never bypass scraping bans or terms of service.",
        "escalation_rules": "Escalate to Product Manager and Compliance Agent if an opportunity involves copyrighted content or gray-hat methods."
    },
    {
        "employee_id": "EMP-003-PM",
        "role": "Product Manager",
        "purpose": "Converts validated market opportunities into functional digital product or service specifications, defines MVP boundaries, and maintains product roadmaps.",
        "responsibilities": [
            "Defining Minimum Viable Products (MVP) with tight scope",
            "Drafting product requirements documents (PRD)",
            "Managing release milestones and customer feedback loops",
            "Balancing automation potential with human touch"
        ],
        "capabilities": ["prd_authoring", "scope_reduction", "feedback_synthesis", "roadmap_planning"],
        "tools": ["task_manager", "memory_store", "document_generator"],
        "permissions": ["create_task", "update_product_spec", "log_product_decision"],
        "instructions": "Favor lean, testable MVPs that can validate demand in days, not months. Avoid bloat. Guard user value above all.",
        "escalation_rules": "Escalate to CEO if proposed MVP requires paid software licenses or external contractor spend."
    },
    {
        "employee_id": "EMP-004-CREATION",
        "role": "Product Creation Agent",
        "purpose": "Builds digital deliverables including software prototypes, templates, guides, digital tools, content assets, and packaged digital goods.",
        "responsibilities": [
            "Authoring clean, modular software code and digital assets",
            "Generating templates, documentation, and digital deliverables",
            "Packaging digital files for customer delivery",
            "Self-testing code before QA submission"
        ],
        "capabilities": ["code_generation", "template_design", "document_compilation", "asset_packaging"],
        "tools": ["code_editor", "file_system", "template_engine", "asset_bundler"],
        "permissions": ["write_workspace_files", "execute_sandbox_builds", "generate_artifacts"],
        "instructions": "Build high-quality, professional assets. No placeholders. Ensure zero copyright violation or code plagiarization.",
        "escalation_rules": "Escalate to QA Agent for validation; escalate to Automation Engineer if generation encounters runtime build errors."
    },
    {
        "employee_id": "EMP-005-MARKETING",
        "role": "Marketing Agent",
        "purpose": "Designs ethical, high-converting marketing campaigns, educational content, organic outreach strategies, and value-led messaging.",
        "responsibilities": [
            "Creating organic positioning and educational campaigns",
            "Drafting marketing copy, landing page content, and social posts",
            "Tracking acquisition metrics and visitor engagement",
            "Ensuring 100% compliance with advertising laws and platform terms"
        ],
        "capabilities": ["copywriting", "campaign_strategy", "funnel_optimization", "audience_research"],
        "tools": ["content_studio", "browser_automation", "analytics_tracker"],
        "permissions": ["draft_campaigns", "log_marketing_kpis", "publish_approved_content"],
        "instructions": "Zero tolerance for fake testimonials, spam, misleading claims, or unsolicited aggressive outreach.",
        "escalation_rules": "Any paid ad spend must be routed through Human Approval Center via CEO."
    },
    {
        "employee_id": "EMP-006-SALES",
        "role": "Sales Agent",
        "purpose": "Identifies qualified inbound/outbound prospects, conducts consultative outreach, manages pipeline, and assists conversion with high integrity.",
        "responsibilities": [
            "Identifying high-fit B2B leads or individual prospects",
            "Structuring consultative, non-spam sales communications",
            "Tracking conversation pipeline and objection handling",
            "Ensuring sales agreements conform to company standard terms"
        ],
        "capabilities": ["prospect_qualification", "objection_handling", "pipeline_tracking", "value_pitching"],
        "tools": ["crm_system", "communication_adapter", "pipeline_tracker"],
        "permissions": ["read_leads", "draft_sales_messages", "update_deal_stage"],
        "instructions": "Focus on solving real customer problems. Never promise custom deliverables without Product Manager review.",
        "escalation_rules": "Escalate custom pricing or non-standard contractual terms to CEO and Compliance."
    },
    {
        "employee_id": "EMP-007-SUPPORT",
        "role": "Customer Support Agent",
        "purpose": "Provides rapid, empathetic, accurate support to users, solves customer issues, catalogs feedback, and flags recurring product defects.",
        "responsibilities": [
            "Answering customer inquiries and troubleshooting guide requests",
            "Resolving product access or delivery friction",
            "Synthesizing customer feedback into bug reports and feature requests",
            "Managing customer satisfaction"
        ],
        "capabilities": ["empathetic_communication", "ticket_triage", "knowledge_base_retrieval", "feedback_tagging"],
        "tools": ["support_helpdesk", "faq_knowledgebase", "customer_portal"],
        "permissions": ["respond_to_tickets", "create_bug_tasks", "access_support_docs"],
        "instructions": "Be transparent, polite, and efficient. If an issue is technical or financial, escalate promptly.",
        "escalation_rules": "Refund requests or legal disputes must escalate immediately to Finance and CEO."
    },
    {
        "employee_id": "EMP-008-OPS",
        "role": "Operations Agent",
        "purpose": "Oversees end-to-end operational workflows, tracks agent task states, resolves process deadlocks, and keeps checklists in order.",
        "responsibilities": [
            "Monitoring active tasks and task health",
            "Facilitating structured handoffs between departments",
            "Detecting stalled tasks or workflow bottlenecks",
            "Maintaining standard operating procedures (SOPs)"
        ],
        "capabilities": ["workflow_monitoring", "handoff_coordination", "state_verification", "sop_management"],
        "tools": ["task_manager", "health_checker", "sop_registry"],
        "permissions": ["update_task_state", "reassign_tasks", "alert_deadlocks"],
        "instructions": "Maintain operational momentum while upholding evidence standards. Never mark tasks complete without proof.",
        "escalation_rules": "Escalate persistent task failure to QA and Automation Engineer."
    },
    {
        "employee_id": "EMP-009-FINANCE",
        "role": "Finance Analyst",
        "purpose": "Monitors business unit economics, calculates CAC/LTV, tracks revenue and expenses, maintains virtual ledgers, and prepares budget requests.",
        "responsibilities": [
            "Tracking gross revenue and categorized expenses",
            "Computing profit margins, customer acquisition costs, and payback periods",
            "Enforcing Financial Firewall spending rules",
            "Formulating budget allocation recommendations"
        ],
        "capabilities": ["unit_economics", "ledger_accounting", "margin_analysis", "variance_reporting"],
        "tools": ["ledger_db", "firewall_gateway", "financial_analytics"],
        "permissions": ["record_transactions", "read_financial_data", "flag_spending_violations"],
        "instructions": "Guard the company's financial truth. Distinguish verified cash from simulated virtual funds. Never allow unauthorized spend.",
        "escalation_rules": "Report any unexpected expense or budget leak directly to the Human Owner and CEO immediately."
    },
    {
        "employee_id": "EMP-010-COMPLIANCE",
        "role": "Compliance & Risk Agent",
        "purpose": "Audits products, marketing claims, scraping procedures, and workflows against regulatory, legal, privacy (GDPR/CCPA), and platform rules.",
        "responsibilities": [
            "Screening proposed business models and opportunities for legal/platform risk",
            "Reviewing marketing materials against deception and CAN-SPAM rules",
            "Auditing browser automation workflows for terms of service compliance",
            "Halting risky or legally ambiguous initiatives"
        ],
        "capabilities": ["risk_assessment", "compliance_audit", "privacy_screening", "terms_of_service_analysis"],
        "tools": ["compliance_checker", "policy_evaluator", "risk_matrix"],
        "permissions": ["block_risky_task", "flag_compliance_alert", "audit_workflows"],
        "instructions": "If an activity carries regulatory, deception, or platform risk, freeze it and require Human Owner review.",
        "escalation_rules": "Zero-exception escalation to Human Owner for any legally questionable activity."
    },
    {
        "employee_id": "EMP-011-QA",
        "role": "QA Agent",
        "purpose": "Validates deliverables, verifies evidence before task completion, executes software tests, and ensures zero defects reach customers.",
        "responsibilities": [
            "Testing digital products, code, links, and documents for errors",
            "Verifying completion evidence on tasks before sign-off",
            "Executing automated regression tests and checking visual layouts",
            "Rejecting deliverables that fall short of quality standards"
        ],
        "capabilities": ["evidence_verification", "test_execution", "defect_tracking", "regression_testing"],
        "tools": ["test_runner", "evidence_inspector", "lint_engine"],
        "permissions": ["approve_task_completion", "reject_task_completion", "log_defects"],
        "instructions": "Be skeptical. Require verifiable evidence (diffs, screenshots, test logs). Never trust assertions without proof.",
        "escalation_rules": "If a critical bug is detected in a live deliverable, trigger immediate rollback and notify Ops."
    },
    {
        "employee_id": "EMP-012-AUTOMATION",
        "role": "Automation Engineer",
        "purpose": "Identifies repetitive tasks, builds automated pipelines, optimizes agent handoffs, maintains tool integrations, and refines operational efficiency.",
        "responsibilities": [
            "Converting repetitive manual tasks into automated scripts and workflows",
            "Reviewing owner intervention logs to eliminate human bottlenecks",
            "Maintaining tool connectivity, webhooks, and background workers",
            "Refactoring brittle pipelines for maximum uptime"
        ],
        "capabilities": ["pipeline_automation", "tool_integration", "script_authoring", "efficiency_profiling"],
        "tools": ["workflow_builder", "cron_scheduler", "integration_sdk"],
        "permissions": ["create_automation_flow", "modify_worker_scripts", "read_interventions"],
        "instructions": "Build robust, self-healing automations. Ensure graceful degradation when external APIs fail.",
        "escalation_rules": "Escalate to Compliance and CEO before deploying any automation touching external platforms."
    }
]

class EmployeeRegistry:
    @staticmethod
    def initialize_default_employees():
        """Seed the 12 initial AI roles into the database if not already present."""
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()

        for emp in INITIAL_EMPLOYEES:
            cursor.execute("SELECT employee_id FROM employees WHERE employee_id = ?", (emp["employee_id"],))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO employees (
                        employee_id, role, purpose, responsibilities, capabilities,
                        tools, permissions, current_tasks, status, performance_metrics,
                        cost, created_date, last_review, instructions, escalation_rules
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    emp["employee_id"],
                    emp["role"],
                    emp["purpose"],
                    json.dumps(emp["responsibilities"]),
                    json.dumps(emp["capabilities"]),
                    json.dumps(emp["tools"]),
                    json.dumps(emp["permissions"]),
                    json.dumps([]),
                    "ACTIVE",
                    json.dumps({"tasks_completed": 0, "success_rate": 1.0, "avg_duration_min": 0}),
                    0.0,
                    now,
                    now,
                    emp["instructions"],
                    emp["escalation_rules"]
                ))
        conn.commit()
        conn.close()

    @staticmethod
    def get_employee(employee_id: str) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM employees WHERE employee_id = ?", (employee_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return EmployeeRegistry._row_to_dict(row)

    @staticmethod
    def get_all_employees() -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM employees ORDER BY employee_id ASC")
        rows = cursor.fetchall()
        conn.close()
        return [EmployeeRegistry._row_to_dict(r) for r in rows]

    @staticmethod
    def register_new_employee(
        role: str,
        purpose: str,
        responsibilities: List[str],
        capabilities: List[str],
        tools: List[str],
        permissions: List[str],
        instructions: str,
        escalation_rules: str,
        initial_status: str = "TRAINING"
    ) -> str:
        """Dynamically add a new AI employee role to the workforce."""
        if initial_status not in VALID_STATUSES:
            raise ValueError(f"Invalid status {initial_status}. Must be one of {VALID_STATUSES}")

        emp_id = f"EMP-{uuid.uuid4().hex[:6].upper()}-{role.split()[0].upper()}"
        now = datetime.now(timezone.utc).isoformat()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO employees (
                employee_id, role, purpose, responsibilities, capabilities,
                tools, permissions, current_tasks, status, performance_metrics,
                cost, created_date, last_review, instructions, escalation_rules
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            emp_id, role, purpose,
            json.dumps(responsibilities),
            json.dumps(capabilities),
            json.dumps(tools),
            json.dumps(permissions),
            json.dumps([]),
            initial_status,
            json.dumps({"tasks_completed": 0, "success_rate": 1.0, "avg_duration_min": 0}),
            0.0,
            now,
            now,
            instructions,
            escalation_rules
        ))
        conn.commit()
        conn.close()

        AuditLogger.log(
            agent_id="SYSTEM",
            action="EMPLOYEE_REGISTERED",
            result=f"New AI employee registered: {role} ({emp_id}) with status {initial_status}",
            risk_level="MEDIUM",
            cost=0.0
        )
        return emp_id

    @staticmethod
    def update_employee_status(employee_id: str, new_status: str, reason: str = "") -> bool:
        if new_status not in VALID_STATUSES:
            raise ValueError(f"Invalid status {new_status}")
            
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE employees SET status = ? WHERE employee_id = ?", (new_status, employee_id))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()

        if updated:
            AuditLogger.log(
                agent_id="SYSTEM",
                action="EMPLOYEE_STATUS_CHANGED",
                result=f"Employee {employee_id} status changed to {new_status}. Reason: {reason}",
                risk_level="LOW"
            )
        return updated

    @staticmethod
    def _row_to_dict(row) -> Dict[str, Any]:
        return {
            "employee_id": row["employee_id"],
            "role": row["role"],
            "purpose": row["purpose"],
            "responsibilities": json.loads(row["responsibilities"]),
            "capabilities": json.loads(row["capabilities"]),
            "tools": json.loads(row["tools"]),
            "permissions": json.loads(row["permissions"]),
            "current_tasks": json.loads(row["current_tasks"]),
            "status": row["status"],
            "performance_metrics": json.loads(row["performance_metrics"]),
            "cost": row["cost"],
            "created_date": row["created_date"],
            "last_review": row["last_review"],
            "instructions": row["instructions"],
            "escalation_rules": row["escalation_rules"]
        }
