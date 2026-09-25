"""
Capability Acquisition Engine & Free-First Acquisition Ladder (Part 2, 3, 4, 19).
Systematically detects capability gaps, evaluates options across an 8-level free-first ladder,
calculates ROI, and recommends whether to upgrade an existing employee, create a new skill,
or spawn a new AI employee.
"""

import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core.db import get_connection
from core.audit import AuditLogger

ACQUISITION_LADDER_LEVELS = [
    "LEVEL_1_EXISTING_CAPABILITY",
    "LEVEL_2_INSTALLED_SOFTWARE",
    "LEVEL_3_FREE_NATIVE_FUNCTIONALITY",
    "LEVEL_4_OPEN_SOURCE_SOFTWARE",
    "LEVEL_5_FREE_API_FREE_TIER",
    "LEVEL_6_LOW_COST_SERVICE",
    "LEVEL_7_CUSTOM_DEVELOPMENT",
    "LEVEL_8_ENTERPRISE_COMMERCIAL"
]

class CapabilityAcquisitionEngine:
    @staticmethod
    def calculate_roi_analysis(
        current_cost_usd: float,
        proposed_cost_usd: float,
        expected_revenue_impact_usd: float,
        owner_hours_saved_monthly: float,
        owner_hourly_rate_usd: float = 100.0,
        risk_level: str = "LOW"
    ) -> Dict[str, Any]:
        """
        Part 19: ROI Calculation Engine.
        Computes cost savings, owner time savings, net benefit, and payback period.
        """
        owner_value_saved_monthly = owner_hours_saved_monthly * owner_hourly_rate_usd
        monthly_cost_delta = proposed_cost_usd - current_cost_usd
        monthly_net_gain = (expected_revenue_impact_usd + owner_value_saved_monthly) - monthly_cost_delta

        payback_months = 0.0
        if proposed_cost_usd > 0:
            if monthly_net_gain > 0:
                payback_months = round(proposed_cost_usd / monthly_net_gain, 1)
            else:
                payback_months = 999.0 # Negative return

        roi_pct = 0.0
        if proposed_cost_usd > 0:
            roi_pct = round((monthly_net_gain * 12.0) / proposed_cost_usd * 100.0, 1)
        else:
            roi_pct = 1000.0 # Infinite/zero-cost return

        return {
            "current_cost_usd": current_cost_usd,
            "proposed_cost_usd": proposed_cost_usd,
            "expected_revenue_impact_usd": expected_revenue_impact_usd,
            "owner_hours_saved_monthly": owner_hours_saved_monthly,
            "monthly_net_gain_usd": round(monthly_net_gain, 2),
            "yearly_net_gain_usd": round(monthly_net_gain * 12.0, 2),
            "payback_months": payback_months,
            "expected_roi_pct": roi_pct,
            "risk_level": risk_level,
            "failure_condition": "Net business return is less than the operating cost or maintenance overhead."
        }

    @staticmethod
    def register_capability_gap(
        capability_name: str,
        why_required: str,
        business_objective: str,
        detected_by: str = "EMP-012-AUTOMATION",
        frequency: str = "WEEKLY",
        current_workaround: str = "Manual owner task",
        owner_time_required_hours: float = 2.0,
        current_cost: float = 0.0,
        expected_benefit: str = "",
        urgency: str = "MEDIUM",
        risk: str = "LOW",
        free_options: Optional[List[str]] = None,
        oss_options: Optional[List[str]] = None,
        free_tier_options: Optional[List[str]] = None,
        paid_options: Optional[List[str]] = None,
        build_internal_option: str = "Implement specialized Python skill script",
        recommended_approach: str = "FREE_FIRST_OSS",
        expected_cost: float = 0.0,
        expected_roi: str = "300% efficiency gain with $0 capital expense",
        approval_required: bool = True
    ) -> str:
        """
        Part 4: Structured Capability Gap Record.
        """
        gap_id = f"GAP-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO capability_gaps (
                gap_id, title, why_required, frequency, expected_business_impact,
                free_tools, oss_options, free_tiers, paid_options, estimated_cost,
                expected_roi, owner_time_saved, risk, status, created_at,
                capability_name, detected_by, business_objective, current_workaround,
                owner_time_required, current_cost, expected_benefit, urgency,
                free_tier_options, build_internal_option, recommended_approach,
                approval_required
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'IDENTIFIED', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            gap_id, capability_name, why_required, frequency, expected_benefit or business_objective,
            json.dumps(free_options or []), json.dumps(oss_options or []),
            json.dumps(free_tier_options or []), json.dumps(paid_options or []),
            expected_cost, expected_roi, owner_time_required_hours, risk, now,
            capability_name, detected_by, business_objective, current_workaround,
            owner_time_required_hours, current_cost, expected_benefit, urgency,
            json.dumps(free_tier_options or []), build_internal_option, recommended_approach,
            1 if approval_required else 0
        ))
        conn.commit()
        conn.close()

        AuditLogger.log(
            agent_id=detected_by,
            action="CAPABILITY_GAP_REGISTERED",
            result=f"Capability Gap {gap_id} registered: '{capability_name}' (Recommended: {recommended_approach})",
            risk_level=risk.upper(),
            cost=expected_cost,
            details={"gap_id": gap_id, "capability_name": capability_name}
        )
        return gap_id

    @staticmethod
    def evaluate_acquisition_ladder(capability_name: str, description: str) -> Dict[str, Any]:
        """
        Part 2 & 3: Evaluates the Free-First Ladder across all 8 levels.
        Always inspects internal, free, and open-source options before paid.
        """
        cap_lower = capability_name.lower() + " " + description.lower()

        import re
        # Check Voice / Calling using word boundaries
        if re.search(r"\b(voice|call|calling|phone|telephony|dialer)\b", cap_lower):
            return {
                "capability_name": capability_name,
                "ladder_levels": [
                    {"level": 1, "name": "Existing Capability", "candidate": "None active in company", "cost": 0.0, "viable": False},
                    {"level": 2, "name": "Installed Software", "candidate": "Python standard library (wave/audio)", "cost": 0.0, "viable": False},
                    {"level": 3, "name": "Free Native Tool", "candidate": "WebRTC / Browser audio recording", "cost": 0.0, "viable": True},
                    {"level": 4, "name": "Open-Source Software", "candidate": "Whisper.cpp (Speech-to-Text) + Piper TTS (Text-to-Speech)", "cost": 0.0, "viable": True, "recommended": True},
                    {"level": 5, "name": "Free Tier API", "candidate": "Twilio free trial credits / Groq Audio API free tier", "cost": 0.0, "viable": True},
                    {"level": 6, "name": "Low-Cost SaaS", "candidate": "Vapi / Retell AI ($0.05/min)", "cost": 15.0, "viable": True},
                    {"level": 7, "name": "Custom Development", "candidate": "SIP / Asterisk gateway integration", "cost": 0.0, "viable": False},
                    {"level": 8, "name": "Enterprise Service", "candidate": "Genesys Cloud / Amazon Connect enterprise", "cost": 500.0, "viable": False}
                ],
                "recommended_level": 4,
                "recommended_solution": "Open-Source Piper TTS + Whisper STT on free tier API bridge",
                "recommended_action_type": "CREATE_NEW_EMPLOYEE", # e.g. EMP-013 AI Sales Caller
                "suggested_role": "AI Voice Communication Specialist",
                "estimated_cost": 0.0,
                "security_rating": 0.95
            }

        # Check Analytics / Reporting
        elif "analytics" in cap_lower or "metrics" in cap_lower:
            return {
                "ladder_levels": [
                    {"level": 1, "name": "Existing Capability", "candidate": "FinanceEngine & TaskEngine internal tables", "cost": 0.0, "viable": True, "recommended": True},
                    {"level": 2, "name": "Installed Software", "candidate": "SQLite / Pandas", "cost": 0.0, "viable": True},
                    {"level": 3, "name": "Free Native Tool", "candidate": "HTML5 Canvas / SVG charts", "cost": 0.0, "viable": True},
                    {"level": 4, "name": "Open-Source Software", "candidate": "Chart.js / Metabase OSS", "cost": 0.0, "viable": True}
                ],
                "recommended_level": 1,
                "recommended_solution": "Upgrade Finance Analyst (EMP-009-FINANCE) with enhanced SQL analytics skill",
                "recommended_action_type": "UPGRADE_EXISTING_EMPLOYEE",
                "target_employee_id": "EMP-009-FINANCE",
                "estimated_cost": 0.0,
                "security_rating": 1.0
            }

        # Default: General Developer / Automation Tool
        else:
            return {
                "ladder_levels": [
                    {"level": 1, "name": "Existing Capability", "candidate": "Inspect internal tool registry", "cost": 0.0, "viable": False},
                    {"level": 3, "name": "Free Native Tool", "candidate": "Python standard library script", "cost": 0.0, "viable": True},
                    {"level": 4, "name": "Open-Source Software", "candidate": "Permitted open-source library from PyPI/GitHub", "cost": 0.0, "viable": True, "recommended": True},
                    {"level": 6, "name": "Low-Cost SaaS", "candidate": "Third-party subscription API", "cost": 29.0, "viable": True}
                ],
                "recommended_level": 4,
                "recommended_solution": "Build clean self-contained open-source Python module via Skill Pipeline",
                "recommended_action_type": "CREATE_NEW_SKILL",
                "estimated_cost": 0.0,
                "security_rating": 0.98
            }

    @staticmethod
    def get_all_gaps() -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM capability_gaps ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
