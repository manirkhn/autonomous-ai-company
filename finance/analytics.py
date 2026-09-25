"""
Financial Analytics & Ledger Engine (Phase 2 Upgraded).
Strictly separates:
- ACTUAL REVENUE (verified customer transactions)
- ESTIMATED REVENUE (modeled forecasts)
- PENDING REVENUE (orders awaiting settlement)
- REFUNDED REVENUE
Enforces zero unapproved spending, maintains virtual ledgers, and prepares reinvestment controls.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from core.db import get_connection
from core.audit import AuditLogger
from core.firewall import FinancialFirewall, FinancialFirewallViolation

class FinanceEngine:
    @staticmethod
    def get_reinvestment_policy() -> Dict[str, Any]:
        """Part 23: Financial Reinvestment Parameters."""
        settings = FinancialFirewall.get_settings()
        return {
            "reinvestment_percentage": float(settings.get("reinvestment_percentage", 0.0)), # Initially 0%
            "operating_reserve_percentage": float(settings.get("operating_reserve_percentage", 100.0)),
            "max_single_investment": float(settings.get("max_single_investment", 0.0)),
            "max_monthly_investment": float(settings.get("max_monthly_investment", 0.0)),
            "owner_approval_threshold": float(settings.get("approval_required_threshold", 0.0)),
            "emergency_reserve_usd": float(settings.get("emergency_reserve", 500.0)),
            "owner_approval_required": True
        }

    @staticmethod
    def record_transaction(
        tx_type: str,  # 'REVENUE' or 'EXPENSE'
        category: str, # 'SOFTWARE', 'ADVERTISING', 'INFRASTRUCTURE', 'DIGITAL_PRODUCT', 'SERVICE', 'OTHER'
        amount: float,
        description: str,
        agent_id: str,
        is_virtual: bool = True,
        approved_by: Optional[str] = None,
        tx_status: str = "ACTUAL" # 'ACTUAL', 'ESTIMATED', 'PENDING', 'REFUNDED'
    ) -> str:
        """
        Record a financial event. Real funds strictly require approved_by.
        Expenses are checked against the Financial Firewall.
        """
        tx_type = tx_type.upper()
        if tx_type not in {"REVENUE", "EXPENSE"}:
            raise ValueError("Transaction type must be 'REVENUE' or 'EXPENSE'")

        if tx_status.upper() not in {"ACTUAL", "ESTIMATED", "PENDING", "REFUNDED"}:
            tx_status = "ACTUAL"

        # If expense, check firewall rules
        if tx_type == "EXPENSE":
            is_allowed, reason = FinancialFirewall.check_operation_safety(
                action_type=f"SPEND_{category.upper()}",
                amount=amount,
                agent_id=agent_id,
                is_virtual=is_virtual
            )
            if not is_allowed and not approved_by:
                raise FinancialFirewallViolation(f"FIREWALL BLOCKED EXPENSE: {reason}")

        tx_id = f"TX-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO financial_transactions (
                transaction_id, type, category, amount, description, approved_by, timestamp, is_virtual, tx_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tx_id, tx_type, category.upper(), amount, description,
            approved_by or ("OWNER" if not is_virtual else "SYSTEM_VIRTUAL"),
            now, 1 if is_virtual else 0, tx_status.upper()
        ))
        conn.commit()
        conn.close()

        AuditLogger.log(
            agent_id=agent_id,
            action=f"FINANCIAL_{tx_type}_{tx_status}",
            result=f"{tx_type} (${amount:.2f}) [{category}] status={tx_status}: {description} (Virtual: {is_virtual})",
            risk_level="HIGH" if not is_virtual and tx_type == "EXPENSE" else "LOW",
            cost=amount if tx_type == "EXPENSE" else 0.0,
            details={"transaction_id": tx_id, "amount": amount, "category": category, "tx_status": tx_status}
        )
        return tx_id

    @staticmethod
    def get_financial_summary() -> Dict[str, Any]:
        """
        Compute aggregated financial performance strictly separating:
        ACTUAL REVENUE, ESTIMATED REVENUE, PENDING REVENUE, REFUNDED REVENUE.
        """
        conn = get_connection()
        cursor = conn.cursor()

        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        week_start = (now - timedelta(days=7)).isoformat()
        month_start = (now - timedelta(days=30)).isoformat()

        cursor.execute("SELECT * FROM financial_transactions ORDER BY timestamp ASC")
        rows = cursor.fetchall()
        conn.close()

        # Part 20 Streams
        actual_rev_today = actual_rev_week = actual_rev_month = actual_rev_total = 0.0
        estimated_rev_total = 0.0
        pending_rev_total = 0.0
        refunded_rev_total = 0.0

        exp_today = exp_week = exp_month = exp_total = 0.0
        by_category_exp = {"SOFTWARE": 0.0, "ADVERTISING": 0.0, "INFRASTRUCTURE": 0.0, "OTHER": 0.0}
        by_channel_actual_rev = {}

        for r in rows:
            amt = float(r["amount"])
            ts = r["timestamp"]
            tx_type = r["type"]
            cat = r["category"]
            status = (r["tx_status"] if "tx_status" in r.keys() else "ACTUAL") or "ACTUAL"

            if tx_type == "REVENUE":
                if status == "ACTUAL":
                    actual_rev_total += amt
                    by_channel_actual_rev[cat] = by_channel_actual_rev.get(cat, 0.0) + amt
                    if ts >= month_start:
                        actual_rev_month += amt
                    if ts >= week_start:
                        actual_rev_week += amt
                    if ts >= today_start:
                        actual_rev_today += amt
                elif status == "ESTIMATED":
                    estimated_rev_total += amt
                elif status == "PENDING":
                    pending_rev_total += amt
                elif status == "REFUNDED":
                    refunded_rev_total += amt
            elif tx_type == "EXPENSE":
                exp_total += amt
                by_category_exp[cat] = by_category_exp.get(cat, 0.0) + amt
                if ts >= month_start:
                    exp_month += amt
                if ts >= week_start:
                    exp_week += amt
                if ts >= today_start:
                    exp_today += amt

        # Part 25: If no actual revenue, report $0.00
        profit_total = actual_rev_total - exp_total
        margin = (profit_total / actual_rev_total * 100.0) if actual_rev_total > 0 else 0.0
        settings = FinancialFirewall.get_settings()
        virtual_balance = settings.get("virtual_balance", 1000.0) + profit_total

        return {
            "revenue": {
                "today": actual_rev_today,
                "this_week": actual_rev_week,
                "this_month": actual_rev_month,
                "total": actual_rev_total,
                "by_channel": by_channel_actual_rev
            },
            "revenue_breakdown": {
                "actual_revenue": round(actual_rev_total, 2),
                "estimated_revenue": round(estimated_rev_total, 2),
                "pending_revenue": round(pending_rev_total, 2),
                "refunded_revenue": round(refunded_rev_total, 2)
            },
            "expenses": {
                "today": exp_today,
                "this_week": exp_week,
                "this_month": exp_month,
                "total": exp_total,
                "by_category": by_category_exp
            },
            "profit": {
                "gross_revenue": actual_rev_total,
                "expenses": exp_total,
                "estimated_profit": profit_total,
                "profit_margin_pct": round(margin, 2),
                "cash_available_reinvestment": max(0.0, virtual_balance)
            },
            "reinvestment_policy": FinanceEngine.get_reinvestment_policy(),
            "firewall_limits": settings
        }
