"""
Owner Settlement Profile & Banking Air-Gap Enforcement (Phase 5D, Sections 2-4, 19, 35).

CRITICAL INVARIANTS:
1. OWNER BANKING REMAINS STRICTLY AIR-GAPPED.
2. AI MUST NEVER store, log, or request online banking passwords, OTPs, PINs,
   debit card credentials, CVVs, or full account/IBAN numbers.
3. If a payment provider requires bank account details during secure merchant onboarding,
   the owner must enter those details directly inside the provider's official dashboard,
   NEVER inside the AI company application.
4. Only non-sensitive metadata (masked references, settlement currency, status) is retained.
"""

import os
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from core.db import get_connection
from revenue.ledger import BankingSecurityViolation

# Regex patterns for accidental banking credential leak detection
SENSITIVE_CREDENTIAL_PATTERNS = [
    (re.compile(r"AE\d{21}", re.IGNORECASE), "Full UAE IBAN"),
    (re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b"), "Credit/Debit Card Number"),
    (re.compile(r"\b\d{3,4}\b(?=.*(?:cvv|cvc|security code))", re.IGNORECASE), "CVV/CVC"),
    (re.compile(r"(?:password|pin|otp|passcode)\s*[:=]\s*['\"]?[^\s'\"]+", re.IGNORECASE), "Password/PIN/OTP")
]

class OwnerSettlementManager:
    """
    Manages non-sensitive owner settlement configuration with strict banking security enforcement.
    """

    DEFAULT_PROFILE = {
        "profile_id": "PRIMARY",
        "country": "AE",
        "bank_name": "Emirates Islamic",
        "settlement_currency": "AED",
        "account_type": "business",
        "settlement_destination_status": "CONFIGURED",
        "payment_provider": "STRIPE_UAE",
        "masked_destination_reference": "****1234",
        "owner_approval_status": "APPROVED",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    @classmethod
    def get_profile(cls) -> Dict[str, Any]:
        """
        Retrieves the current owner settlement profile from the database.
        Initializes default non-sensitive profile if none exists.
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM owner_settlement_profile WHERE profile_id = 'PRIMARY'")
        row = cursor.fetchone()
        
        if not row:
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
            INSERT INTO owner_settlement_profile (
                profile_id, country, bank_name, settlement_currency,
                account_type, settlement_destination_status, payment_provider,
                masked_destination_reference, owner_approval_status, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cls.DEFAULT_PROFILE["profile_id"],
                cls.DEFAULT_PROFILE["country"],
                cls.DEFAULT_PROFILE["bank_name"],
                cls.DEFAULT_PROFILE["settlement_currency"],
                cls.DEFAULT_PROFILE["account_type"],
                cls.DEFAULT_PROFILE["settlement_destination_status"],
                cls.DEFAULT_PROFILE["payment_provider"],
                cls.DEFAULT_PROFILE["masked_destination_reference"],
                cls.DEFAULT_PROFILE["owner_approval_status"],
                now
            ))
            conn.commit()
            cursor.execute("SELECT * FROM owner_settlement_profile WHERE profile_id = 'PRIMARY'")
            row = cursor.fetchone()

        conn.close()
        profile_dict = dict(row)
        profile_dict["banking_air_gap_enforced"] = True
        profile_dict["credentials_held_by_ai"] = False
        return profile_dict

    @classmethod
    def update_profile(
        cls,
        country: Optional[str] = None,
        bank_name: Optional[str] = None,
        settlement_currency: Optional[str] = None,
        account_type: Optional[str] = None,
        settlement_destination_status: Optional[str] = None,
        payment_provider: Optional[str] = None,
        masked_destination_reference: Optional[str] = None,
        owner_approval_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Updates the owner settlement profile with strict input sanitation.
        Rejects full IBANs, card numbers, or passwords with BankingSecurityViolation.
        """
        updates = {}
        for key, val in [
            ("country", country),
            ("bank_name", bank_name),
            ("settlement_currency", settlement_currency),
            ("account_type", account_type),
            ("settlement_destination_status", settlement_destination_status),
            ("payment_provider", payment_provider),
            ("masked_destination_reference", masked_destination_reference),
            ("owner_approval_status", owner_approval_status)
        ]:
            if val is not None:
                cls._validate_no_credentials(str(val), key)
                updates[key] = val

        if not updates:
            return cls.get_profile()

        # If masked_destination_reference is provided, enforce masking
        if "masked_destination_reference" in updates:
            ref = updates["masked_destination_reference"]
            if not ref.startswith("****") and len(ref) > 4:
                raise BankingSecurityViolation(
                    "Security violation: Only masked destination references (e.g. '****1234') are permitted."
                )

        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        updates["updated_at"] = now

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + ["PRIMARY"]

        cursor.execute(f"UPDATE owner_settlement_profile SET {set_clause} WHERE profile_id = ?", values)
        conn.commit()
        conn.close()

        return cls.get_profile()

    @classmethod
    def _validate_no_credentials(cls, text: str, field_name: str) -> None:
        """
        Throws BankingSecurityViolation if text contains full IBAN, card numbers, or credential markers.
        """
        for pattern, desc in SENSITIVE_CREDENTIAL_PATTERNS:
            if pattern.search(text):
                raise BankingSecurityViolation(
                    f"CRITICAL SECURITY BLOCK: Attempt to insert sensitive banking credential ({desc}) "
                    f"in field '{field_name}'. The AI company is air-gapped from personal banking."
                )

    @classmethod
    def verify_air_gap(cls) -> Dict[str, Any]:
        """
        Audits current settlement profile to guarantee that no private banking credentials exist.
        """
        profile = cls.get_profile()
        violations = []

        for field, val in profile.items():
            if isinstance(val, str):
                for pattern, desc in SENSITIVE_CREDENTIAL_PATTERNS:
                    if pattern.search(val):
                        violations.append(f"Sensitive credential ({desc}) detected in field {field}")

        is_air_gapped = len(violations) == 0
        return {
            "air_gap_intact": is_air_gapped,
            "violations": violations,
            "bank_name": profile.get("bank_name"),
            "masked_reference": profile.get("masked_destination_reference"),
            "credentials_held_by_ai": False,
            "owner_direct_onboarding_required": True
        }

    @classmethod
    def get_safe_settlement_instructions(cls) -> Dict[str, str]:
        """
        Provides owner instructions for configuring payout destination directly in payment provider portal.
        """
        return {
            "title": "Air-Gapped Payout Configuration",
            "rule": "Never give banking passwords or full details to the AI application.",
            "step_1": "Log into your official Payment Provider dashboard (e.g., dashboard.stripe.com).",
            "step_2": "Navigate to Settings -> Payout Settings / Bank Accounts.",
            "step_3": "Enter your Emirates Islamic IBAN directly into the provider's PCI-DSS compliant interface.",
            "step_4": "Once verified by the provider, update the AI system's masked reference (e.g. '****1234') only."
        }
