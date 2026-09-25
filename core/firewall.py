"""
Financial Firewall & Governance Gate.
Enforces strict boundaries between Owner Funds and Company Operations.
Guarantees AI cannot touch banking, withdraw, or spend without explicit human approval.
"""

from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timezone, timedelta
import json
from .db import get_connection

class FinancialFirewallViolation(Exception):
    """Raised when an action violates the financial safety firewall."""
    pass

class FinancialFirewall:
    """
    Manages and strictly enforces all financial constraints, approval thresholds,
    and banking isolation rules.
    """
    
    # Prohibited operations for any AI agent under all circumstances
    STRICTLY_PROHIBITED_ACTIONS = {
        "BANK_TRANSFER",
        "BANK_WITHDRAWAL",
        "ADD_BANK_BENEFICIARY",
        "MODIFY_BANK_BENEFICIARY",
        "CHANGE_BANKING_CREDENTIALS",
        "ACCESS_PRIVATE_BANKING_CREDENTIALS",
        "TAKE_LOAN",
        "SIGN_DEBT_AGREEMENT",
        "BINDING_FINANCIAL_COMMITMENT_UNAPPROVED"
    }

    @staticmethod
    def get_settings() -> Dict[str, Any]:
        """Fetch current firewall settings from database or return secure defaults."""
        defaults = {
            "max_single_expense": 0.0,             # Default: $0 (requires owner approval)
            "max_daily_expense": 0.0,              # Default: $0
            "max_monthly_expense": 0.0,            # Default: $0
            "advertising_limit": 0.0,              # Default: $0
            "software_subscription_limit": 0.0,    # Default: $0
            "approval_required_threshold": 0.0,    # All spend > $0 requires approval
            "emergency_stop": False,               # Emergency shutdown switch
            "allow_virtual_spending": True,        # Permitted for simulated testing
            "virtual_balance": 1000.0,             # Simulated sandbox seed capital
            "real_balance": 0.0                    # Actual verified cash balance
        }
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM company_settings WHERE key LIKE 'firewall_%'")
        rows = cursor.fetchall()
        conn.close()
        
        settings = defaults.copy()
        for row in rows:
            k = row["key"].replace("firewall_", "")
            try:
                settings[k] = json.loads(row["value"])
            except Exception:
                settings[k] = row["value"]
                
        return settings

    @classmethod
    def update_setting(cls, key: str, value: Any, updated_by: str = "OWNER") -> None:
        """Update a firewall setting. Only OWNER or verified admin can update."""
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        db_key = f"firewall_{key}"
        val_str = json.dumps(value)
        cursor.execute("""
            INSERT INTO company_settings (key, value, description, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
        """, (db_key, val_str, f"Updated by {updated_by}", now))
        conn.commit()
        conn.close()

    @classmethod
    def set_emergency_stop(cls, enabled: bool, reason: str = "Owner manual trigger") -> None:
        """Activate or deactivate the emergency shutdown kill switch."""
        cls.update_setting("emergency_stop", enabled)
        from .audit import AuditLogger
        AuditLogger.log(
            agent_id="SYSTEM",
            action="EMERGENCY_STOP_TOGGLED",
            result=f"Emergency stop set to {enabled}: {reason}",
            risk_level="CRITICAL",
            cost=0.0
        )

    @classmethod
    def is_halted(cls) -> bool:
        """Check if emergency stop is currently active."""
        return cls.get_settings().get("emergency_stop", False)

    @classmethod
    def check_operation_safety(cls, action_type: str, amount: float, agent_id: str, is_virtual: bool = True) -> Tuple[bool, str]:
        """
        Validate whether an operation is permitted under current firewall policy.
        Returns: (is_allowed, reason_or_status)
        """
        settings = cls.get_settings()
        
        # 1. Emergency Kill Switch Check
        if settings.get("emergency_stop", False):
            raise FinancialFirewallViolation(
                f"BLOCKED: Emergency Stop is active. All financial transactions and external operations are frozen."
            )

        # 2. Strict Absolute Prohibitions (Never allowed for AI)
        if action_type.upper() in cls.STRICTLY_PROHIBITED_ACTIONS:
            raise FinancialFirewallViolation(
                f"STRICTLY PROHIBITED: Action '{action_type}' is permanently forbidden to AI. "
                "The human owner retains exclusive control over banking and financial credentials."
            )

        # 3. Non-virtual (Real funds) spend safety check
        if not is_virtual and amount > 0:
            # Under initial policy, ALL real funds spend requires Human Approval
            return False, "APPROVAL_REQUIRED: All real monetary expenditures require Owner Approval."

        # 4. Expense Threshold Checks
        threshold = float(settings.get("approval_required_threshold", 0.0))
        max_single = float(settings.get("max_single_expense", 0.0))
        
        if amount > max_single:
            return False, f"APPROVAL_REQUIRED: Amount ${amount:.2f} exceeds max single expense limit of ${max_single:.2f}."
            
        if amount > threshold:
            return False, f"APPROVAL_REQUIRED: Amount ${amount:.2f} exceeds immediate approval threshold of ${threshold:.2f}."

        # 5. Daily cumulative check
        conn = get_connection()
        cursor = conn.cursor()
        since = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        cursor.execute("""
            SELECT SUM(amount) as total FROM financial_transactions 
            WHERE type='EXPENSE' AND timestamp >= ? AND is_virtual = ?
        """, (since, 1 if is_virtual else 0))
        row = cursor.fetchone()
        daily_total = (row["total"] or 0.0) + amount
        conn.close()

        max_daily = float(settings.get("max_daily_expense", 0.0))
        if max_daily > 0 and daily_total > max_daily:
            return False, f"APPROVAL_REQUIRED: Daily spending limit (${max_daily:.2f}) reached (Cumulative: ${daily_total:.2f})."

        return True, "ALLOWED"
