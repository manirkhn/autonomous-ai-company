"""
Gumroad Marketplace Channel Engine (Phase 5H, Section 3).

Prepares and manages the Gumroad digital product listing for Nexora AI Labs,
including files, copy, pricing, metadata, and transaction reconciliation.
"""

from typing import Dict, Any, List
from core.db import get_connection

class GumroadMarketplaceEngine:
    """
    Manages Gumroad listing preparation, webhooks, and sales verification.
    """

    CHANNEL_NAME = "Gumroad"
    PRODUCT_TITLE = "Local LLM Offline Evaluation & Prompt Regression Benchmark Suite"
    PRICE_USD = 29.00

    @classmethod
    def get_listing_specification(cls) -> Dict[str, Any]:
        """
        Complete Gumroad listing package matching Phase 5H requirements.
        """
        return {
            "channel": cls.CHANNEL_NAME,
            "brand": "Nexora AI Labs",
            "product_title": cls.PRODUCT_TITLE,
            "permalink": "nexora-local-llm-benchmark",
            "price_usd": cls.PRICE_USD,
            "currency": "USD",
            "summary": "Deterministic offline prompt regression benchmarking harness for Ollama, vLLM, and llama.cpp.",
            "description": (
                "### Local LLM Offline Evaluation & Prompt Regression Benchmark Suite\n\n"
                "**Deploying local LLMs in production without automated regression testing is risky.**\n\n"
                "Whenever you update model weights (e.g., LLaMA-3.1 to 3.2), switch quantizations (float16 to Q4_K_M), "
                "or reconfigure your inference server, system prompts often suffer subtle regressions: JSON syntax breakdown, "
                "formatting drift, reasoning hallucinations, or latency spikes.\n\n"
                "Cloud evaluation tools require sending private prompts and customer data to external APIs. "
                "**This suite runs 100% locally and offline on your own machine.**\n\n"
                "#### What You Get:\n"
                "- **100+ Prompt Regression Test Vectors**: Deterministic test suites covering structured JSON extraction, multi-turn reasoning, tool calls, and math.\n"
                "- **Latency & Throughput Harness**: Precise TTFT (Time To First Token) and token/sec throughput profiling for Ollama, vLLM, and llama.cpp.\n"
                "- **Strict Schema & Drift Verifier**: Automated validation script comparing outputs against baseline snapshots with clear PASS/FAIL scorecards.\n"
                "- **Offline Python Test Runner CLI (`run_eval.py`)**: Zero external dependencies required.\n"
                "- **Sample Golden Baselines & Schema Definitions**\n"
                "- **Lifetime Baseline Updates**: All future prompt packs and updates included.\n\n"
                "#### Supported Inference Engines:\n"
                "- Ollama (REST API)\n"
                "- vLLM (High-throughput OpenAI-compatible server)\n"
                "- llama.cpp (`llama-server`)\n"
                "- Any local OpenAI-compatible HTTP inference runner\n\n"
                "#### 30-Day Quality Assurance Guarantee:\n"
                "If this benchmark suite does not function with your local OpenAI-compatible inference server, contact support for a prompt resolution or full refund."
            ),
            "files_included": [
                {
                    "filename": "nexora-llm-benchmark-suite-v1.zip",
                    "description": "Complete Python test harness, runner CLI, regression suites, and documentation",
                    "checksum_sha256": "3a9c7b1d4e2f80165b4c9e523178fa20c96ba3f524cc179a46b2810bf5c8cb54"
                }
            ],
            "thumbnail_url": "/assets/mockups/gumroad_thumbnail.png",
            "cover_image_url": "/assets/mockups/gumroad_cover.png",
            "product_benefits": [
                "100% Offline & Private — Zero cloud API dependencies",
                "Compatible with Ollama, vLLM, and llama.cpp",
                "Instant digital fulfillment upon purchase",
                "Lifetime updates included with one-time purchase",
                "30-day quality assurance guarantee"
            ],
            "faq": [
                {
                    "q": "Does this tool send any prompt data over the internet?",
                    "a": "No. The entire suite operates locally on your machine or private VPC."
                },
                {
                    "q": "Which Python versions are supported?",
                    "a": "Python 3.10, 3.11, 3.12, 3.13, and 3.14."
                },
                {
                    "q": "How do I receive updates?",
                    "a": "You receive automated email notifications through Gumroad whenever updated test baselines are uploaded."
                }
            ],
            "support_email": "support@nexora-ai.com",
            "guarantee_policy": "30-Day Quality Assurance Guarantee under Nexora AI Labs verified refund policy.",
            "ecosystem_links": {
                "official_store": "https://autonomous-ai-company.onrender.com/store",
                "product_page": "https://autonomous-ai-company.onrender.com/product"
            },
            "status": "DRAFT_READY",
            "owner_action_required": "Create Gumroad account and connect payout destination"
        }

    @classmethod
    def get_channel_metrics(cls) -> Dict[str, Any]:
        """
        Retrieves verified Gumroad traffic and revenue metrics from database.
        Never counts unverified or simulated transactions.
        """
        conn = get_connection()
        cursor = conn.cursor()

        # Query attribution records specifically tagged with source=gumroad
        cursor.execute("""
        SELECT COUNT(*) as visitors,
               SUM(product_page_visited) as views,
               SUM(checkout_started) as checkouts,
               SUM(payment_verified) as sales,
               SUM(CASE WHEN payment_verified = 1 THEN revenue_usd ELSE 0.0 END) as revenue
        FROM acquisition_attribution
        WHERE LOWER(source) = 'gumroad' AND mode = 'PRODUCTION'
        """)
        row = cursor.fetchone()
        conn.close()

        return {
            "channel": cls.CHANNEL_NAME,
            "status": "PENDING_OWNER_SETUP",
            "visitors": row["visitors"] if row and row["visitors"] else 0,
            "product_views": row["views"] if row and row["views"] else 0,
            "checkout_starts": row["checkouts"] if row and row["checkouts"] else 0,
            "verified_purchases": row["sales"] if row and row["sales"] else 0,
            "refunds": 0,
            "net_revenue_usd": float(row["revenue"]) if row and row["revenue"] else 0.0
        }

    @classmethod
    def get_listing_package(cls) -> Dict[str, Any]:
        """
        Alias returning listing package formatted for tests and integrations.
        """
        spec = cls.get_listing_specification()
        return {
            "title": spec["product_title"],
            "description": spec["description"],
            "pricing": {"price_usd": spec["price_usd"], "currency": spec["currency"]},
            "product_files": spec["files_included"],
            "thumbnail": spec["thumbnail_url"],
            "product_benefits": spec["product_benefits"],
            "faq": spec["faq"],
            "support_info": spec["support_email"],
            "refund_guarantee": spec["guarantee_policy"],
            "branding": {"brand_name": spec["brand"]}
        }

    @classmethod
    def get_channel_status(cls) -> Dict[str, Any]:
        """
        Returns channel metrics and verification policy.
        """
        metrics = cls.get_channel_metrics()
        return {
            "channel": cls.CHANNEL_NAME,
            "strict_revenue_verification": True,
            "verified_sales_count": metrics["verified_purchases"],
            "verified_net_revenue": metrics["net_revenue_usd"],
            "visitors": metrics["visitors"],
            "product_views": metrics["product_views"],
            "checkout_starts": metrics["checkout_starts"],
            "refunds": metrics["refunds"]
        }
