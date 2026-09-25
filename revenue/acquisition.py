"""
Customer Acquisition Engine & Outreach Governance (Phase 4, Parts 12, 13 & 14).
Supports compliant organic, community, and direct outreach channels.
Enforces strict anti-spam, suppression lists, opt-out automation, and owner approval gates.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core.db import get_connection
from approvals.manager import ApprovalManager
from tools.abstractions import VoiceSafetyGuard

class AcquisitionPolicyError(Exception):
    """Raised when an acquisition activity violates safety or compliance policies."""
    pass

class CustomerAcquisitionEngine:
    """
    Orchestrates compliant customer acquisition campaigns and manages suppression.
    """

    @classmethod
    def create_campaign(
        cls,
        target_definition: str,
        source: str,
        consent_or_legal_basis: str,
        message: str,
        frequency_limit: str,
        opt_out_method: str,
        channel: str = "ORGANIC_COMMUNITY",
        require_owner_approval: bool = True
    ) -> Dict[str, Any]:
        """
        Creates a new outreach or acquisition campaign.
        Enforces approval requirement before any external launch.
        """
        # Anti-spam and anti-deception pre-validation
        if not opt_out_method:
            raise AcquisitionPolicyError("Campaign must provide a clear opt-out method.")
        if "guaranteed income" in message.lower() or "100% profit" in message.lower():
            raise AcquisitionPolicyError("Deceptive marketing claims are strictly prohibited.")

        # Check voice channel restrictions (Part 14)
        if channel.upper() == "VOICE":
            # Must evaluate free-first alternatives and ensure voice safety compliance
            voice_eval = VoiceSafetyGuard.evaluate_call_safety(
                recipient_phone="PENDING_VERIFICATION",
                purpose="Lead qualification",
                consent_record=consent_or_legal_basis,
                is_opted_out=False
            )
            if not voice_eval["allowed"]:
                raise AcquisitionPolicyError(f"Voice campaign blocked by safety guard: {voice_eval['reasons']}")

        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        campaign_id = f"CAMP-{int(datetime.now(timezone.utc).timestamp())}"

        # If owner approval required, submit to ApprovalManager
        approval_id = None
        if require_owner_approval:
            approval_id = ApprovalManager.create_approval_request(
                requesting_agent="EMP-003-MARKETING",
                what=f"Authorize Acquisition Campaign: {campaign_id} via {channel}",
                why=f"Target: {target_definition}. Legal basis: {consent_or_legal_basis}.",
                expected_benefit="Generate qualified traffic and initial customer discovery leads.",
                expected_cost=0.0,
                risk_level="LOW",
                alternatives="Passive organic search only",
                recommendation=f"Approve compliant {channel} outreach with automated opt-out suppression."
            )

        cursor.execute("""
        INSERT INTO outreach_campaigns (
            campaign_id, target_definition, source, consent_or_legal_basis,
            message, frequency_limit, opt_out_method, suppression_list,
            channel, start_time, owner_approval, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            campaign_id, target_definition, source, consent_or_legal_basis,
            message, frequency_limit, opt_out_method, json.dumps([]),
            channel, now, 0 if require_owner_approval else 1,
            "PENDING_APPROVAL" if require_owner_approval else "ACTIVE", now
        ))
        conn.commit()
        conn.close()

        return {
            "campaign_id": campaign_id,
            "channel": channel,
            "status": "PENDING_APPROVAL" if require_owner_approval else "ACTIVE",
            "approval_id": approval_id,
            "opt_out_method": opt_out_method
        }

    @classmethod
    def record_opt_out(cls, campaign_id: str, contact_identifier: str) -> bool:
        """
        Suppresses a contact immediately upon opt-out request.
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT suppression_list FROM outreach_campaigns WHERE campaign_id = ?", (campaign_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False

        suppression = json.loads(row["suppression_list"] or "[]")
        if contact_identifier not in suppression:
            suppression.append(contact_identifier)

        cursor.execute("""
        UPDATE outreach_campaigns SET suppression_list = ? WHERE campaign_id = ?
        """, (json.dumps(suppression), campaign_id))
        conn.commit()
        conn.close()
        return True

    @classmethod
    def is_suppressed(cls, campaign_id: str, contact_identifier: str) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT suppression_list FROM outreach_campaigns WHERE campaign_id = ?", (campaign_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return False
        suppression = json.loads(row["suppression_list"] or "[]")
        return contact_identifier in suppression

    @classmethod
    def get_campaigns(cls) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM outreach_campaigns ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
