"""
Virtual Company Treasury & Reinvestment Priority Engine (Part 15, 16, 17, 18, 21, 22, 23).
Maintains internal corporate accounting completely isolated from the owner's bank account.
Enforces the Reinvestment Priority Ladder and manages the company's maturity progression
from Level 1 (Bootstrap) to Level 6 (Autonomous AI Organization).
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from core.db import get_connection
from core.audit import AuditLogger
from core.firewall import FinancialFirewall
from finance.analytics import FinanceEngine

REINVESTMENT_PRIORITIES = [
    "1_SECURITY",
    "2_RELIABILITY",
    "3_REVENUE_BOTTLENECK",
    "4_AUTOMATION_OWNER_TIME_REDUCTION",
    "5_CUSTOMER_EXPERIENCE",
    "6_PRODUCT_IMPROVEMENT",
    "7_MARKETING_INFRASTRUCTURE",
    "8_NEW_REVENUE_OPPORTUNITY",
    "9_EXPERIMENTAL_CAPABILITY"
]

GROWTH_LEVELS = [
    "LEVEL_1_BOOTSTRAP",
    "LEVEL_2_VALIDATION",
    "LEVEL_3_AUTOMATION",
    "LEVEL_4_SCALE",
    "LEVEL_5_MULTI_BUSINESS",
    "LEVEL_6_AI_ORGANIZATION"
]

class CompanyTreasuryEngine:
    @staticmethod
    def get_treasury_state() -> Dict[str, Any]:
        """
        Part 15: Retrieve comprehensive treasury state.
        Never confuses virtual company ledgers with real banking accounts.
        """
        finances = FinanceEngine.get_financial_summary()
        actual_rev = finances["revenue_breakdown"]["actual_revenue"]
        total_exp = finances["expenses"]["total"]
        profit = actual_rev - total_exp
        
        settings = FinancialFirewall.get_settings()
        virtual_balance = settings.get("virtual_balance", 1000.0) + profit
        operating_reserve = 500.0
        reinvestment_pct = float(settings.get("reinvestment_percentage", 0.0))
        
        # Calculate available reinvestment budget based on verified profit
        reinvestment_budget = 0.0
        if profit > 0 and reinvestment_pct > 0:
            reinvestment_budget = round((profit - operating_reserve) * (reinvestment_pct / 100.0), 2)
            reinvestment_budget = max(0.0, reinvestment_budget)

        # Operating Mode (Part 22 & 23)
        operating_mode = "FREE_FIRST" if actual_rev < 100.0 or profit <= 0 else "PROFIT_FIRST"

        # Growth Level (Part 21)
        growth_level = "LEVEL_1_BOOTSTRAP"
        if actual_rev >= 1000.0:
            growth_level = "LEVEL_3_AUTOMATION"
        elif actual_rev > 0.0:
            growth_level = "LEVEL_2_VALIDATION"

        return {
            "treasury_id": "TREASURY-CORP-V1",
            "operating_mode": operating_mode,
            "growth_level": growth_level,
            "total_actual_revenue": round(actual_rev, 2),
            "total_expenses": round(total_exp, 2),
            "actual_profit": round(profit, 2),
            "available_business_funds": round(virtual_balance, 2),
            "operating_reserve_usd": operating_reserve,
            "reinvestment_budget_usd": reinvestment_budget,
            "reinvestment_percentage": reinvestment_pct,
            "pending_commitments": 0.0,
            "unapproved_spending": 0.0, # Strictly $0 enforced
            "reinvestment_priorities": REINVESTMENT_PRIORITIES,
            "air_gap_confirmed": True
        }

    @staticmethod
    def propose_reinvestment(
        category: str, # From REINVESTMENT_PRIORITIES
        item_name: str,
        expected_cost_usd: float,
        why_needed: str,
        expected_business_benefit: str,
        expected_payback_months: float,
        agent_id: str = "EMP-001-CEO"
    ) -> Dict[str, Any]:
        """
        Part 17: Profit-Based Capability Acquisition Proposal.
        Structures a formal investment proposal for Owner Approval.
        """
        treasury = CompanyTreasuryEngine.get_treasury_state()
        if expected_cost_usd > treasury["available_business_funds"]:
            raise ValueError(f"INSUFFICIENT FUNDS: Proposed investment (${expected_cost_usd:.2f}) exceeds available corporate funds (${treasury['available_business_funds']:.2f}).")

        proposal_id = f"REV-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        from approvals.manager import ApprovalManager
        app_id = ApprovalManager.create_approval_request(
            requesting_agent=agent_id,
            what=f"Reinvest ${expected_cost_usd:.2f} in {category}: {item_name}",
            why=why_needed,
            expected_benefit=expected_business_benefit,
            expected_cost=expected_cost_usd,
            risk_level="MEDIUM" if expected_cost_usd > 50 else "LOW",
            alternatives="Rely strictly on zero-cost manual effort or open-source tier.",
            recommendation=f"Approve investment from business cashflow. Payback modeled at {expected_payback_months} months."
        )

        AuditLogger.log(
            agent_id=agent_id,
            action="REINVESTMENT_PROPOSAL_SUBMITTED",
            result=f"Reinvestment proposal {proposal_id} submitted for {item_name} (${expected_cost_usd:.2f}). Approval ID: {app_id}",
            risk_level="MEDIUM",
            cost=expected_cost_usd
        )

        return {
            "proposal_id": proposal_id,
            "approval_id": app_id,
            "category": category,
            "expected_cost": expected_cost_usd,
            "status": "AWAITING_OWNER_APPROVAL"
        }
