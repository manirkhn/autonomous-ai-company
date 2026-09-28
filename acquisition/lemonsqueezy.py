"""
Lemon Squeezy Marketplace Channel Engine (Phase 5H, Section 4).

Prepares and tracks the Lemon Squeezy software and digital product channel.
Operates as a Merchant of Record (MoR) for global compliance and tax remittance.
Creates verified owner actions for KYC/KYB store onboarding.
"""

from typing import Dict, Any
from core.db import get_connection

class LemonSqueezyMarketplaceEngine:
    """
    Manages Lemon Squeezy integration specification, compliance status, and telemetry.
    """

    CHANNEL_NAME = "Lemon Squeezy"
    PRODUCT_TITLE = "Local LLM Offline Evaluation & Prompt Regression Benchmark Suite"
    PRICE_USD = 29.00

    @classmethod
    def get_channel_specification(cls) -> Dict[str, Any]:
        """
        Complete Lemon Squeezy integration specification matching Phase 5H requirements.
        """
        return {
            "channel": cls.CHANNEL_NAME,
            "brand": "Nexora AI Labs",
            "model": "Merchant of Record (MoR)",
            "product_title": cls.PRODUCT_TITLE,
            "product_type": "Digital Software / Developer Testing Suite",
            "price_usd": cls.PRICE_USD,
            "currency": "USD",
            "hosted_checkout_ready": True,
            "digital_fulfillment": {
                "method": "Direct ZIP download + license key",
                "file_attached": "nexora-llm-benchmark-suite-v1.zip",
                "redirect_url": "https://autonomous-ai-company.onrender.com/delivery"
            },
            "external_checkout_links": {
                "buy_button_url": "https://nexora.lemonsqueezy.com/buy/local-llm-benchmark",
                "embed_overlay_supported": True
            },
            "marketplace_discovery_status": {
                "eligible": True,
                "review_required": True,
                "notes": "Lemon Squeezy requires store activation and first sale review before inclusion in public discovery directory."
            },
            "onboarding_state": {
                "application_status": "PENDING_OWNER_SUBMISSION",
                "activation_status": "AWAITING_OWNER_KYC",
                "product_status": "DRAFT_SPECIFIED",
                "kyc_kyb_required": True
            },
            "owner_action_required": "ACTION REQUIRED: Connect Lemon Squeezy and submit KYC/KYB business verification."
        }

    @classmethod
    def get_channel_metrics(cls) -> Dict[str, Any]:
        """
        Returns verified Lemon Squeezy metrics from database.
        Never counts unverified or simulated transactions.
        """
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT COUNT(*) as visitors,
               SUM(product_page_visited) as views,
               SUM(checkout_started) as checkouts,
               SUM(payment_verified) as sales,
               SUM(CASE WHEN payment_verified = 1 THEN revenue_usd ELSE 0.0 END) as revenue
        FROM acquisition_attribution
        WHERE LOWER(source) = 'lemon squeezy' AND mode = 'PRODUCTION'
        """)
        row = cursor.fetchone()
        conn.close()

        return {
            "channel": cls.CHANNEL_NAME,
            "application_status": "PENDING_OWNER_SUBMISSION",
            "activation_status": "AWAITING_OWNER_KYC",
            "product_status": "DRAFT_SPECIFIED",
            "marketplace_eligibility": "PENDING_FIRST_SALE_REVIEW",
            "checkout_status": "HOSTED_CHECKOUT_DRAFT",
            "visitors": row["visitors"] if row and row["visitors"] else 0,
            "product_views": row["views"] if row and row["views"] else 0,
            "checkout_starts": row["checkouts"] if row and row["checkouts"] else 0,
            "verified_sales": row["sales"] if row and row["sales"] else 0,
            "verified_revenue_usd": float(row["revenue"]) if row and row["revenue"] else 0.0
        }

    @classmethod
    def get_channel_status(cls) -> Dict[str, Any]:
        """
        Returns full integration status including role, KYC status, and metrics.
        """
        spec = cls.get_channel_specification()
        metrics = cls.get_channel_metrics()
        return {
            "channel": cls.CHANNEL_NAME,
            "role": spec["model"],
            "activation_status": {
                "kyc_completed": False,
                "owner_action_required": True,
                "status_label": metrics["activation_status"]
            },
            "metrics": metrics
        }
