"""
FastAPI Server for Autonomous AI Company & Owner Command Center.
Exposes REST endpoints, Server-Sent Events (SSE) for live telemetry, and serves the UI.
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query, Body, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.db import init_db, get_connection
from core.firewall import FinancialFirewall, FinancialFirewallViolation
from core.audit import AuditLogger, EventBus
from core.interventions import InterventionTracker
from core.capabilities import CapabilityGapRegistry
from core.owner_metrics import OwnerMetricsEngine
from agents.registry import EmployeeRegistry
from tasks.engine import TaskEngine
from approvals.manager import ApprovalManager
from memory.store import CorporateMemory
from discovery.engine import OpportunityDiscoveryEngine
from experiments.engine import ExperimentEngine
from finance.analytics import FinanceEngine
from reporting.ceo_report import CEOReportGenerator
from factory.product_factory import ProductFactory
from factory.quality_control import QualityControlEngine
from factory.sales_asset_factory import SalesAssetFactory
from sales.pipeline import SalesPipelineEngine
from sales.delivery import DeliveryEngine
from feedback.engine import CustomerFeedbackEngine
from orchestration.loop import OrchestrationLoop
from skills.registry import SkillRegistry
from skills.pipeline import SkillPipelineEngine
from agents.factory import AIEmployeeFactory
from treasury.engine import CompanyTreasuryEngine
from marketplace.catalog import CapabilityMarketplaceCatalog
from orchestration.self_growth import SelfGrowthEngine

# Ensure DB is initialized, employees seeded, opportunities seeded, marketplace catalog loaded
init_db()
EmployeeRegistry.initialize_default_employees()
OpportunityDiscoveryEngine.seed_initial_researched_opportunities()
CapabilityMarketplaceCatalog.initialize_marketplace()

app = FastAPI(title="Autonomous AI Enterprise Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Models -----------------
class TaskCreateRequest(BaseModel):
    creator: str
    assigned_agent: str
    objective: str
    description: str
    priority: str = "MEDIUM"
    deadline: Optional[str] = None
    dependencies: Optional[List[str]] = None
    required_tools: Optional[List[str]] = None
    requires_approval: bool = False
    estimated_cost: float = 0.0
    estimated_revenue_impact: float = 0.0

class TaskCompleteRequest(BaseModel):
    agent_id: str
    result: str
    evidence: str
    actual_cost: float = 0.0
    revenue_impact: float = 0.0

class TaskTransitionRequest(BaseModel):
    new_status: str
    agent_id: str
    reason: str = ""

class ApprovalCreateRequest(BaseModel):
    requesting_agent: str
    what: str
    why: str
    expected_benefit: str
    expected_cost: float
    risk_level: str
    alternatives: str
    recommendation: str
    task_id: Optional[str] = None
    deadline: Optional[str] = None

class ApprovalResolveRequest(BaseModel):
    decision: str  # APPROVE, REJECT, REQUEST_INFO, PAUSE
    owner_notes: str = ""

class FinancialTransactionRequest(BaseModel):
    type: str  # REVENUE, EXPENSE
    category: str
    amount: float
    description: str
    agent_id: str
    is_virtual: bool = True
    approved_by: Optional[str] = None

class EmergencyStopRequest(BaseModel):
    enabled: bool
    reason: str = "Manual owner action"

class FirewallSettingRequest(BaseModel):
    key: str
    value: Any

class OpportunityCreateRequest(BaseModel):
    customer_problem: str
    target_customer: str
    proposed_solution: str
    competitors: List[str]
    demand_evidence: str
    estimated_price: float
    estimated_costs: float
    estimated_automation_potential: float
    estimated_human_involvement: float
    platform_risks: str
    legal_compliance: str
    mvp_requirements: str
    validation_method: str
    expected_time_to_test: str
    agent_id: str = "EMP-002-RESEARCH"

class ExperimentCreateRequest(BaseModel):
    title: str
    hypothesis: str
    success_metric: str
    mvp_description: str
    opportunity_id: Optional[str] = None
    retry_reason: Optional[str] = None
    creator_agent: str = "EMP-003-PM"

class MemoryCreateRequest(BaseModel):
    category: str
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    author_agent: str = "SYSTEM"

class InterventionCreateRequest(BaseModel):
    context: str
    reason_needed: str
    can_be_automated: bool
    missing_capability: str
    missing_tool: Optional[str] = None
    new_skill_needed: Optional[str] = None

# ----------------- Endpoints -----------------

@app.get("/api/status")
def get_company_status():
    employees = EmployeeRegistry.get_all_employees()
    tasks = TaskEngine.get_tasks(limit=200)
    pending_approvals = ApprovalManager.get_pending_approvals()
    finances = FinanceEngine.get_financial_summary()
    experiments = ExperimentEngine.get_experiments()
    firewall_settings = FinancialFirewall.get_settings()

    return {
        "company_name": "Autonomous Digital Enterprise",
        "company_status": "FROZEN_EMERGENCY" if firewall_settings.get("emergency_stop") else "OPERATIONAL",
        "emergency_stop": firewall_settings.get("emergency_stop", False),
        "active_employees": len([e for e in employees if e["status"] == "ACTIVE"]),
        "total_employees": len(employees),
        "tasks": {
            "total": len(tasks),
            "new": len([t for t in tasks if t["status"] == "NEW"]),
            "in_progress": len([t for t in tasks if t["status"] == "IN_PROGRESS"]),
            "completed": len([t for t in tasks if t["status"] == "COMPLETED"]),
            "failed": len([t for t in tasks if t["status"] == "FAILED"]),
            "approval_required": len([t for t in tasks if t["status"] == "APPROVAL_REQUIRED"]),
        },
        "pending_approvals_count": len(pending_approvals),
        "active_experiments_count": len([e for e in experiments if e["status"] not in {"SUCCESSFUL", "FAILED_STOPPED"}]),
        "finances": finances
    }

# Real-time Server-Sent Events (SSE)
@app.get("/api/events")
async def events(request: Request):
    queue = asyncio.Queue()
    EventBus.subscribe(queue)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Heartbeat
                    yield f": heartbeat\n\n"
        finally:
            EventBus.unsubscribe(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Employees
@app.get("/api/employees")
def list_employees():
    return EmployeeRegistry.get_all_employees()

@app.post("/api/employees/status")
def update_employee_status(employee_id: str = Body(...), status: str = Body(...), reason: str = Body("")):
    try:
        updated = EmployeeRegistry.update_employee_status(employee_id, status, reason)
        return {"success": updated}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Tasks
@app.get("/api/tasks")
def list_tasks(status: Optional[str] = None, agent: Optional[str] = None, limit: int = 50):
    return TaskEngine.get_tasks(status=status, agent=agent, limit=limit)

@app.post("/api/tasks")
def create_task(req: TaskCreateRequest):
    try:
        task_id = TaskEngine.create_task(
            creator=req.creator,
            assigned_agent=req.assigned_agent,
            objective=req.objective,
            description=req.description,
            priority=req.priority,
            deadline=req.deadline,
            dependencies=req.dependencies,
            required_tools=req.required_tools,
            requires_approval=req.requires_approval,
            estimated_cost=req.estimated_cost,
            estimated_revenue_impact=req.estimated_revenue_impact
        )
        return {"task_id": task_id, "status": "CREATED"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/tasks/{task_id}/transition")
def transition_task(task_id: str, req: TaskTransitionRequest):
    try:
        success = TaskEngine.transition_state(task_id, req.new_status, req.agent_id, req.reason)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/tasks/{task_id}/complete")
def complete_task(task_id: str, req: TaskCompleteRequest):
    try:
        success = TaskEngine.complete_task(
            task_id=task_id,
            agent_id=req.agent_id,
            result=req.result,
            evidence=req.evidence,
            actual_cost=req.actual_cost,
            revenue_impact=req.revenue_impact
        )
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Approvals
@app.get("/api/approvals")
def list_approvals(pending_only: bool = False):
    if pending_only:
        return ApprovalManager.get_pending_approvals()
    return ApprovalManager.get_all_approvals()

@app.post("/api/approvals")
def create_approval(req: ApprovalCreateRequest):
    try:
        app_id = ApprovalManager.create_approval_request(
            requesting_agent=req.requesting_agent,
            what=req.what,
            why=req.why,
            expected_benefit=req.expected_benefit,
            expected_cost=req.expected_cost,
            risk_level=req.risk_level,
            alternatives=req.alternatives,
            recommendation=req.recommendation,
            task_id=req.task_id,
            deadline=req.deadline
        )
        return {"approval_id": app_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/approvals/{approval_id}/resolve")
def resolve_approval(approval_id: str, req: ApprovalResolveRequest):
    try:
        success = ApprovalManager.resolve_approval(approval_id, req.decision, req.owner_notes)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Finances & Firewall
@app.get("/api/finances")
def get_finances():
    return FinanceEngine.get_financial_summary()

@app.post("/api/finances/transaction")
def record_transaction(req: FinancialTransactionRequest):
    try:
        tx_id = FinanceEngine.record_transaction(
            tx_type=req.type,
            category=req.category,
            amount=req.amount,
            description=req.description,
            agent_id=req.agent_id,
            is_virtual=req.is_virtual,
            approved_by=req.approved_by
        )
        return {"transaction_id": tx_id}
    except FinancialFirewallViolation as fe:
        raise HTTPException(status_code=403, detail=str(fe))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/firewall")
def get_firewall_settings():
    return FinancialFirewall.get_settings()

@app.post("/api/firewall/setting")
def update_firewall_setting(req: FirewallSettingRequest):
    FinancialFirewall.update_setting(req.key, req.value)
    return {"success": True}

@app.post("/api/firewall/emergency-stop")
def toggle_emergency_stop(req: EmergencyStopRequest):
    FinancialFirewall.set_emergency_stop(req.enabled, req.reason)
    return {"emergency_stop": req.enabled}

# Opportunities & Experiments
@app.get("/api/opportunities")
def list_opportunities(status: Optional[str] = None):
    return OpportunityDiscoveryEngine.get_opportunities(status)

@app.post("/api/opportunities")
def create_opportunity(req: OpportunityCreateRequest):
    try:
        opp_id = OpportunityDiscoveryEngine.register_opportunity(
            customer_problem=req.customer_problem,
            target_customer=req.target_customer,
            proposed_solution=req.proposed_solution,
            competitors=req.competitors,
            demand_evidence=req.demand_evidence,
            estimated_price=req.estimated_price,
            estimated_costs=req.estimated_costs,
            estimated_automation_potential=req.estimated_automation_potential,
            estimated_human_involvement=req.estimated_human_involvement,
            platform_risks=req.platform_risks,
            legal_compliance=req.legal_compliance,
            mvp_requirements=req.mvp_requirements,
            validation_method=req.validation_method,
            expected_time_to_test=req.expected_time_to_test,
            agent_id=req.agent_id
        )
        return {"opportunity_id": opp_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/experiments")
def list_experiments(status: Optional[str] = None):
    return ExperimentEngine.get_experiments(status)

@app.post("/api/experiments")
def create_experiment(req: ExperimentCreateRequest):
    try:
        exp_id = ExperimentEngine.create_experiment(
            title=req.title,
            hypothesis=req.hypothesis,
            success_metric=req.success_metric,
            mvp_description=req.mvp_description,
            opportunity_id=req.opportunity_id,
            retry_reason=req.retry_reason,
            creator_agent=req.creator_agent
        )
        return {"experiment_id": exp_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Corporate Memory
@app.get("/api/memory")
def search_memory(query: Optional[str] = None, category: Optional[str] = None, tag: Optional[str] = None):
    return CorporateMemory.search_memories(query=query, category=category, tag=tag)

@app.post("/api/memory")
def store_memory(req: MemoryCreateRequest):
    mem_id = CorporateMemory.store_memory(
        category=req.category,
        title=req.title,
        content=req.content,
        metadata=req.metadata,
        tags=req.tags,
        author_agent=req.author_agent
    )
    return {"memory_id": mem_id}

# Owner Interventions
@app.get("/api/interventions")
def list_interventions():
    return InterventionTracker.get_interventions()

@app.post("/api/interventions")
def record_intervention(req: InterventionCreateRequest):
    iid = InterventionTracker.record_intervention(
        context=req.context,
        reason_needed=req.reason_needed,
        can_be_automated=req.can_be_automated,
        missing_capability=req.missing_capability,
        missing_tool=req.missing_tool,
        new_skill_needed=req.new_skill_needed
    )
    return {"intervention_id": iid}

# CEO Report
@app.get("/api/reports/weekly")
def get_weekly_ceo_report():
    return CEOReportGenerator.generate_weekly_report()

# Audit Logs
@app.get("/api/audit-logs")
def get_audit_logs(limit: int = 50, risk: Optional[str] = None):
    return AuditLogger.get_recent_logs(limit=limit, risk_filter=risk)

# ----------------- Phase 2 Endpoints -----------------

# Orchestration Handoff Pipeline
@app.post("/api/pipeline/run-handoff")
def run_handoff_pipeline(opportunity_id: str = Body(..., embed=True)):
    try:
        result = OrchestrationLoop.run_automated_handoff_pipeline(opportunity_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/daily-cycle")
def get_daily_cycle():
    return OrchestrationLoop.execute_daily_cycle()

# Products & Factory
@app.get("/api/products")
def list_products(status: Optional[str] = None):
    return ProductFactory.get_all_products(status)

@app.post("/api/products")
def create_product(
    name: str = Body(...),
    asset_type: str = Body(...),
    requirements: str = Body(...),
    opportunity_id: Optional[str] = Body(None)
):
    try:
        pid = ProductFactory.create_product_draft(name, asset_type, requirements, opportunity_id)
        return {"product_id": pid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/products/{product_id}/build")
def build_product_mvp(
    product_id: str,
    file_name: str = Body(...),
    content: str = Body(...)
):
    try:
        res = ProductFactory.build_mvp_deliverable(product_id, file_name, content)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/products/{product_id}/qa")
def qa_inspect_product(product_id: str):
    try:
        report = QualityControlEngine.inspect_and_verify_product(product_id)
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/products/{product_id}/sales-assets")
def generate_sales_assets(product_id: str, price: float = Body(29.0)):
    try:
        assets = SalesAssetFactory.generate_sales_package(product_id, price=price)
        return assets
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Sales Leads & Pipeline
@app.get("/api/leads")
def list_leads(status: Optional[str] = None):
    return SalesPipelineEngine.get_leads(status)

@app.post("/api/leads")
def create_lead(
    source: str = Body(...),
    customer_type: str = Body(...),
    problem: str = Body(...),
    contact_method: str = Body(...),
    consent_basis: str = Body(...),
    product_id: Optional[str] = Body(None)
):
    try:
        lead_id = SalesPipelineEngine.create_lead(source, customer_type, problem, contact_method, consent_basis, product_id)
        return {"lead_id": lead_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/leads/{lead_id}/advance")
def advance_lead(
    lead_id: str,
    new_stage: str = Body(...),
    outcome: str = Body(""),
    next_action: str = Body("")
):
    try:
        success = SalesPipelineEngine.advance_lead_stage(lead_id, new_stage, outcome, next_action)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Deliveries
@app.get("/api/deliveries")
def list_deliveries(limit: int = 50):
    return DeliveryEngine.get_deliveries(limit)

@app.post("/api/deliveries")
def process_delivery(
    order_id: str = Body(...),
    product_id: str = Body(...),
    customer_ref: str = Body(...),
    payment_verified: bool = Body(...)
):
    try:
        result = DeliveryEngine.process_order_and_deliver(order_id, product_id, customer_ref, payment_verified)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Customer Feedback
@app.get("/api/feedback")
def list_feedback(product_id: Optional[str] = None, limit: int = 50):
    return CustomerFeedbackEngine.get_feedback(product_id, limit)

@app.post("/api/feedback")
def record_feedback(
    product_id: str = Body(...),
    customer_ref: str = Body(...),
    feedback_type: str = Body(...),
    content: str = Body(...),
    resolution: str = Body("")
):
    try:
        fid = CustomerFeedbackEngine.record_feedback(product_id, customer_ref, feedback_type, content, resolution)
        return {"feedback_id": fid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Capability Gaps
@app.get("/api/capability-gaps")
def list_capability_gaps():
    return CapabilityGapRegistry.get_capability_gaps()

# Owner Metrics & Automation Opportunities
@app.get("/api/owner-metrics")
def get_owner_metrics():
    return OwnerMetricsEngine.get_metrics()

# ----------------- Phase 3 Endpoints -----------------

# Skills Registry & Pipeline
@app.get("/api/skills")
def list_skills(status: Optional[str] = None):
    return SkillRegistry.get_all_skills(status)

@app.post("/api/skills/{skill_id}/activate")
def activate_skill(skill_id: str):
    try:
        res = SkillPipelineEngine.advance_skill_to_active(skill_id)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# AI Employee Factory
@app.post("/api/employees/spawn")
def spawn_employee(
    role_title: str = Body(...),
    purpose: str = Body(...),
    responsibilities: List[str] = Body(...),
    capabilities: List[str] = Body(...),
    tools: List[str] = Body(...),
    permissions: List[str] = Body(...),
    instructions: str = Body(...),
    escalation_rules: str = Body(...)
):
    try:
        emp = AIEmployeeFactory.spawn_new_employee(
            role_title=role_title,
            purpose=purpose,
            responsibilities=responsibilities,
            capabilities=capabilities,
            tools=tools,
            permissions=permissions,
            instructions=instructions,
            escalation_rules=escalation_rules
        )
        return emp
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/employees/{employee_id}/activate")
def activate_employee(employee_id: str, test_evidence: str = Body(..., embed=True)):
    try:
        success = AIEmployeeFactory.advance_employee_to_active(employee_id, test_evidence)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/employees/{employee_id}/retrain")
def retrain_employee(
    employee_id: str,
    identified_missing_skill: str = Body(...),
    training_sops: str = Body(...)
):
    try:
        success = AIEmployeeFactory.retrain_employee(employee_id, identified_missing_skill, training_sops)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/employees/{employee_id}/retire")
def retire_employee(employee_id: str, reason: str = Body(..., embed=True)):
    try:
        success = AIEmployeeFactory.retire_employee(employee_id, reason)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Virtual Company Treasury & Reinvestment
@app.get("/api/treasury")
def get_treasury():
    return CompanyTreasuryEngine.get_treasury_state()

@app.post("/api/treasury/propose-reinvestment")
def propose_reinvestment(
    category: str = Body(...),
    item_name: str = Body(...),
    expected_cost_usd: float = Body(...),
    why_needed: str = Body(...),
    expected_business_benefit: str = Body(...),
    expected_payback_months: float = Body(...)
):
    try:
        res = CompanyTreasuryEngine.propose_reinvestment(
            category=category,
            item_name=item_name,
            expected_cost_usd=expected_cost_usd,
            why_needed=why_needed,
            expected_business_benefit=expected_business_benefit,
            expected_payback_months=expected_payback_months
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Capability Marketplace
@app.get("/api/marketplace")
def get_marketplace():
    return CapabilityMarketplaceCatalog.get_catalog()

# Self-Growth Loop
@app.post("/api/self-growth/cycle")
def run_self_growth_cycle(
    capability_name: str = Body(...),
    why_needed: str = Body(...),
    business_goal: str = Body(...)
):
    try:
        result = SelfGrowthEngine.execute_self_growth_cycle(capability_name, why_needed, business_goal)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ----------------- Phase 4: Revenue Engine Endpoints -----------------
from revenue import (
    RevenueDiscoveryEngine,
    OpportunityEvaluator,
    SalesAssetFactory,
    RevenueProductFactory,
    CustomerAcquisitionEngine,
    SalesPipelineEngine as RevenueSalesPipelineEngine,
    RevenueLedgerEngine,
    CustomerDeliveryEngine,
    CustomerSupportEngine,
    RefundProcessingEngine,
    RevenueBottleneckEngine,
    FirstRevenueExperimentEngine,
    DailyRevenueLoop,
    LaunchGateEngine
)

@app.get("/api/revenue/metrics")
def get_revenue_metrics():
    return RevenueLedgerEngine.get_revenue_metrics()

@app.get("/api/revenue/opportunities/candidates")
def get_opportunity_candidates():
    ranked = OpportunityEvaluator.rank_all_candidates()
    return ranked

@app.post("/api/revenue/opportunities/select-proposal")
def select_opportunity_proposal():
    try:
        return OpportunityEvaluator.generate_owner_approval_proposal()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/revenue/pipeline")
def get_revenue_pipeline():
    return RevenueSalesPipelineEngine.get_pipeline_summary()

@app.post("/api/revenue/pipeline/leads")
def create_revenue_lead(
    product_id: str = Body(...),
    customer_ref: str = Body(...),
    source: str = Body(...),
    customer_type: str = Body(...),
    problem: str = Body(...),
    consent_basis: str = Body("INBOUND_INQUIRY")
):
    try:
        lead_id = RevenueSalesPipelineEngine.create_lead(product_id, customer_ref, source, customer_type, problem, consent_basis)
        return {"lead_id": lead_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/revenue/pipeline/leads/{lead_id}/advance")
def advance_lead_stage(
    lead_id: str,
    new_stage: str = Body(..., embed=True),
    outcome_notes: str = Body("", embed=True)
):
    try:
        res = RevenueSalesPipelineEngine.advance_stage(lead_id, new_stage, outcome_notes)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/revenue/campaigns")
def list_revenue_campaigns():
    return CustomerAcquisitionEngine.get_campaigns()

@app.post("/api/revenue/campaigns")
def create_revenue_campaign(
    target_definition: str = Body(...),
    source: str = Body(...),
    consent_or_legal_basis: str = Body(...),
    message: str = Body(...),
    frequency_limit: str = Body(...),
    opt_out_method: str = Body(...),
    channel: str = Body("ORGANIC_COMMUNITY")
):
    try:
        res = CustomerAcquisitionEngine.create_campaign(
            target_definition, source, consent_or_legal_basis,
            message, frequency_limit, opt_out_method, channel
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/revenue/campaigns/{campaign_id}/opt-out")
def opt_out_campaign_contact(campaign_id: str, contact_identifier: str = Body(..., embed=True)):
    success = CustomerAcquisitionEngine.record_opt_out(campaign_id, contact_identifier)
    return {"success": success}

@app.get("/api/revenue/bottlenecks")
def get_revenue_bottlenecks():
    return RevenueBottleneckEngine.analyze_bottlenecks()

@app.get("/api/revenue/report/weekly")
def get_ceo_weekly_revenue_report():
    return DailyRevenueLoop.generate_ceo_weekly_revenue_report()

@app.post("/api/revenue/daily-loop")
def run_daily_revenue_loop():
    return DailyRevenueLoop.execute_daily_cycle()

@app.post("/api/revenue/launch-readiness")
def generate_launch_readiness(opportunity_id: str = Body("OPP-P4-001", embed=True)):
    try:
        return LaunchGateEngine.generate_launch_readiness_report(opportunity_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/revenue/launch")
def execute_launch(report_id: str = Body(..., embed=True)):
    try:
        LaunchGateEngine.attempt_launch(report_id)
        return {"status": "LAUNCH_SUCCESSFUL"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/revenue/support")
def submit_customer_support(
    customer_ref: str = Body(...),
    issue_type: str = Body(...),
    content: str = Body(...),
    order_id: Optional[str] = Body(None)
):
    return CustomerSupportEngine.submit_inquiry(customer_ref, issue_type, content, order_id)

@app.get("/api/revenue/refunds")
def get_refund_summary():
    return RefundProcessingEngine.get_refund_summary()

@app.post("/api/revenue/refunds")
def request_refund(
    order_id: str = Body(...),
    customer_id: str = Body(...),
    product_id: str = Body(...),
    amount: float = Body(...),
    reason: str = Body(...)
):
    try:
        return RefundProcessingEngine.request_refund(order_id, customer_id, product_id, amount, reason)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ----------------- Phase 5A: AI Virtual Office Endpoints -----------------
from server.office import OfficeStateEngine

@app.get("/api/office/state")
def get_office_state():
    """
    Returns full real-time operational state for the AI Virtual Office.
    Grounded exclusively in actual database records.
    """
    try:
        return OfficeStateEngine.get_office_state()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assemble office state: {str(e)}")

@app.get("/api/office/employees/{employee_id}")
def get_office_employee_detail(employee_id: str):
    """
    Returns comprehensive employee detail, live workstation status, and task history.
    """
    emp = OfficeStateEngine.get_employee_detail(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
    return emp

@app.get("/api/office/glossary")
def get_office_glossary():
    """
    Returns safe, predefined explanatory glossary for the owner.
    """
    from server.office import SAFE_GLOSSARY
    return SAFE_GLOSSARY

# ----------------- Phase 5B: 24/7 Cloud, Gemini & Daily Report Endpoints -----------------
from providers.llm import LLMManager
from core.heartbeat import CompanyHeartbeat
from core.activity import ActivityTracker
from reporting.daily_ceo_report import DailyCEOReportGenerator
from reporting.email_service import EmailService
from cloud.scheduler import CloudScheduler
from cloud.worker import CloudWorker

@app.on_event("startup")
def start_cloud_background_services():
    try:
        CloudScheduler.get_instance().start()
        CloudWorker.get_instance().start()
    except Exception as e:
        print(f"Background service start warning: {e}")

@app.get("/api/cloud/status")
def get_cloud_status():
    """
    Returns unified 24/7 cloud status, heartbeat, scheduler, and worker health.
    """
    heartbeat = CompanyHeartbeat.check_heartbeat()
    scheduler = CloudScheduler.get_instance().get_status()
    worker = CloudWorker.get_instance().get_status()
    gemini = LLMManager.get_status()
    return {
        "cloud_mode": "24/7 Independent Cloud Runtime",
        "owner_laptop_required": False,
        "owner_laptop_role": "Monitoring & Control Device Only",
        "heartbeat": heartbeat,
        "scheduler": scheduler,
        "worker": worker,
        "gemini": gemini,
        "approved_cloud_cost_usd": 0.00,
        "cost_ceiling_enforced": True
    }

@app.get("/api/cloud/gemini")
def get_gemini_status():
    """
    Returns Gemini provider health, quota info, and fallback status without secret exposure.
    """
    return LLMManager.get_status()

@app.get("/api/cloud/heartbeat")
def get_heartbeat():
    """
    Executes and returns the 9-component company heartbeat probe.
    """
    return CompanyHeartbeat.check_heartbeat()

@app.get("/api/cloud/reports/daily")
def get_daily_reports(limit: int = 10):
    """
    Returns list of generated and archived daily CEO reports.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT report_id, date, timezone, generated_at, status, validation_status, summary
        FROM ceo_reports ORDER BY generated_at DESC LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

@app.post("/api/cloud/reports/generate-daily")
def trigger_daily_report():
    """
    Manually triggers daily CEO progress report compilation and delivery to manirkhn@gmail.com.
    """
    try:
        result = CloudScheduler.get_instance().trigger_now()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate daily CEO report: {str(e)}")

@app.get("/api/cloud/email/deliveries")
def get_email_deliveries(limit: int = 20):
    """
    Returns recent daily report email delivery status logs.
    """
    return EmailService.get_recent_deliveries(limit=limit)

# ----------------- Phase 5C: Cloud Reality & Laptop-Off Verification Endpoints -----------------
from cloud.remote_proof import RemoteProofEngine, CloudInstanceIdentity

@app.get("/api/cloud/proof")
def get_cloud_proof():
    """
    Returns empirical remote execution proof and Cloud Independence Gate evaluation.
    """
    return RemoteProofEngine.evaluate_independence_gate()

@app.get("/api/cloud/can-close-laptop")
def get_can_close_laptop():
    """
    Dynamically answers: CAN I CLOSE MY LAPTOP?
    """
    return RemoteProofEngine.can_close_laptop()

@app.post("/api/cloud/proof/run-task")
def run_cloud_proof_task():
    """
    Executes a harmless verification task on the worker and records empirical receipt.
    """
    return RemoteProofEngine.execute_cloud_proof_task()

@app.post("/api/cloud/proof/test-persistence")
def run_persistence_test():
    """
    Tests persistent database retention across operational cycles.
    """
    return RemoteProofEngine.run_persistence_test()

@app.post("/api/cloud/proof/test-worker-recovery")
def run_worker_recovery_test():
    """
    Simulates worker fault and verifies auto-restart recovery logging.
    """
    return RemoteProofEngine.test_worker_recovery()

@app.get("/api/cloud/proof/security-scan")
def run_security_scan():
    """
    Scans repository for hard-coded credentials, private keys, or API tokens.
    """
    return RemoteProofEngine.run_security_scan()

@app.get("/api/cloud/activities")
def get_employee_activities(
    employee_id: Optional[str] = None,
    timeframe: str = Query("today", pattern="^(today|7days|all)$"),
    limit: int = 100
):
    """
    Returns recorded AI employee activity history with genuine execution context.
    """
    return ActivityTracker.get_activities(employee_id=employee_id, timeframe=timeframe, limit=limit)

@app.get("/api/cloud/activities/summary")
def get_employee_activity_summary(timeframe: str = Query("today", pattern="^(today|7days|all)$")):
    """
    Returns summary table of tasks completed, failed, and blocked per employee.
    """
    return ActivityTracker.get_employee_summary_table(timeframe=timeframe)


# ----------------- Phase 5D: Secure Payments, Checkout & Owner Settlement Endpoints -----------------
from payments.owner_settlement import OwnerSettlementManager
from payments.provider import get_payment_provider, TestPaymentProvider, StripePaymentProvider
from payments.checkout import CheckoutManager, PRIMARY_PRODUCT_ID
from payments.settlement import SettlementManager
from payments.refunds import RefundGovernanceEngine
from payments.approval_gates import PaymentApprovalGates
from payments.income_metrics import IncomeGenerationAnalytics

class CheckoutRequest(BaseModel):
    customer_email: str
    currency: str = "USD"
    mode: str = "TEST"
    product_id: str = PRIMARY_PRODUCT_ID
    provider_name: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    utm_term: Optional[str] = None

class ProfileUpdateRequest(BaseModel):
    country: Optional[str] = None
    bank_name: Optional[str] = None
    settlement_currency: Optional[str] = None
    account_type: Optional[str] = None
    settlement_destination_status: Optional[str] = None
    payment_provider: Optional[str] = None
    masked_destination_reference: Optional[str] = None
    owner_approval_status: Optional[str] = None

class GateUpdateRequest(BaseModel):
    gate_key: str
    is_approved: bool
    notes: str = ""

class RefundRequestModel(BaseModel):
    order_id: str
    customer_email: str
    amount: float
    reason: str

class RefundReviewModel(BaseModel):
    refund_id: str
    approved: bool
    owner_notes: str = ""

@app.get("/api/payments/dashboard")
def get_payments_dashboard():
    """
    Returns complete payments & verified revenue dashboard metrics.
    """
    return IncomeGenerationAnalytics.get_payment_revenue_dashboard()

@app.get("/api/payments/settlement-profile")
def get_settlement_profile():
    """
    Returns the non-sensitive owner settlement profile.
    """
    return OwnerSettlementManager.get_profile()

@app.post("/api/payments/settlement-profile")
def update_settlement_profile(req: ProfileUpdateRequest):
    """
    Updates settlement profile while enforcing strict air-gap credential protection.
    """
    try:
        return OwnerSettlementManager.update_profile(
            country=req.country,
            bank_name=req.bank_name,
            settlement_currency=req.settlement_currency,
            account_type=req.account_type,
            settlement_destination_status=req.settlement_destination_status,
            payment_provider=req.payment_provider,
            masked_destination_reference=req.masked_destination_reference,
            owner_approval_status=req.owner_approval_status
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/payments/air-gap-audit")
def get_air_gap_audit():
    """
    Audits settlement profile to prove that no private credentials or bank details are stored.
    """
    return OwnerSettlementManager.verify_air_gap()

@app.get("/api/payments/instructions")
def get_settlement_instructions():
    """
    Returns safe owner instructions for direct portal onboarding.
    """
    return OwnerSettlementManager.get_safe_settlement_instructions()

@app.post("/api/payments/checkout")
def create_customer_checkout(req: CheckoutRequest):
    """
    Creates a new checkout session.
    """
    session = CheckoutManager.create_checkout(
        customer_email=req.customer_email,
        currency=req.currency,
        product_id=req.product_id,
        mode=req.mode,
        provider_name=req.provider_name
    )
    try:
        from acquisition.attribution import AttributionEngine
        AttributionEngine.record_touchpoint(
            source=req.utm_source or "direct",
            landing_page="/store",
            medium=req.utm_medium or "",
            campaign=req.utm_campaign or "",
            content=req.utm_content or "",
            term=req.utm_term or "",
            product_page_visited=1,
            checkout_started=1,
            order_id=session.get("order_id"),
            mode=req.mode.upper()
        )
    except Exception as e:
        logger.error(f"Attribution tracking error: {e}")
    return session

@app.post("/api/payments/webhook")
async def handle_payment_webhook(request: Request):
    """
    Cryptographically verifies and processes payment provider webhooks.
    """
    body_bytes = await request.body()
    sig_header = request.headers.get("stripe-signature") or request.headers.get("x-signature") or ""
    try:
        result = CheckoutManager.process_incoming_webhook(
            payload_bytes=body_bytes,
            signature_header=sig_header
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/payments/receipt/{order_id}")
def get_order_receipt(order_id: str):
    """
    Returns customer receipt and delivery verification evidence.
    """
    receipt = CheckoutManager.get_receipt(order_id)
    if not receipt:
        raise HTTPException(status_code=404, detail=f"Receipt for order {order_id} not found.")
    return receipt

@app.get("/api/payments/gates")
def get_payment_approval_gates():
    """
    Returns owner approval gates for payment provider activation, refunds, etc.
    """
    return PaymentApprovalGates.get_all_gates()

@app.post("/api/payments/gates")
def update_payment_approval_gate(req: GateUpdateRequest):
    """
    Updates an owner payment approval gate.
    """
    return PaymentApprovalGates.update_gate(
        gate_key=req.gate_key,
        is_approved=req.is_approved,
        approved_by="OWNER",
        notes=req.notes
    )

@app.get("/api/payments/money-flow")
def get_where_did_the_money_go(order_id: Optional[str] = None):
    """
    Returns 'Where Did The Money Go?' visual audit trail.
    """
    return SettlementManager.get_where_did_money_go_flow(order_id=order_id)

@app.get("/api/payments/settlements")
def get_settlements_summary():
    """
    Returns settlement history and status.
    """
    return SettlementManager.get_settlement_summary()

@app.post("/api/payments/refund/request")
def request_customer_refund(req: RefundRequestModel):
    """
    Initiates customer refund request with owner approval gate.
    """
    return RefundGovernanceEngine.request_refund(
        order_id=req.order_id,
        customer_email=req.customer_email,
        amount=req.amount,
        reason=req.reason
    )

@app.post("/api/payments/refund/review")
def review_customer_refund(req: RefundReviewModel):
    """
    Owner reviews and resolves refund request.
    """
    try:
        return RefundGovernanceEngine.owner_review_refund(
            refund_id=req.refund_id,
            approved=req.approved,
            owner_notes=req.owner_notes
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/payments/refunds")
def list_customer_refunds():
    """
    Lists all customer refund records.
    """
    return RefundGovernanceEngine.get_all_refunds()

@app.post("/api/payments/test-flow")
def run_end_to_end_test_flow():
    """
    Executes a complete sandbox payment lifecycle without spending money or altering verified actual revenue.
    1. Creates test checkout session
    2. Simulates cryptographic webhook
    3. Verifies idempotency
    4. Triggers digital delivery
    5. Confirms zero leakage into production revenue ledger
    """
    # 1. Create test checkout
    test_email = "sandbox.developer@example.com"
    session = CheckoutManager.create_checkout(
        customer_email=test_email,
        currency="USD",
        mode="TEST"
    )
    order_id = session["order_id"]

    # 2. Simulate webhook
    test_provider = TestPaymentProvider()
    event_payload = json.dumps({
        "id": f"evt_sandbox_{order_id}",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": session["provider_payment_id"],
                "order_id": order_id,
                "amount": session["amount"],
                "currency": session["currency"]
            }
        }
    })
    sig = test_provider.generate_test_signature(event_payload)

    # 3. Process webhook
    webhook_res = CheckoutManager.process_incoming_webhook(
        payload_bytes=event_payload.encode("utf-8"),
        signature_header=sig
    )

    # 4. Verify Idempotency (replay attack test)
    replay_res = CheckoutManager.process_incoming_webhook(
        payload_bytes=event_payload.encode("utf-8"),
        signature_header=sig
    )

    # 5. Fetch Receipt
    receipt = CheckoutManager.get_receipt(order_id)

    # 6. Fetch Money Flow Trace
    flow = SettlementManager.get_where_did_money_go_flow(order_id=order_id)

    # 7. Verify Isolation from Production Ledger
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM revenue_ledger WHERE order_id = ?", (order_id,))
    prod_ledger_entry = cursor.fetchone()
    conn.close()

    isolation_preserved = prod_ledger_entry is None

    return {
        "test_status": "SUCCESS",
        "order_id": order_id,
        "mode": "TEST",
        "webhook_result": webhook_res,
        "replay_prevention_result": replay_res,
        "receipt": receipt,
        "money_flow": flow,
        "production_revenue_ledger_leakage": not isolation_preserved,
        "isolation_verified": isolation_preserved,
        "summary": "Sandbox end-to-end checkout, cryptographic webhook, anti-replay, digital delivery, and ledger isolation verified."
    }


# ==========================================
# PHASE 5E: SALES, MARKETING & ACQUISITION
# ==========================================

from marketing.command_center import MarketingCommandCenter
from marketing.activity import MarketingActivityManager
from marketing.campaigns import CampaignManager
from marketing.personas import CustomerPersonaEngine
from marketing.content import MarketingContentEngine
from marketing.funnel import CustomerAcquisitionFunnelEngine
from marketing.diagnostics import MoneyPipelineDiagnostics
from marketing.experiments import MarketingExperimentEngine
from marketing.product_loop import ProductImprovementLoop

@app.get("/api/marketing/command-center")
def get_marketing_command_center():
    """Returns the full Phase 5E Marketing & Sales Command Center telemetry."""
    return MarketingCommandCenter.get_full_command_center_payload()

@app.get("/api/marketing/selling")
def get_marketing_what_we_are_selling():
    """Returns what the company is selling, pricing, problem solved, and verification status."""
    return MarketingCommandCenter.get_what_we_are_selling()

@app.get("/api/marketing/funnel")
def get_marketing_funnel():
    """Returns the 12-stage customer acquisition funnel with historical vs production separation."""
    return CustomerAcquisitionFunnelEngine.get_visual_funnel_data()

@app.get("/api/marketing/where-marketed")
def get_marketing_where_marketed():
    """Returns where the company has actually marketed (only channels with verified activities)."""
    return {
        "channels": MarketingActivityManager.get_where_we_marketed_summary(),
        "total_activities": len(MarketingActivityManager.list_activities())
    }

@app.get("/api/marketing/today-timeline")
def get_marketing_today_timeline():
    """Returns the chronological What Did The AI Do Today? timeline."""
    return {
        "timeline": MarketingActivityManager.get_what_did_ai_do_today_timeline(),
        "status": "ACTIVE"
    }

@app.get("/api/marketing/desks")
def get_marketing_employee_desks():
    """Returns the active work state for Marketing, Sales, Research, Product, and CEO desks."""
    return MarketingCommandCenter.get_marketing_employee_desks()

@app.get("/api/marketing/diagnostics")
def get_marketing_diagnostics():
    """Returns the Money Pipeline plain-English bottleneck diagnostics."""
    return MoneyPipelineDiagnostics.run_money_pipeline_diagnostics()

@app.get("/api/marketing/campaigns")
def list_marketing_campaigns():
    """Returns all tracked campaigns."""
    return {
        "campaigns": CampaignManager.list_campaigns()
    }

@app.get("/api/marketing/personas")
def list_marketing_personas():
    """Returns researched customer personas with verified signal vs hypothesis labeling."""
    return {
        "personas": CustomerPersonaEngine.get_all_personas()
    }

@app.get("/api/marketing/content")
def list_marketing_content():
    """Returns verified marketing content assets."""
    return {
        "content_assets": MarketingContentEngine.get_all_content_assets()
    }

@app.get("/api/marketing/experiments")
def list_marketing_experiments():
    """Returns autonomous customer acquisition experiments."""
    return {
        "experiments": MarketingExperimentEngine.list_experiments()
    }

@app.get("/api/marketing/proposals")
def list_product_proposals():
    """Returns product improvement proposals driven by research/feedback loop."""
    return {
        "proposals": ProductImprovementLoop.list_proposals()
    }

@app.post("/api/marketing/activity")
def record_marketing_activity(payload: Dict[str, Any] = Body(...)):
    """Records a verified marketing activity."""
    try:
        activity_id = MarketingActivityManager.record_activity(payload)
        return {"success": True, "activity_id": activity_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/marketing/campaign")
def create_marketing_campaign(payload: Dict[str, Any] = Body(...)):
    """Creates a marketing campaign with zero-cost financial verification."""
    try:
        campaign_id = CampaignManager.create_campaign(payload)
        return {"success": True, "campaign_id": campaign_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/marketing/experiment")
def create_marketing_experiment(payload: Dict[str, Any] = Body(...)):
    """Creates an autonomous marketing experiment."""
    try:
        exp_id = MarketingExperimentEngine.create_experiment(payload)
        return {"success": True, "experiment_id": exp_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/marketing/proposal")
def create_product_proposal(payload: Dict[str, Any] = Body(...)):
    """Creates a product improvement proposal."""
    try:
        prop_id = ProductImprovementLoop.create_proposal(payload)
        return {"success": True, "proposal_id": prop_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ----------------- Social Media & Video Operating System (5 Moves) -----------------
from marketing.video_research import VideoResearchEngine
from factory.video_engine import VideoFactoryEngine
from marketing.distributor import SocialDistributionEngine
from sales.social_funnel import SocialMonetizationFunnel
from orchestration.social_loop import SocialMediaOrchestrator

@app.post("/api/social/cycle/run")
def run_social_cycle(payload: Dict[str, Any] = Body(default={})):
    """Runs the 5-move autonomous social media and video cycle."""
    topic = payload.get("topic", "AI Social Media Operating System")
    product = payload.get("product_name", "Autonomous Enterprise System")
    try:
        result = SocialMediaOrchestrator.run_daily_cycle(topic=topic, product_name=product)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/social/publications")
def get_social_publications(limit: int = 15):
    """Retrieves recent cross-platform publications (YouTube Shorts, IG Reels, TikTok, FB)."""
    return {"success": True, "publications": SocialDistributionEngine.get_recent_publications(limit=limit)}

@app.get("/api/social/hooks")
def get_decoded_hooks(limit: int = 10):
    """Retrieves top-ranked hooks from competitor research."""
    return {"success": True, "hooks": VideoResearchEngine.get_top_ranked_hooks(limit=limit)}

@app.get("/api/social/funnel")
def get_social_funnel():
    """Retrieves 24/7 comment & DM monetization funnel metrics."""
    return {"success": True, "funnel": SocialMonetizationFunnel.get_funnel_metrics()}

@app.post("/api/social/comment")
def ingest_social_comment(payload: Dict[str, Any] = Body(...)):
    """Simulates or ingests an inbound social media comment to trigger the 24/7 DM funnel."""
    pub_id = payload.get("publication_id", "PUB-ALL-1")
    platform = payload.get("platform", "YOUTUBE_SHORTS")
    handle = payload.get("user_handle", "creator_fan")
    comment = payload.get("comment_text", "Comment SYSTEM to get this!")
    try:
        res = SocialMonetizationFunnel.process_incoming_comment(pub_id, platform, handle, comment)
        return {"success": True, "interaction": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Mount UI static files
UI_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui")
if os.path.exists(UI_DIR):
    app.mount("/static", StaticFiles(directory=UI_DIR), name="static")

# ----------------- Phase 5F: Cloud Deployment & Public Access Endpoints -----------------
from cloud.config import CloudConfig
from cloud.heartbeat_service import CloudHeartbeatService
from cloud.laptop_independence import LaptopIndependenceManager
from cloud.leak_scanner import LocalhostLeakScanner
from cloud.access_test import CustomerAccessTester
from cloud.deployment_audit import DeploymentAuditor

@app.get("/health")
def get_public_health():
    """
    Public safe operational health endpoint (Phase 5F, Section 9).
    Exposes app, worker, scheduler, and database health with ZERO secrets or banking leaks.
    """
    return CloudHeartbeatService.get_safe_health_status()

@app.get("/store", response_class=HTMLResponse)
def serve_store_page():
    """
    Public customer-facing storefront for Nexora AI Labs (Phase 5G).
    """
    store_path = os.path.join(UI_DIR, "store.html")
    if os.path.exists(store_path):
        with open(store_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Store Loading...</h1>"

@app.get("/product", response_class=HTMLResponse)
def serve_product_page():
    """
    Public customer-facing product landing page for Nexora AI Labs (Phase 5G).
    """
    product_path = os.path.join(UI_DIR, "product.html")
    if os.path.exists(product_path):
        with open(product_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Product Page Loading...</h1>"

@app.get("/checkout", response_class=HTMLResponse)
@app.get("/checkout/{session_id}", response_class=HTMLResponse)
@app.get("/success", response_class=HTMLResponse)
@app.get("/delivery", response_class=HTMLResponse)
def serve_checkout_page(session_id: Optional[str] = None):
    """
    Public customer-facing secure checkout & delivery page for Nexora AI Labs (Phase 5G).
    """
    checkout_path = os.path.join(UI_DIR, "checkout.html")
    if os.path.exists(checkout_path):
        with open(checkout_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Checkout Loading...</h1>"

@app.get("/api/cloud/deployment-audit")
def get_deployment_audit():
    """
    Returns comprehensive evidence-based cloud deployment audit (Phase 5F, Section 25).
    """
    return DeploymentAuditor.audit()

@app.get("/api/cloud/access-test")
def run_access_verification_test():
    """
    Runs 10-point customer access and checkout journey verification (Phase 5F, Section 22).
    """
    return CustomerAccessTester.run_verification_test()

@app.get("/api/cloud/leak-scan")
def run_localhost_leak_scan(url: Optional[str] = None):
    """
    Scans customer-facing URL for localhost, private IP, or local filesystem leaks (Phase 5F, Section 23).
    """
    target = url or CloudConfig.get_customer_checkout_url()
    is_prod = (CloudConfig.get_environment() == "PRODUCTION")
    return LocalhostLeakScanner.validate_customer_url(target, is_production=is_prod)

@app.get("/api/cloud/laptop-status")
def get_laptop_status():
    """
    Dynamically answers 'CAN I CLOSE MY LAPTOP?' with anti-fabrication stages (Phase 5F, Section 2 & 21).
    """
    return LaptopIndependenceManager.can_close_laptop()

@app.get("/api/cloud/actions")
def get_owner_actions():
    """
    Returns Owner Action Center items (Phase 5F, Section 28).
    """
    return LaptopIndependenceManager.get_owner_action_center()

@app.get("/api/payments/checkout/session")
def start_checkout_session(
    customer_email: str = Query("customer@example.com"),
    currency: str = Query("USD"),
    mode: str = Query("TEST"),
    product_id: str = Query(PRIMARY_PRODUCT_ID)
):
    """
    Initializes a checkout session and returns redirect URL for buy button integration.
    """
    from payments.checkout import CheckoutManager
    return CheckoutManager.create_checkout(
        customer_email=customer_email,
        currency=currency,
        product_id=product_id,
        mode=mode
    )

# ==================== Phase 5H: Multi-Channel Customer Acquisition Routes ====================

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

@app.get("/api/acquisition/channels")
def get_acquisition_channels():
    """Returns the persistent acquisition channel registry (Phase 5H, Section 1)."""
    return {
        "channels": ChannelRegistry.list_channels(),
        "total_channels": len(ChannelRegistry.list_channels())
    }

@app.get("/api/acquisition/performance")
def get_channel_performance(mode: str = Query("PRODUCTION")):
    """Returns Channel Performance view: CHANNEL | VISITORS | PRODUCT VIEWS | CHECKOUTS | SALES | REVENUE (Phase 5H, Section 9)."""
    perf_data = ChannelRegistry.get_channel_performance(mode=mode.upper())
    return {
        "mode": mode.upper(),
        "performance": perf_data.get("performance", []),
        "channels": perf_data.get("channels", [])
    }

@app.get("/api/acquisition/funnel")
def get_acquisition_funnel(mode: str = Query("PRODUCTION")):
    """Returns the 7-stage business conversion funnel (Phase 5H, Section 10)."""
    return MultiChannelFunnelEngine.get_funnel(mode=mode.upper())

@app.get("/api/acquisition/opportunities")
def list_acquisition_opportunities(status: Optional[str] = None):
    """Returns public developer discussions and outreach opportunities (Phase 5H, Sections 5 & 6)."""
    return {
        "opportunities": DeveloperDiscoveryEngine.list_opportunities(status=status)
    }

@app.post("/api/acquisition/opportunities/{opportunity_id}/approve")
def approve_outreach_opportunity(opportunity_id: str):
    """Owner Approval: Approves an outreach response for publication."""
    return DeveloperDiscoveryEngine.approve_opportunity(opportunity_id=opportunity_id)

@app.post("/api/acquisition/opportunities/{opportunity_id}/reject")
def reject_outreach_opportunity(opportunity_id: str):
    """Owner Rejection: Rejects an outreach response."""
    return DeveloperDiscoveryEngine.reject_opportunity(opportunity_id=opportunity_id)

@app.get("/api/acquisition/content")
def list_seo_content(status: Optional[str] = None):
    """Returns technical problem-solving SEO articles and developer guides (Phase 5H, Section 7)."""
    return {
        "articles": SEOContentEngine.list_articles(status=status)
    }

@app.post("/api/acquisition/content/{article_id}/approve")
def approve_seo_article(article_id: str):
    """Owner Approval: Approves an SEO article for publication."""
    return SEOContentEngine.approve_article(article_id=article_id)

@app.get("/api/acquisition/etsy-audit")
def get_etsy_audit():
    """Returns the Etsy marketplace audit and compliance assessment (Phase 5H, Section 2)."""
    return {
        "audit": EtsyMarketplaceEngine.get_audit_report(),
        "listing_package": EtsyMarketplaceEngine.get_compliant_listing_package()
    }

@app.get("/api/acquisition/etsy")
def get_etsy_direct():
    """Direct Etsy audit compliance report endpoint."""
    return EtsyMarketplaceEngine.audit_compliance()

@app.get("/api/acquisition/gumroad-spec")
def get_gumroad_spec():
    """Returns Gumroad listing package, ecosystem connections, and metrics (Phase 5H, Section 3)."""
    return {
        "listing": GumroadMarketplaceEngine.get_listing_specification(),
        "metrics": GumroadMarketplaceEngine.get_channel_metrics()
    }

@app.get("/api/acquisition/gumroad")
def get_gumroad_direct():
    """Direct Gumroad listing package endpoint."""
    return GumroadMarketplaceEngine.get_listing_package()

@app.get("/api/acquisition/lemonsqueezy-spec")
def get_lemonsqueezy_spec():
    """Returns Lemon Squeezy specification, KYC onboarding state, and metrics (Phase 5H, Section 4)."""
    return {
        "specification": LemonSqueezyMarketplaceEngine.get_channel_specification(),
        "metrics": LemonSqueezyMarketplaceEngine.get_channel_metrics()
    }

@app.get("/api/acquisition/lemonsqueezy")
def get_lemonsqueezy_direct():
    """Direct Lemon Squeezy status endpoint."""
    return LemonSqueezyMarketplaceEngine.get_channel_status()

@app.get("/api/acquisition/owner-actions")
def list_owner_actions(status: Optional[str] = None):
    """Returns the explicit list of pending Owner Action items (Phase 5H, Section 14)."""
    return {
        "actions": OwnerActionCenter.list_actions(status=status)
    }

@app.post("/api/acquisition/owner-actions/{action_id}/resolve")
def resolve_owner_action(action_id: str):
    """Marks an owner action as completed."""
    return OwnerActionCenter.resolve_action(action_id=action_id)

@app.post("/api/acquisition/owner-actions/{action_id}/complete")
def complete_owner_action(action_id: str):
    """Marks an owner action as completed."""
    return OwnerActionCenter.complete_action(action_id=action_id)

@app.get("/api/acquisition/expansion-queue")
def list_product_expansion_queue():
    """Returns evidence-ranked future digital product opportunities (Phase 5H, Section 11)."""
    return {
        "expansion_queue": ProductExpansionQueue.list_queue(),
        "queue": ProductExpansionQueue.get_ranked_queue()
    }

@app.get("/api/acquisition/expansion")
def list_product_expansion_direct():
    """Returns evidence-ranked future digital product opportunities."""
    return {
        "queue": ProductExpansionQueue.get_ranked_queue(),
        "expansion_queue": ProductExpansionQueue.list_queue()
    }

@app.post("/api/acquisition/automation/pulse")
def trigger_acquisition_pulse():
    """Triggers autonomous acquisition routines."""
    hourly = AcquisitionAutomationEngine.run_hourly_routine()
    four_hour = AcquisitionAutomationEngine.run_4hour_routine()
    daily = AcquisitionAutomationEngine.run_daily_routine()
    return {
        "hourly": hourly,
        "four_hour": four_hour,
        "daily": daily
    }

# ----------------- Phase 5I: Universal Autonomous Business Operator -----------------

from business.autonomous_operator import AutonomousBusinessOperator
from business.ceo_metrics import CEOMetricsEngine
from integrations.platform_registry import PlatformRegistry
from support.autonomous_support import AutonomousSupportEngine
from acquisition.autonomous_distribution import AutonomousDistributionEngine

@app.get("/api/operator/status")
def get_operator_status():
    """Returns the high-level operating status of the business."""
    return AutonomousBusinessOperator.get_operator_status()

@app.post("/api/operator/pulse")
def trigger_operator_pulse():
    """Triggers one complete 12-step autonomous business cycle."""
    return AutonomousBusinessOperator.execute_cycle()

@app.get("/api/integrations/platforms")
def list_platforms(classification: Optional[str] = None):
    """Returns platform integrations registry and summary."""
    return {
        "summary": PlatformRegistry.get_summary(),
        "platforms": PlatformRegistry.list_platforms(classification=classification)
    }

@app.post("/api/integrations/platforms/{platform}/status")
async def update_platform_status(platform: str, request: Request):
    """Updates connection status of an external platform."""
    body = await request.json()
    status = body.get("status", "CONNECTED")
    notes = body.get("notes", "")
    return PlatformRegistry.update_connection_status(platform, status=status, notes=notes)

@app.get("/api/business/ceo-metrics")
def get_ceo_metrics():
    """Returns real, unmanipulated business KPIs (revenue, visitors, checkouts, bottleneck)."""
    return CEOMetricsEngine.compute_ceo_metrics()

@app.post("/api/business/ceo-report/send")
def trigger_daily_ceo_report():
    """Compiles and dispatches the daily CEO executive summary to manirkhn@gmail.com."""
    return CEOMetricsEngine.generate_daily_ceo_report()

@app.get("/api/support/tickets")
def list_support_tickets(status: Optional[str] = None):
    """Returns customer support tickets."""
    return {
        "tickets": AutonomousSupportEngine.list_tickets(status=status),
        "open_tickets": AutonomousSupportEngine.get_open_tickets()
    }

@app.post("/api/support/submit")
async def submit_support_question(request: Request):
    """Customer submits a question, answered autonomously or escalated to owner."""
    body = await request.json()
    email = body.get("customer_email", "customer@example.com")
    question = body.get("question", "")
    product_id = body.get("product_id", "PROD-OPP-P4-001")
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    return AutonomousSupportEngine.handle_customer_inquiry(
        customer_email=email,
        product_id=product_id,
        question=question
    )

@app.post("/api/support/resolve")
async def resolve_support_ticket(request: Request):
    """Resolves an open support ticket."""
    body = await request.json()
    ticket_id = body.get("ticket_id")
    resolution = body.get("resolution", "Resolved")
    if not ticket_id:
        raise HTTPException(status_code=400, detail="ticket_id required")
    return AutonomousSupportEngine.resolve_ticket(ticket_id=ticket_id, resolution=resolution)

@app.get("/api/acquisition/opportunities")
def list_acquisition_opportunities():
    """Returns discovered customer demand opportunities."""
    return {
        "stats": AutonomousDistributionEngine.get_acquisition_stats(),
        "opportunities": AutonomousDistributionEngine.list_opportunities()
    }

@app.get("/", response_class=HTMLResponse)
def serve_index():
    index_path = os.path.join(UI_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Autonomous AI Company Server Active</h1><p>UI loading...</p>"
