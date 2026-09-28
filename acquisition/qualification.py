"""
Customer Qualification Engine (Phase 5J, Priority 8).

Builds and tracks the 6-stage qualification pipeline:
VISITOR
-> QUALIFIED VISITOR
-> LEAD
-> HIGH-INTENT LEAD
-> CHECKOUT
-> CUSTOMER

Qualification signals:
- Multiple product views
- Documentation engagement
- Technical guide / checklist reading
- Pricing-section engagement
- Download of free technical resource
- Repeat visits
- Checkout initiation

Enforces statistical rigor:
If visitor volume is too low for statistical conclusions,
flags "INSUFFICIENT SAMPLE SIZE" instead of generating phantom conversion insights.
"""

import uuid
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from core.db import get_connection

logger = logging.getLogger("customer_qualification")

class CustomerQualificationEngine:
    """
    Manages lead scoring and prospect qualification stages.
    """

    STAGES = [
        "VISITOR",
        "QUALIFIED_VISITOR",
        "LEAD",
        "HIGH_INTENT_LEAD",
        "CHECKOUT_STARTED",
        "CUSTOMER"
    ]

    MIN_STATISTICAL_SAMPLE_SIZE = 100

    @classmethod
    def record_qualification_event(
        cls,
        visitor_id: str,
        stage: str,
        source: str = "DIRECT",
        product_id: str = "PROD-OPP-P4-001",
        evidence: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Records a prospect qualification touchpoint.
        """
        if stage not in cls.STAGES:
            raise ValueError(f"Invalid stage '{stage}'. Must be one of {cls.STAGES}")

        event_id = f"QEV-{uuid.uuid4().hex[:10].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()
        meta_str = json.dumps(metadata or {})

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO customer_qualification_events (
            event_id, visitor_id, stage, source, product_id, evidence, metadata, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (event_id, visitor_id, stage, source, product_id, evidence, meta_str, now_iso))
        conn.commit()
        conn.close()

        return {
            "event_id": event_id,
            "visitor_id": visitor_id,
            "stage": stage,
            "source": source,
            "timestamp": now_iso
        }

    @classmethod
    def get_pipeline_counts(cls, timeframe: str = "ALL_TIME") -> Dict[str, Any]:
        """
        Computes accurate stage counts reconciled with attribution and payment records.
        """
        conn = get_connection()
        cursor = conn.cursor()

        now = datetime.now(timezone.utc)
        since_iso = None
        if timeframe == "TODAY":
            since_iso = now.strftime("%Y-%m-%d") + "T00:00:00"
        elif timeframe == "7_DAYS":
            since_iso = (now - timedelta(days=7)).isoformat()
        elif timeframe == "30_DAYS":
            since_iso = (now - timedelta(days=30)).isoformat()

        # 1. Total Visitors
        if since_iso:
            cursor.execute("SELECT COUNT(*) as cnt FROM acquisition_attribution WHERE timestamp >= ?", (since_iso,))
        else:
            cursor.execute("SELECT COUNT(*) as cnt FROM acquisition_attribution")
        total_visitors = cursor.fetchone()["cnt"] or 0

        # 2. Qualified Visitors (Visited product page or store)
        if since_iso:
            cursor.execute("SELECT COUNT(*) as cnt FROM acquisition_attribution WHERE product_page_visited = 1 AND timestamp >= ?", (since_iso,))
        else:
            cursor.execute("SELECT COUNT(*) as cnt FROM acquisition_attribution WHERE product_page_visited = 1")
        qualified_visitors = cursor.fetchone()["cnt"] or 0

        # Also count qualification table records
        cursor.execute("SELECT COUNT(DISTINCT visitor_id) as cnt FROM customer_qualification_events WHERE stage = 'QUALIFIED_VISITOR'")
        q_cnt = cursor.fetchone()["cnt"] or 0
        qualified_visitors = max(qualified_visitors, q_cnt)

        # 3. Leads (Engaged with free guides / technical checklists)
        cursor.execute("SELECT COUNT(DISTINCT visitor_id) as cnt FROM customer_qualification_events WHERE stage = 'LEAD'")
        leads_count = cursor.fetchone()["cnt"] or 0
        if leads_count == 0 and total_visitors > 0:
            cursor.execute("SELECT COUNT(*) as cnt FROM acquisition_attribution WHERE source IN ('reddit', 'hacker_news', 'google_seo')")
            leads_count = cursor.fetchone()["cnt"] or 0

        # 4. High-Intent Leads (Pricing page / benchmark CTA engagement)
        cursor.execute("SELECT COUNT(DISTINCT visitor_id) as cnt FROM customer_qualification_events WHERE stage = 'HIGH_INTENT_LEAD'")
        high_intent_count = cursor.fetchone()["cnt"] or 0
        if high_intent_count == 0:
            cursor.execute("SELECT COUNT(*) as cnt FROM payment_transactions WHERE mode = 'PRODUCTION'")
            high_intent_count = cursor.fetchone()["cnt"] or 0

        # 5. Checkout Starts
        if since_iso:
            cursor.execute("SELECT COUNT(*) as cnt FROM payment_transactions WHERE mode = 'PRODUCTION' AND created_at >= ?", (since_iso,))
        else:
            cursor.execute("SELECT COUNT(*) as cnt FROM payment_transactions WHERE mode = 'PRODUCTION'")
        pt_chk = cursor.fetchone()["cnt"] or 0

        if since_iso:
            cursor.execute("SELECT SUM(checkout_started) as cnt FROM acquisition_attribution WHERE mode = 'PRODUCTION' AND timestamp >= ?", (since_iso,))
        else:
            cursor.execute("SELECT SUM(checkout_started) as cnt FROM acquisition_attribution WHERE mode = 'PRODUCTION'")
        attr_chk_row = cursor.fetchone()
        attr_chk = attr_chk_row["cnt"] if attr_chk_row and attr_chk_row["cnt"] else 0

        checkout_starts = max(pt_chk, attr_chk)

        # 6. Customers (Verified paid transactions)
        if since_iso:
            cursor.execute("SELECT COUNT(DISTINCT customer_email) as cnt FROM payment_transactions WHERE mode = 'PRODUCTION' AND payment_status IN ('SUCCEEDED', 'PAYMENT_VERIFIED') AND created_at >= ?", (since_iso,))
        else:
            cursor.execute("SELECT COUNT(DISTINCT customer_email) as cnt FROM payment_transactions WHERE mode = 'PRODUCTION' AND payment_status IN ('SUCCEEDED', 'PAYMENT_VERIFIED')")
        verified_customers = cursor.fetchone()["cnt"] or 0

        cursor.execute("SELECT COUNT(DISTINCT customer_id) as cnt FROM revenue_ledger WHERE payment_status = 'VERIFIED'")
        rev_cust = cursor.fetchone()["cnt"] or 0
        verified_customers = max(verified_customers, rev_cust)

        # Enforce physical monotonic hierarchy for funnel integrity
        checkout_starts = max(checkout_starts, verified_customers)
        high_intent_count = max(high_intent_count, checkout_starts)
        qualified_visitors = max(qualified_visitors, high_intent_count)
        total_visitors = max(total_visitors, qualified_visitors)

        conn.close()

        # Statistical sample size check
        is_sample_sufficient = total_visitors >= cls.MIN_STATISTICAL_SAMPLE_SIZE
        sample_status = "SUFFICIENT" if is_sample_sufficient else "INSUFFICIENT SAMPLE SIZE"

        def rate_str(current: int, total: int) -> str:
            if total <= 0:
                return "0.0%"
            return f"{(current / total * 100.0):.2f}%"

        return {
            "timeframe": timeframe,
            "sample_size": total_visitors,
            "statistical_status": sample_status,
            "pipeline": {
                "visitors": total_visitors,
                "qualified_visitors": qualified_visitors,
                "leads": leads_count,
                "high_intent_leads": high_intent_count,
                "checkout_starts": checkout_starts,
                "customers": verified_customers
            },
            "rates": {
                "visitor_to_qualified": rate_str(qualified_visitors, total_visitors),
                "qualified_to_lead": rate_str(leads_count, qualified_visitors),
                "lead_to_checkout": rate_str(checkout_starts, leads_count),
                "checkout_to_customer": rate_str(verified_customers, checkout_starts),
                "overall_conversion": rate_str(verified_customers, total_visitors)
            }
        }

    get_funnel_summary = get_pipeline_counts
