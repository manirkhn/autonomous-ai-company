"""
Platform Integration Registry (Phase 5I).
Tracks every commercial channel, its official API/OAuth capabilities,
and classifies each into AUTONOMOUS, PARTIALLY_AUTONOMOUS, OWNER_ACTION_REQUIRED,
NOT_SUPPORTED, or NOT_RECOMMENDED with factual, documented evidence.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core.db import get_connection

class PlatformRegistry:
    """
    Registry for external commercial distribution channels and their automation status.
    """

    INITIAL_PLATFORMS = [
        {
            "platform": "Nexora Direct Website",
            "category": "OWNED_STOREFRONT",
            "official_url": "https://autonomous-ai-company.onrender.com/store",
            "api_available": 1,
            "oauth_available": 1,
            "automation_allowed": 1,
            "product_creation_supported": 1,
            "listing_creation_supported": 1,
            "publishing_supported": 1,
            "sales_data_supported": 1,
            "customer_data_supported": 1,
            "delivery_supported": 1,
            "requires_owner_action": 0,
            "owner_action_reason": "",
            "connection_status": "CONNECTED",
            "classification": "AUTONOMOUS",
            "integration_method": "NATIVE_FASTAPI_SQLITE",
            "compliance_status": "COMPLIANT",
            "evidence_notes": "First-party storefront running on Render cloud with automated Stripe checkout, SHA-256 digital fulfillment, and revenue verification."
        },
        {
            "platform": "Gumroad",
            "category": "DIGITAL_MARKETPLACE",
            "official_url": "https://gumroad.com",
            "api_available": 1,
            "oauth_available": 1,
            "automation_allowed": 1,
            "product_creation_supported": 0,
            "listing_creation_supported": 0,
            "publishing_supported": 0,
            "sales_data_supported": 1,
            "customer_data_supported": 1,
            "delivery_supported": 1,
            "requires_owner_action": 1,
            "owner_action_reason": "Gumroad API v2 supports sales, products, and webhook read operations, but restricts programmatic product creation on standard accounts. Legal owner must establish seller profile and link payout account.",
            "connection_status": "AWAITING_OWNER_SETUP",
            "classification": "PARTIALLY_AUTONOMOUS",
            "integration_method": "API_V2_WEBHOOKS",
            "compliance_status": "COMPLIANT",
            "evidence_notes": "Antigravity prepares complete package (copy, files, price, tags). Once owner initiates product or connects token, sales and fulfillment sync autonomously."
        },
        {
            "platform": "Lemon Squeezy",
            "category": "MERCHANT_OF_RECORD",
            "official_url": "https://lemonsqueezy.com",
            "api_available": 1,
            "oauth_available": 1,
            "automation_allowed": 1,
            "product_creation_supported": 1,
            "listing_creation_supported": 1,
            "publishing_supported": 1,
            "sales_data_supported": 1,
            "customer_data_supported": 1,
            "delivery_supported": 1,
            "requires_owner_action": 1,
            "owner_action_reason": "Merchant of Record regulations legally mandate human identity verification (KYC/KYB), tax forms, and banking payout approval.",
            "connection_status": "AWAITING_OWNER_KYC",
            "classification": "PARTIALLY_AUTONOMOUS",
            "integration_method": "REST_API_V1_WEBHOOKS",
            "compliance_status": "COMPLIANT",
            "evidence_notes": "Lemon Squeezy REST API v1 supports programmatic product, variant, and checkout creation. Antigravity operates all store operations automatically once API key is provisioned."
        },
        {
            "platform": "Etsy",
            "category": "CRAFT_CONSUMER_MARKETPLACE",
            "official_url": "https://etsy.com",
            "api_available": 1,
            "oauth_available": 1,
            "automation_allowed": 1,
            "product_creation_supported": 0,
            "listing_creation_supported": 0,
            "publishing_supported": 0,
            "sales_data_supported": 1,
            "customer_data_supported": 0,
            "delivery_supported": 0,
            "requires_owner_action": 0,
            "owner_action_reason": "Not recommended. Buyer intent is oriented toward crafts, design templates, and physical handmade items. Terminal CLI evaluation suites risk policy friction and customer refunds.",
            "connection_status": "NOT_RECOMMENDED",
            "classification": "NOT_RECOMMENDED",
            "integration_method": "OPEN_API_V3",
            "compliance_status": "POLICY_MISALIGNED",
            "evidence_notes": "ETSY_STATUS = NOT_RECOMMENDED_FOR_THIS_PRODUCT recorded based on audience and category mismatch."
        },
        {
            "platform": "GitHub",
            "category": "DEVELOPER_COMMUNITY",
            "official_url": "https://github.com",
            "api_available": 1,
            "oauth_available": 1,
            "automation_allowed": 1,
            "product_creation_supported": 0,
            "listing_creation_supported": 0,
            "publishing_supported": 0,
            "sales_data_supported": 0,
            "customer_data_supported": 0,
            "delivery_supported": 0,
            "requires_owner_action": 0,
            "owner_action_reason": "",
            "connection_status": "ACTIVE_MONITORING",
            "classification": "AUTONOMOUS",
            "integration_method": "REST_API_PUBLIC_DISCUSSIONS",
            "compliance_status": "COMPLIANT",
            "evidence_notes": "Autonomous read-only scanning of public issues and discussions on Ollama, vLLM, and llama.cpp. Anti-spam policy strictly enforced (zero bot comments)."
        },
        {
            "platform": "Reddit",
            "category": "COMMUNITY_FORUM",
            "official_url": "https://reddit.com",
            "api_available": 1,
            "oauth_available": 1,
            "automation_allowed": 1,
            "product_creation_supported": 0,
            "listing_creation_supported": 0,
            "publishing_supported": 0,
            "sales_data_supported": 0,
            "customer_data_supported": 0,
            "delivery_supported": 0,
            "requires_owner_action": 1,
            "owner_action_reason": "Reddit API ToS and subreddit self-promotion rules (r/LocalLLaMA Rule 3) prohibit autonomous promotional bot posting. Owner must review and approve outreach drafts.",
            "connection_status": "ACTIVE_MONITORING",
            "classification": "PARTIALLY_AUTONOMOUS",
            "integration_method": "REDDIT_DATA_API_MONITORING",
            "compliance_status": "COMPLIANT",
            "evidence_notes": "Opportunity detection is 100% autonomous. Outbound posts require human confirmation to prevent community bans."
        },
        {
            "platform": "Hacker News",
            "category": "TECH_COMMUNITY",
            "official_url": "https://news.ycombinator.com",
            "api_available": 1,
            "oauth_available": 0,
            "automation_allowed": 1,
            "product_creation_supported": 0,
            "listing_creation_supported": 0,
            "publishing_supported": 0,
            "sales_data_supported": 0,
            "customer_data_supported": 0,
            "delivery_supported": 0,
            "requires_owner_action": 1,
            "owner_action_reason": "Hacker News has no public write API. Automated posting or astroturfing triggers immediate algorithmic shadowbanning. Submissions must be owner-approved.",
            "connection_status": "ACTIVE_MONITORING",
            "classification": "PARTIALLY_AUTONOMOUS",
            "integration_method": "FIREBASE_HN_API_MONITORING",
            "compliance_status": "COMPLIANT",
            "evidence_notes": "Read monitoring is automated via official Firebase endpoints. Post drafting is automated; publishing is owner-verified."
        },
        {
            "platform": "Product Hunt",
            "category": "PRODUCT_DIRECTORY",
            "official_url": "https://www.producthunt.com",
            "api_available": 1,
            "oauth_available": 1,
            "automation_allowed": 1,
            "product_creation_supported": 1,
            "listing_creation_supported": 1,
            "publishing_supported": 0,
            "sales_data_supported": 0,
            "customer_data_supported": 0,
            "delivery_supported": 0,
            "requires_owner_action": 1,
            "owner_action_reason": "Product Hunt algorithm flags API-only programmatic product launches as low-reputation. High-converting launches require an active maker profile and scheduled launch date confirmation.",
            "connection_status": "ASSETS_PREPARED",
            "classification": "PARTIALLY_AUTONOMOUS",
            "integration_method": "GRAPHQL_API_V2",
            "compliance_status": "COMPLIANT",
            "evidence_notes": "Product Hunt launch copy, GIFs, maker comments, and badges are generated autonomously; owner authorizes launch day."
        },
        {
            "platform": "Google / SEO",
            "category": "SEARCH_ENGINE",
            "official_url": "https://google.com",
            "api_available": 1,
            "oauth_available": 0,
            "automation_allowed": 1,
            "product_creation_supported": 1,
            "listing_creation_supported": 1,
            "publishing_supported": 1,
            "sales_data_supported": 1,
            "customer_data_supported": 1,
            "delivery_supported": 1,
            "requires_owner_action": 0,
            "owner_action_reason": "",
            "connection_status": "ACTIVE_INDEXING",
            "classification": "AUTONOMOUS",
            "integration_method": "SITEMAP_ROBOTS_SCHEMA_ORG",
            "compliance_status": "COMPLIANT",
            "evidence_notes": "Autonomous generation of technical guides, sitemap.xml, Schema.org SoftwareApplication JSON-LD, and canonical links. Indexing proceeds organically."
        },
        {
            "platform": "Affiliate & Partner Network",
            "category": "REFERRAL_NETWORK",
            "official_url": "https://autonomous-ai-company.onrender.com/affiliates",
            "api_available": 1,
            "oauth_available": 0,
            "automation_allowed": 1,
            "product_creation_supported": 1,
            "listing_creation_supported": 1,
            "publishing_supported": 1,
            "sales_data_supported": 1,
            "customer_data_supported": 1,
            "delivery_supported": 1,
            "requires_owner_action": 0,
            "owner_action_reason": "",
            "connection_status": "ACTIVE_AUTONOMOUS",
            "classification": "AUTONOMOUS",
            "integration_method": "UTM_REFERRAL_CODE_ENGINE",
            "compliance_status": "COMPLIANT",
            "evidence_notes": "Autonomous generation of partner referral codes and commission tracking with full revenue ledger integration."
        },
        {
            "platform": "Software Directories (AlternativeTo, SaaSHub)",
            "category": "SOFTWARE_DIRECTORIES",
            "official_url": "https://alternativeto.net",
            "api_available": 0,
            "oauth_available": 0,
            "automation_allowed": 1,
            "product_creation_supported": 0,
            "listing_creation_supported": 1,
            "publishing_supported": 0,
            "sales_data_supported": 0,
            "customer_data_supported": 0,
            "delivery_supported": 0,
            "requires_owner_action": 1,
            "owner_action_reason": "Directories require manual CAPTCHA verification and personal account validation to prevent spam directory submissions.",
            "connection_status": "PACKAGES_READY",
            "classification": "PARTIALLY_AUTONOMOUS",
            "integration_method": "FORM_SUBMISSION_PACKAGE",
            "compliance_status": "COMPLIANT",
            "evidence_notes": "Antigravity prepares directory submission payload (title, tagline, alternatives, tags); single-click owner confirmation required."
        }
    ]

    @classmethod
    def init_registry(cls):
        """
        Seeds all commercial platforms into database if missing.
        """
        conn = get_connection()
        cursor = conn.cursor()
        now_iso = datetime.now(timezone.utc).isoformat()

        for p in cls.INITIAL_PLATFORMS:
            cursor.execute("SELECT platform FROM platform_integrations WHERE platform = ?", (p["platform"],))
            if not cursor.fetchone():
                cursor.execute("""
                INSERT INTO platform_integrations (
                    platform, category, official_url, api_available, oauth_available,
                    automation_allowed, product_creation_supported, listing_creation_supported,
                    publishing_supported, sales_data_supported, customer_data_supported,
                    delivery_supported, requires_owner_action, owner_action_reason,
                    connection_status, classification, last_verified, integration_method,
                    compliance_status, evidence_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    p["platform"], p["category"], p["official_url"], p["api_available"],
                    p["oauth_available"], p["automation_allowed"], p["product_creation_supported"],
                    p["listing_creation_supported"], p["publishing_supported"],
                    p["sales_data_supported"], p["customer_data_supported"], p["delivery_supported"],
                    p["requires_owner_action"], p["owner_action_reason"], p["connection_status"],
                    p["classification"], now_iso, p["integration_method"], p["compliance_status"],
                    p["evidence_notes"]
                ))

        conn.commit()
        conn.close()

    @classmethod
    def list_platforms(cls, classification: Optional[str] = None) -> List[Dict[str, Any]]:
        cls.init_registry()
        conn = get_connection()
        cursor = conn.cursor()
        if classification:
            cursor.execute("SELECT * FROM platform_integrations WHERE classification = ? ORDER BY platform ASC", (classification,))
        else:
            cursor.execute("SELECT * FROM platform_integrations ORDER BY platform ASC")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @classmethod
    def get_platform(cls, platform_name: str) -> Optional[Dict[str, Any]]:
        cls.init_registry()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM platform_integrations WHERE LOWER(platform) = LOWER(?)", (platform_name,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @classmethod
    def update_connection_status(cls, platform_name: str, status: str, notes: str = "") -> Dict[str, Any]:
        cls.init_registry()
        conn = get_connection()
        cursor = conn.cursor()
        now_iso = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
        UPDATE platform_integrations SET
            connection_status = ?,
            evidence_notes = CASE WHEN ? != '' THEN ? ELSE evidence_notes END,
            last_verified = ?
        WHERE LOWER(platform) = LOWER(?)
        """, (status, notes, notes, now_iso, platform_name))
        conn.commit()
        conn.close()
        return {"platform": platform_name, "connection_status": status, "last_verified": now_iso}

    @classmethod
    def get_autonomous_channels(cls) -> List[Dict[str, Any]]:
        return cls.list_platforms(classification="AUTONOMOUS")

    @classmethod
    def get_owner_required_channels(cls) -> List[Dict[str, Any]]:
        return cls.list_platforms(classification="OWNER_ACTION_REQUIRED")

    @classmethod
    def sync_all_platforms(cls) -> List[Dict[str, Any]]:
        """Syncs and refreshes the platform integration registry."""
        cls.init_registry()
        return cls.list_platforms()

    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        """Provides high-level integration counts and operational status."""
        platforms = cls.sync_all_platforms()
        autonomous_cnt = sum(1 for p in platforms if p["classification"] == "AUTONOMOUS")
        partially_cnt = sum(1 for p in platforms if p["classification"] == "PARTIALLY_AUTONOMOUS")
        owner_req_cnt = sum(1 for p in platforms if p["classification"] == "OWNER_ACTION_REQUIRED")
        not_rec_cnt = sum(1 for p in platforms if p["classification"] == "NOT_RECOMMENDED")
        not_sup_cnt = sum(1 for p in platforms if p["classification"] == "NOT_SUPPORTED")
        
        operating_cnt = sum(1 for p in platforms if p["connection_status"] in ["CONNECTED", "AUTONOMOUS_INDEXED", "PUBLIC_DIRECTORY_INDEXED"])

        return {
            "total_platforms": len(platforms),
            "autonomous": autonomous_cnt,
            "partially_autonomous": partially_cnt,
            "owner_action_required": owner_req_cnt,
            "not_recommended": not_rec_cnt,
            "not_supported": not_sup_cnt,
            "operating_channels": operating_cnt,
            "platforms": platforms
        }
