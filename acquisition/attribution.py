"""
Acquisition Source & UTM Attribution Engine (Phase 5H, Section 8).

Tracks and records full-funnel customer journeys:
source -> landing page -> product page -> checkout -> successful payment -> fulfillment.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from core.db import get_connection

class AttributionEngine:
    """
    Manages UTM and referral attribution records across the complete customer journey.
    """

    @classmethod
    def record_touchpoint(
        cls,
        source: str,
        landing_page: Optional[str] = None,
        landing_path: Optional[str] = None,
        medium: str = "",
        campaign: str = "",
        content: str = "",
        term: str = "",
        product_page_visited: int = 1,
        checkout_started: int = 0,
        order_id: Optional[str] = None,
        payment_verified: int = 0,
        fulfilled: int = 0,
        revenue_usd: float = 0.0,
        mode: str = "PRODUCTION",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Records an attribution event into the acquisition_attribution table.
        """
        resolved_landing = landing_page or landing_path or "/store"
        conn = get_connection()
        cursor = conn.cursor()
        attr_id = f"ATTR-{uuid.uuid4().hex[:10].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        cursor.execute("""
        INSERT INTO acquisition_attribution (
            attribution_id, source, medium, campaign, content, term,
            landing_page, product_page_visited, checkout_started,
            order_id, payment_verified, fulfilled, revenue_usd,
            mode, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            attr_id, source, medium, campaign, content, term,
            resolved_landing, product_page_visited, checkout_started,
            order_id, payment_verified, fulfilled, revenue_usd,
            mode, now_iso
        ))
        conn.commit()
        conn.close()

        return {
            "attribution_id": attr_id,
            "touchpoint_id": attr_id,
            "source": source,
            "utm_source": source,
            "medium": medium,
            "campaign": campaign,
            "landing_page": resolved_landing,
            "checkout_started": checkout_started,
            "payment_verified": payment_verified,
            "timestamp": now_iso
        }

    @classmethod
    def link_checkout_session(cls, touchpoint_id: str, checkout_session_id: str) -> Dict[str, Any]:
        """
        Links a customer touchpoint to an active checkout session.
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE acquisition_attribution SET
            checkout_started = 1,
            order_id = ?
        WHERE attribution_id = ?
        """, (checkout_session_id, touchpoint_id))
        conn.commit()
        conn.close()
        return {
            "touchpoint_id": touchpoint_id,
            "checkout_session_id": checkout_session_id,
            "checkout_started": 1
        }

    @classmethod
    def link_order_payment(
        cls,
        order_id: Optional[str] = None,
        checkout_session_id: Optional[str] = None,
        payment_reference: Optional[str] = None,
        amount_usd: float = 29.00,
        revenue_usd: Optional[float] = None,
        channel: Optional[str] = None,
        fulfilled: int = 1,
        mode: str = "PRODUCTION"
    ) -> Dict[str, Any]:
        """
        Updates an existing attribution touchpoint upon successful payment verification.
        """
        final_rev = revenue_usd if revenue_usd is not None else amount_usd
        final_order = order_id or checkout_session_id or "ORD-UNKNOWN"
        conn = get_connection()
        cursor = conn.cursor()
        
        # Try matching by order_id or by checkout_session_id stored in order_id
        cursor.execute("""
        UPDATE acquisition_attribution SET
            payment_verified = 1,
            fulfilled = ?,
            revenue_usd = ?,
            order_id = ?
        WHERE order_id = ? OR order_id = ?
        """, (fulfilled, final_rev, final_order, final_order, checkout_session_id))
        
        if cursor.rowcount == 0:
            # If no matching pre-existing touchpoint, create an attributed payment record
            src = channel or "Direct"
            attr_id = f"ATTR-{uuid.uuid4().hex[:10].upper()}"
            now_iso = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
            INSERT INTO acquisition_attribution (
                attribution_id, source, landing_page, product_page_visited,
                checkout_started, order_id, payment_verified, fulfilled,
                revenue_usd, mode, timestamp
            ) VALUES (?, ?, ?, 1, 1, ?, 1, ?, ?, ?, ?)
            """, (attr_id, src, "/store", final_order, fulfilled, final_rev, mode, now_iso))

        conn.commit()
        conn.close()

        return {
            "status": "ATTRIBUTION_LINKED",
            "order_id": final_order,
            "payment_reference": payment_reference,
            "revenue_usd": final_rev,
            "fulfillment_status": "FULFILLED" if fulfilled == 1 else "PENDING"
        }

    @classmethod
    def get_attribution_summary(cls, mode: str = "PRODUCTION") -> List[Dict[str, Any]]:
        """
        Summarizes touchpoint conversions by source channel.
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT source,
               COUNT(*) as total_touchpoints,
               SUM(product_page_visited) as product_views,
               SUM(checkout_started) as checkouts_initiated,
               SUM(payment_verified) as paid_orders,
               SUM(fulfilled) as fulfilled_orders,
               SUM(CASE WHEN payment_verified = 1 THEN revenue_usd ELSE 0.0 END) as verified_revenue
        FROM acquisition_attribution
        WHERE mode = ?
        GROUP BY source
        ORDER BY paid_orders DESC, total_touchpoints DESC
        """, (mode,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
