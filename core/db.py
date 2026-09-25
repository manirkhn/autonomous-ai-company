"""
Database Layer for Autonomous AI Company.
Uses SQLite for zero-dependency, local, reliable persistence.
"""

import sqlite3
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.path.dirname(DB_DIR), "data", "company.db")

def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Employees Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        employee_id TEXT PRIMARY KEY,
        role TEXT NOT NULL,
        purpose TEXT NOT NULL,
        responsibilities TEXT NOT NULL,
        capabilities TEXT NOT NULL,
        tools TEXT NOT NULL,
        permissions TEXT NOT NULL,
        current_tasks TEXT NOT NULL,
        status TEXT NOT NULL,
        performance_metrics TEXT NOT NULL,
        cost REAL DEFAULT 0.0,
        created_date TEXT NOT NULL,
        last_review TEXT NOT NULL,
        instructions TEXT NOT NULL,
        escalation_rules TEXT NOT NULL
    );
    """)

    # 2. Tasks Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        task_id TEXT PRIMARY KEY,
        creator TEXT NOT NULL,
        assigned_agent TEXT NOT NULL,
        objective TEXT NOT NULL,
        description TEXT NOT NULL,
        priority TEXT NOT NULL,
        deadline TEXT,
        dependencies TEXT,
        required_tools TEXT,
        status TEXT NOT NULL,
        result TEXT,
        evidence TEXT,
        errors TEXT,
        approval_requirement INTEGER DEFAULT 0,
        approval_status TEXT DEFAULT 'NONE',
        timestamp TEXT NOT NULL,
        cost REAL DEFAULT 0.0,
        revenue_impact REAL DEFAULT 0.0
    );
    """)

    # 3. Approvals Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS approvals (
        approval_id TEXT PRIMARY KEY,
        task_id TEXT,
        requesting_agent TEXT NOT NULL,
        what TEXT NOT NULL,
        why TEXT NOT NULL,
        expected_benefit TEXT NOT NULL,
        expected_cost REAL DEFAULT 0.0,
        risk_level TEXT NOT NULL,
        alternatives TEXT NOT NULL,
        recommendation TEXT NOT NULL,
        deadline TEXT,
        status TEXT NOT NULL,
        owner_notes TEXT,
        created_at TEXT NOT NULL,
        resolved_at TEXT
    );
    """)

    # 4. Corporate Memory Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memory (
        memory_id TEXT PRIMARY KEY,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        metadata TEXT,
        tags TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # 5. Opportunities Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS opportunities (
        opportunity_id TEXT PRIMARY KEY,
        customer_problem TEXT NOT NULL,
        target_customer TEXT NOT NULL,
        proposed_solution TEXT NOT NULL,
        competitors TEXT,
        demand_evidence TEXT,
        estimated_price REAL DEFAULT 0.0,
        estimated_costs REAL DEFAULT 0.0,
        estimated_automation_potential REAL DEFAULT 0.0,
        estimated_human_involvement REAL DEFAULT 0.0,
        platform_risks TEXT,
        legal_compliance TEXT,
        mvp_requirements TEXT,
        validation_method TEXT,
        expected_time_to_test TEXT,
        actual_results TEXT,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    # 6. Experiments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS experiments (
        experiment_id TEXT PRIMARY KEY,
        opportunity_id TEXT,
        title TEXT NOT NULL,
        hypothesis TEXT NOT NULL,
        success_metric TEXT NOT NULL,
        mvp_description TEXT NOT NULL,
        status TEXT NOT NULL,
        results TEXT,
        retry_reason TEXT,
        created_at TEXT NOT NULL,
        closed_at TEXT
    );
    """)

    # 7. Financial Transactions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS financial_transactions (
        transaction_id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        description TEXT NOT NULL,
        approved_by TEXT,
        timestamp TEXT NOT NULL,
        is_virtual INTEGER DEFAULT 1
    );
    """)

    # 8. Audit Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        log_id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        agent_id TEXT NOT NULL,
        action TEXT NOT NULL,
        result TEXT NOT NULL,
        risk_level TEXT NOT NULL,
        cost REAL DEFAULT 0.0,
        details TEXT
    );
    """)

    # 9. Owner Interventions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS owner_interventions (
        intervention_id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        context TEXT NOT NULL,
        reason_needed TEXT NOT NULL,
        can_be_automated INTEGER DEFAULT 0,
        missing_capability TEXT,
        missing_tool TEXT,
        new_skill_needed TEXT,
        status TEXT DEFAULT 'RECORDED'
    );
    """)

    # 10. Company Settings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS company_settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        description TEXT,
        updated_at TEXT NOT NULL
    );
    """)

    # 11. Products Table (Product Factory Pipeline)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id TEXT PRIMARY KEY,
        opportunity_id TEXT,
        name TEXT NOT NULL,
        asset_type TEXT NOT NULL,
        version TEXT NOT NULL,
        requirements TEXT NOT NULL,
        mvp_path TEXT,
        qa_status TEXT DEFAULT 'PENDING',
        qa_evidence TEXT,
        listing_copy TEXT,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # 12. Sales Leads Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales_leads (
        lead_id TEXT PRIMARY KEY,
        product_id TEXT,
        source TEXT NOT NULL,
        customer_type TEXT NOT NULL,
        problem TEXT NOT NULL,
        contact_method TEXT NOT NULL,
        status TEXT NOT NULL,
        consent_basis TEXT NOT NULL,
        outcome TEXT,
        next_action TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # 13. Deliveries Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deliveries (
        delivery_id TEXT PRIMARY KEY,
        order_id TEXT NOT NULL,
        product_id TEXT NOT NULL,
        customer_ref TEXT NOT NULL,
        status TEXT NOT NULL,
        verification_evidence TEXT NOT NULL,
        timestamp TEXT NOT NULL
    );
    """)

    # 14. Customer Feedback Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customer_feedback (
        feedback_id TEXT PRIMARY KEY,
        product_id TEXT NOT NULL,
        customer_ref TEXT NOT NULL,
        feedback_type TEXT NOT NULL,
        content TEXT NOT NULL,
        resolution TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # 15. Capability Gaps Table (Future Self-Growth Preparation)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS capability_gaps (
        gap_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        why_required TEXT NOT NULL,
        frequency TEXT NOT NULL,
        expected_business_impact TEXT NOT NULL,
        free_tools TEXT,
        oss_options TEXT,
        free_tiers TEXT,
        paid_options TEXT,
        estimated_cost REAL DEFAULT 0.0,
        expected_roi TEXT,
        owner_time_saved REAL DEFAULT 0.0,
        risk TEXT NOT NULL,
        status TEXT DEFAULT 'IDENTIFIED',
        created_at TEXT NOT NULL
    );
    """)

    # 16. Safe Schema Migrations for Phase 2 columns on opportunities
    cursor.execute("PRAGMA table_info(opportunities)")
    existing_opp_cols = [row[1] for row in cursor.fetchall()]
    
    new_opp_cols = [
        ("name", "TEXT DEFAULT ''"),
        ("customer_segment", "TEXT DEFAULT ''"),
        ("business_model", "TEXT DEFAULT ''"),
        ("existing_alternatives", "TEXT DEFAULT ''"),
        ("search_evidence", "TEXT DEFAULT ''"),
        ("customer_pain_evidence", "TEXT DEFAULT ''"),
        ("evidence_classification", "TEXT DEFAULT 'UNKNOWN'"),
        ("price_range", "TEXT DEFAULT ''"),
        ("expected_gross_margin", "REAL DEFAULT 0.0"),
        ("human_time_requirement", "REAL DEFAULT 0.0"),
        ("technical_complexity", "TEXT DEFAULT 'LOW'"),
        ("time_to_mvp", "TEXT DEFAULT ''"),
        ("platform_dependency", "TEXT DEFAULT 'NONE'"),
        ("legal_compliance_risk", "TEXT DEFAULT 'LOW'"),
        ("refund_risk", "TEXT DEFAULT 'LOW'"),
        ("customer_support_burden", "TEXT DEFAULT 'LOW'"),
        ("scalability", "TEXT DEFAULT 'HIGH'"),
        ("recurring_revenue_potential", "TEXT DEFAULT 'LOW'"),
        ("success_metric", "TEXT DEFAULT ''"),
        ("failure_condition", "TEXT DEFAULT ''"),
        ("source_links", "TEXT DEFAULT '[]'"),
        ("date_researched", "TEXT DEFAULT ''"),
        ("research_confidence", "REAL DEFAULT 0.0"),
        ("composite_score", "REAL DEFAULT 0.0")
    ]
    for col_name, col_type in new_opp_cols:
        if col_name not in existing_opp_cols:
            cursor.execute(f"ALTER TABLE opportunities ADD COLUMN {col_name} {col_type};")

    # Safe Schema Migrations for financial_transactions (transaction status)
    cursor.execute("PRAGMA table_info(financial_transactions)")
    existing_tx_cols = [row[1] for row in cursor.fetchall()]
    if "tx_status" not in existing_tx_cols:
        cursor.execute("ALTER TABLE financial_transactions ADD COLUMN tx_status TEXT DEFAULT 'ACTUAL';")

    # 17. AI Skills Registry Table (Part 5)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS skills (
        skill_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        version TEXT NOT NULL,
        purpose TEXT NOT NULL,
        inputs TEXT NOT NULL,
        outputs TEXT NOT NULL,
        tools TEXT NOT NULL,
        permissions TEXT NOT NULL,
        dependencies TEXT,
        instructions TEXT NOT NULL,
        tests TEXT NOT NULL,
        security_rules TEXT NOT NULL,
        cost REAL DEFAULT 0.0,
        owner_time_saved REAL DEFAULT 0.0,
        business_value TEXT NOT NULL,
        performance TEXT,
        created_date TEXT NOT NULL,
        last_updated TEXT NOT NULL,
        status TEXT NOT NULL
    );
    """)

    # 18. Virtual Company Treasury Table (Part 15)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS company_treasury (
        treasury_id TEXT PRIMARY KEY,
        total_revenue REAL DEFAULT 0.0,
        total_expenses REAL DEFAULT 0.0,
        available_business_funds REAL DEFAULT 1000.0,
        operating_reserve REAL DEFAULT 500.0,
        reinvestment_budget REAL DEFAULT 0.0,
        pending_commitments REAL DEFAULT 0.0,
        approved_spending REAL DEFAULT 0.0,
        unapproved_spending REAL DEFAULT 0.0,
        profit REAL DEFAULT 0.0,
        operating_mode TEXT DEFAULT 'FREE_FIRST',
        growth_level TEXT DEFAULT 'LEVEL_1_BOOTSTRAP',
        updated_at TEXT NOT NULL
    );
    """)

    # 19. Capability Marketplace Catalog (Part 24)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS capability_marketplace (
        item_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        provider TEXT NOT NULL,
        type TEXT NOT NULL,
        is_paid INTEGER DEFAULT 0,
        cost REAL DEFAULT 0.0,
        dependencies TEXT,
        reliability REAL DEFAULT 1.0,
        security_score REAL DEFAULT 1.0,
        permissions TEXT,
        setup_time TEXT,
        maintenance TEXT,
        business_value TEXT,
        status TEXT DEFAULT 'AVAILABLE'
    );
    """)

    # Safe Schema Migrations for capability_gaps (Part 4)
    cursor.execute("PRAGMA table_info(capability_gaps)")
    existing_gap_cols = [row[1] for row in cursor.fetchall()]
    new_gap_cols = [
        ("capability_name", "TEXT DEFAULT ''"),
        ("detected_by", "TEXT DEFAULT 'EMP-012-AUTOMATION'"),
        ("business_objective", "TEXT DEFAULT ''"),
        ("current_workaround", "TEXT DEFAULT ''"),
        ("owner_time_required", "REAL DEFAULT 0.0"),
        ("current_cost", "REAL DEFAULT 0.0"),
        ("expected_benefit", "TEXT DEFAULT ''"),
        ("urgency", "TEXT DEFAULT 'MEDIUM'"),
        ("free_tier_options", "TEXT DEFAULT '[]'"),
        ("build_internal_option", "TEXT DEFAULT ''"),
        ("recommended_approach", "TEXT DEFAULT ''"),
        ("approval_required", "INTEGER DEFAULT 1")
    ]
    for col_name, col_type in new_gap_cols:
        if col_name not in existing_gap_cols:
            cursor.execute(f"ALTER TABLE capability_gaps ADD COLUMN {col_name} {col_type};")

    # ----------------- Phase 4: Revenue Engine Tables -----------------

    # 20. Revenue Ledger Table (Part 17)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS revenue_ledger (
        revenue_id TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL,
        product_id TEXT NOT NULL,
        order_id TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT DEFAULT 'USD',
        payment_status TEXT NOT NULL,
        payment_provider TEXT NOT NULL,
        fees REAL DEFAULT 0.0,
        refund_amount REAL DEFAULT 0.0,
        net_revenue REAL NOT NULL,
        date TEXT NOT NULL,
        source TEXT NOT NULL,
        verification_status TEXT NOT NULL,
        evidence TEXT
    );
    """)

    # 21. Outreach Campaigns Table (Part 13)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS outreach_campaigns (
        campaign_id TEXT PRIMARY KEY,
        target_definition TEXT NOT NULL,
        source TEXT NOT NULL,
        consent_or_legal_basis TEXT NOT NULL,
        message TEXT NOT NULL,
        frequency_limit TEXT NOT NULL,
        opt_out_method TEXT NOT NULL,
        suppression_list TEXT DEFAULT '[]',
        channel TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT,
        owner_approval INTEGER DEFAULT 0,
        status TEXT DEFAULT 'DRAFT',
        created_at TEXT NOT NULL
    );
    """)

    # 22. Customer Support Tickets Table (Part 22)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customer_support_tickets (
        ticket_id TEXT PRIMARY KEY,
        customer_ref TEXT NOT NULL,
        order_id TEXT,
        issue_type TEXT NOT NULL,
        content TEXT NOT NULL,
        resolution TEXT,
        status TEXT DEFAULT 'OPEN',
        escalated_to_owner INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # 23. Refund Records Table (Part 23)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS refund_records (
        refund_id TEXT PRIMARY KEY,
        order_id TEXT NOT NULL,
        customer_id TEXT NOT NULL,
        product_id TEXT NOT NULL,
        amount REAL NOT NULL,
        reason TEXT NOT NULL,
        status TEXT DEFAULT 'REQUESTED',
        owner_notes TEXT,
        created_at TEXT NOT NULL,
        resolved_at TEXT
    );
    """)

    # 24. Launch Readiness Reports Table (Part 34)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS launch_readiness_reports (
        report_id TEXT PRIMARY KEY,
        product_id TEXT NOT NULL,
        opportunity_id TEXT NOT NULL,
        title TEXT NOT NULL,
        product_readiness TEXT NOT NULL,
        qa_results TEXT NOT NULL,
        security_results TEXT NOT NULL,
        pricing REAL DEFAULT 0.0,
        target_customer TEXT NOT NULL,
        acquisition_channel TEXT NOT NULL,
        evidence TEXT NOT NULL,
        legal_compliance TEXT NOT NULL,
        expected_cost REAL DEFAULT 0.0,
        owner_actions_required TEXT,
        requested_permissions TEXT,
        requested_spending REAL DEFAULT 0.0,
        rollback_plan TEXT NOT NULL,
        approval_status TEXT DEFAULT 'PENDING_OWNER_APPROVAL',
        created_at TEXT NOT NULL
    );
    """)

    # Safe Schema Migrations for Phase 4 columns on opportunities
    cursor.execute("PRAGMA table_info(opportunities)")
    existing_opp_cols_p4 = [row[1] for row in cursor.fetchall()]
    new_opp_cols_p4 = [
        ("geography", "TEXT DEFAULT 'Global / Remote'"),
        ("distribution_channel", "TEXT DEFAULT 'Organic / Direct'"),
        ("existing_solutions", "TEXT DEFAULT ''"),
        ("competitor_prices", "TEXT DEFAULT ''"),
        ("evidence_sources", "TEXT DEFAULT '[]'"),
        ("evidence_type", "TEXT DEFAULT 'OBSERVED_SIGNAL'"),
        ("evidence_date", "TEXT DEFAULT ''"),
        ("demand_signals", "TEXT DEFAULT ''"),
        ("pain_signals", "TEXT DEFAULT ''"),
        ("search_signals", "TEXT DEFAULT ''"),
        ("competition_level", "TEXT DEFAULT 'MODERATE'"),
        ("estimated_customer_value", "REAL DEFAULT 0.0"),
        ("estimated_cost", "REAL DEFAULT 0.0"),
        ("estimated_margin", "REAL DEFAULT 0.0"),
        ("estimated_owner_time", "REAL DEFAULT 0.0"),
        ("automation_percentage", "REAL DEFAULT 0.9"),
        ("distribution_difficulty", "TEXT DEFAULT 'LOW'"),
        ("legal_risk", "TEXT DEFAULT 'LOW'"),
        ("platform_risk", "TEXT DEFAULT 'LOW'"),
        ("support_burden", "TEXT DEFAULT 'LOW'"),
        ("time_to_first_customer_estimate", "TEXT DEFAULT '7 days'"),
        ("capital_required", "REAL DEFAULT 0.0"),
        ("recurring_cost", "REAL DEFAULT 0.0"),
        ("confidence_score", "REAL DEFAULT 0.8"),
        ("evidence_quality_score", "REAL DEFAULT 0.85"),
        ("opportunity_score", "REAL DEFAULT 0.8")
    ]
    for col_name, col_type in new_opp_cols_p4:
        if col_name not in existing_opp_cols_p4:
            cursor.execute(f"ALTER TABLE opportunities ADD COLUMN {col_name} {col_type};")

    # ----------------- Phase 5B: 24/7 Cloud, Reports & Activity Tables -----------------

    # 25. Employee Activities Table (Requirements 14, 15, 29)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employee_activities (
        activity_id TEXT PRIMARY KEY,
        employee_id TEXT NOT NULL,
        employee_name TEXT NOT NULL,
        role TEXT NOT NULL,
        task_id TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT,
        status TEXT NOT NULL,
        project TEXT,
        experiment TEXT,
        product TEXT,
        campaign TEXT,
        module TEXT,
        external_platform TEXT,
        action TEXT NOT NULL,
        result TEXT,
        error TEXT,
        handoff TEXT,
        owner_intervention INTEGER DEFAULT 0
    );
    """)

    # 26. Heartbeat Logs Table (Requirements 6, 12)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS heartbeat_logs (
        log_id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        overall_status TEXT NOT NULL,
        components TEXT NOT NULL
    );
    """)

    # 27. Daily CEO Reports Table (Requirements 16, 31, 34)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ceo_reports (
        report_id TEXT PRIMARY KEY,
        date TEXT NOT NULL,
        timezone TEXT NOT NULL,
        generated_at TEXT NOT NULL,
        facts TEXT NOT NULL,
        summary TEXT NOT NULL,
        full_content_md TEXT NOT NULL,
        status TEXT NOT NULL,
        validation_status TEXT NOT NULL
    );
    """)

    # 28. Email Deliveries Table (Requirements 17, 18, 35, 36)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS email_deliveries (
        delivery_id TEXT PRIMARY KEY,
        report_id TEXT NOT NULL,
        recipient TEXT NOT NULL,
        subject TEXT NOT NULL,
        provider TEXT NOT NULL,
        status TEXT NOT NULL,
        message_id TEXT,
        error TEXT,
        timestamp TEXT NOT NULL
    );
    """)

    # ----------------- Phase 5D: Secure Payments, Checkout & Owner Settlement -----------------

    # 29. Owner Settlement Profile Table (Non-secret configuration only)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS owner_settlement_profile (
        profile_id TEXT PRIMARY KEY,
        country TEXT NOT NULL DEFAULT 'AE',
        bank_name TEXT NOT NULL DEFAULT 'Emirates Islamic',
        settlement_currency TEXT NOT NULL DEFAULT 'AED',
        account_type TEXT NOT NULL DEFAULT 'business',
        settlement_destination_status TEXT NOT NULL DEFAULT 'CONFIGURED',
        payment_provider TEXT NOT NULL DEFAULT 'STRIPE_UAE',
        masked_destination_reference TEXT NOT NULL DEFAULT '****1234',
        owner_approval_status TEXT NOT NULL DEFAULT 'APPROVED',
        updated_at TEXT NOT NULL
    );
    """)

    # 30. Payment Transactions Table (Deterministic payment state machine & test/prod isolation)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payment_transactions (
        transaction_id TEXT PRIMARY KEY,
        order_id TEXT NOT NULL,
        mode TEXT NOT NULL DEFAULT 'TEST',
        product_id TEXT NOT NULL,
        product_name TEXT NOT NULL,
        customer_email TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL DEFAULT 'USD',
        provider TEXT NOT NULL DEFAULT 'STRIPE_UAE',
        provider_payment_id TEXT,
        payment_status TEXT NOT NULL,
        provider_fee REAL DEFAULT 0.0,
        net_amount REAL DEFAULT 0.0,
        webhook_verified INTEGER DEFAULT 0,
        idempotency_key TEXT,
        delivery_status TEXT DEFAULT 'PENDING',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        evidence TEXT
    );
    """)

    # 31. Settlements Table (Tracks actual payouts from payment provider to designated bank)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settlements (
        settlement_id TEXT PRIMARY KEY,
        provider TEXT NOT NULL,
        settlement_amount REAL NOT NULL,
        currency TEXT NOT NULL DEFAULT 'AED',
        settlement_date TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'SETTLEMENT_PENDING',
        masked_destination_reference TEXT NOT NULL,
        provider_reference TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # 32. Payment Approval Gates Table (Owner controls for provider activation, refunds, etc.)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payment_approval_gates (
        gate_key TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        is_approved INTEGER DEFAULT 0,
        approved_by TEXT,
        approved_at TEXT,
        notes TEXT
    );
    """)

    # 33. Processed Webhook Events Table (Idempotency and anti-replay protection)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS processed_webhook_events (
        event_id TEXT PRIMARY KEY,
        provider TEXT NOT NULL,
        event_type TEXT NOT NULL,
        processed_at TEXT NOT NULL,
        payload_hash TEXT
    );
    """)

    # ----------------- Phase 5E: Sales, Marketing & Customer Acquisition -----------------

    # 34. Real Marketing Activities Log (Sections 5 & 6)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS marketing_activities (
        activity_id TEXT PRIMARY KEY,
        campaign_id TEXT,
        employee_id TEXT NOT NULL,
        employee_name TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        channel TEXT NOT NULL,
        platform TEXT NOT NULL,
        target_persona TEXT NOT NULL,
        activity_type TEXT NOT NULL,
        content_reference TEXT,
        destination_url TEXT,
        execution_status TEXT NOT NULL,
        approval_status TEXT DEFAULT 'APPROVED',
        result TEXT NOT NULL,
        evidence_reference TEXT NOT NULL,
        impressions_verified INTEGER DEFAULT 0,
        clicks_verified INTEGER DEFAULT 0,
        visits_verified INTEGER DEFAULT 0,
        leads_verified INTEGER DEFAULT 0,
        purchases_verified INTEGER DEFAULT 0,
        spend REAL DEFAULT 0.0,
        currency TEXT DEFAULT 'USD',
        execution_env TEXT DEFAULT 'LOCAL'
    );
    """)

    # 35. Marketing Campaigns Table (Section 9)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS marketing_campaigns (
        campaign_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        objective TEXT NOT NULL,
        product_id TEXT NOT NULL,
        target_persona TEXT NOT NULL,
        target_problem TEXT NOT NULL,
        channel TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT,
        budget REAL DEFAULT 0.0,
        spend REAL DEFAULT 0.0,
        status TEXT NOT NULL DEFAULT 'PLANNED',
        owner_approval INTEGER DEFAULT 0,
        employee_owner TEXT NOT NULL,
        experiment_hypothesis TEXT,
        success_metric TEXT,
        result TEXT,
        next_action TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # 36. Customer Personas Table (Section 11)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customer_personas (
        persona_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        target_problem TEXT NOT NULL,
        evidence_type TEXT NOT NULL DEFAULT 'HYPOTHESIS',
        evidence_notes TEXT NOT NULL,
        likely_use_case TEXT NOT NULL,
        relevant_channel TEXT NOT NULL,
        acquisition_method TEXT NOT NULL,
        objections TEXT,
        offer_angle TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    # 37. Marketing Experiments Table (Section 18)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS marketing_experiments (
        experiment_id TEXT PRIMARY KEY,
        hypothesis TEXT NOT NULL,
        problem TEXT NOT NULL,
        channel TEXT NOT NULL,
        action TEXT NOT NULL,
        expected_signal TEXT NOT NULL,
        actual_result TEXT,
        start_date TEXT NOT NULL,
        end_date TEXT,
        spend REAL DEFAULT 0.0,
        outcome TEXT,
        status TEXT DEFAULT 'RUNNING',
        decision TEXT DEFAULT 'CONTINUE',
        created_at TEXT NOT NULL
    );
    """)

    # 38. Product Improvement Proposals Table (Section 24)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product_improvement_proposals (
        proposal_id TEXT PRIMARY KEY,
        product_id TEXT NOT NULL,
        customer_problem TEXT NOT NULL,
        evidence TEXT NOT NULL,
        proposed_change TEXT NOT NULL,
        expected_benefit TEXT NOT NULL,
        status TEXT DEFAULT 'PROPOSED',
        actual_outcome TEXT,
        created_at TEXT NOT NULL,
        resolved_at TEXT
    );
    """)

    # Column migrations if table existed previously without new columns
    try:
        cursor.execute("ALTER TABLE product_improvement_proposals ADD COLUMN actual_outcome TEXT")
    except Exception:
        pass

    try:
        cursor.execute("ALTER TABLE marketing_experiments ADD COLUMN status TEXT DEFAULT 'RUNNING'")
    except Exception:
        pass

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)
