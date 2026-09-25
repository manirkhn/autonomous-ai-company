"""
Tool Abstraction Layer & Voice Capability Architecture (Part 12, 13, 14).
Provides provider-independent interfaces for:
VOICE, EMAIL, BROWSER, LLM, IMAGE, VIDEO, PAYMENTS, ANALYTICS, SEARCH, STORAGE.
Enforces strict Voice Safety Governance (no deception, AI identification, DNC compliance).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from core.audit import AuditLogger

# ----------------- Voice Safety Governance (Part 13) -----------------
class VoiceSafetyViolation(Exception):
    """Raised when a voice operation violates ethical, legal, or consent boundaries."""
    pass

class VoiceSafetyGuard:
    """Enforces Part 13 Voice Safety Rules."""
    
    @staticmethod
    def validate_call_request(
        recipient_phone: str,
        is_consent_verified: bool,
        is_opted_out: bool,
        intent: str,
        ai_identification_script: str
    ) -> None:
        # Rule 1: No unconsented calls / respect DNC
        if is_opted_out:
            raise VoiceSafetyViolation(f"DNC VIOLATION: Recipient {recipient_phone} has opted out. Contact is strictly prohibited.")
        if not is_consent_verified:
            raise VoiceSafetyViolation(f"CONSENT REQUIRED: Calling {recipient_phone} requires verified prior consent.")

        # Rule 2: Mandatory AI Identification
        if not ai_identification_script or "ai" not in ai_identification_script.lower():
            raise VoiceSafetyViolation(
                "DECEPTION PROHIBITED: Calling script MUST explicitly identify the system as an AI representative in the greeting."
            )

        # Rule 3: Zero mass calling / rate limits
        if "mass" in intent.lower() or "robocall" in intent.lower():
            raise VoiceSafetyViolation("MASS CALLING PROHIBITED: Automated blast calling is permanently disabled.")

    @classmethod
    def evaluate_call_safety(
        cls,
        recipient_phone: str,
        purpose: str,
        consent_record: Optional[str],
        is_opted_out: bool = False
    ) -> Dict[str, Any]:
        """Evaluates whether an intended call meets voice safety rules."""
        reasons = []
        if is_opted_out:
            reasons.append("Recipient is on opt-out / DNC list.")
        if not consent_record or "consent" not in consent_record.lower():
            reasons.append("Missing verified prior consent record.")
        if "mass" in purpose.lower() or "cold" in purpose.lower() or "telemarketing" in purpose.lower():
            reasons.append("Cold/mass robocalling is permanently prohibited.")

        return {
            "allowed": len(reasons) == 0,
            "reasons": reasons
        }

# ----------------- Abstract Interfaces (Part 14) -----------------
class BaseVoiceAdapter(ABC):
    @abstractmethod
    def synthesize_speech(self, text: str, voice_id: str) -> bytes:
        pass

    @abstractmethod
    def initiate_verified_call(self, recipient_phone: str, message: str, consent_token: str) -> Dict[str, Any]:
        pass

class BaseEmailAdapter(ABC):
    @abstractmethod
    def send_consented_email(self, to_addr: str, subject: str, body: str, unsubscribe_link: str) -> Dict[str, Any]:
        pass

class BaseLLMAdapter(ABC):
    @abstractmethod
    def generate_completion(self, prompt: str, system_prompt: str, max_tokens: int) -> str:
        pass

class BasePaymentsAdapter(ABC):
    @abstractmethod
    def create_checkout_session(self, product_id: str, amount_usd: float, customer_ref: str) -> str:
        pass

    @abstractmethod
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        pass

class BaseStorageAdapter(ABC):
    @abstractmethod
    def put_file(self, path: str, data: bytes) -> str:
        pass

    @abstractmethod
    def get_file(self, path: str) -> bytes:
        pass

# ----------------- Voice Capability Comparison Matrix (Part 12) -----------------
class VoiceCapabilityAdvisor:
    @staticmethod
    def get_provider_comparison() -> Dict[str, Any]:
        """Part 12: Comprehensive comparison of voice architectures."""
        return {
            "comparison_matrix": [
                {
                    "provider": "Local Open-Source (Piper TTS + Whisper STT)",
                    "type": "SELF_HOSTED_OSS",
                    "cost_per_min_usd": 0.0,
                    "voice_quality": "High (Offline neural voices)",
                    "reliability": "100% (No external API dependency)",
                    "phone_number_req": "Requires SIP gateway bridge",
                    "compliance_score": 1.0,
                    "recommended_for": "Initial development, voice synthesis, voicemail transcription"
                },
                {
                    "provider": "Twilio Voice API",
                    "type": "PROGRAMMATIC_COMMUNICATION_PAAS",
                    "cost_per_min_usd": 0.013,
                    "voice_quality": "Standard Telecom",
                    "reliability": "99.95%",
                    "phone_number_req": "1 local number (~$1.15/mo)",
                    "compliance_score": 0.95,
                    "recommended_for": "Direct carrier connectivity with strict consent tokens"
                },
                {
                    "provider": "Vapi / Retell AI Free Tier",
                    "type": "CONVERSATIONAL_VOICE_PAAS",
                    "cost_per_min_usd": 0.05,
                    "voice_quality": "Ultra-Low Latency Conversational",
                    "reliability": "99.9%",
                    "phone_number_req": "Virtual number supported",
                    "compliance_score": 0.90,
                    "recommended_for": "Complex inbound support calls once company reaches Level 3"
                }
            ],
            "recommendation": "Start with Level 4 Open-Source (Piper/Whisper) for zero-capital audio asset generation. Transition to Twilio with verified consent tokens only when paid revenue justifies the $1.15/mo phone number."
        }
