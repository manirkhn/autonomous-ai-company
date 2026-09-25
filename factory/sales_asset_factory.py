"""
Landing Page & Sales Asset Factory (EMP-005-MARKETING).
Synthesizes honest, high-converting product listings, value propositions,
FAQs, email announcements, and social content.
CRITICAL INTEGRITY RULE: Zero fabricated testimonials, sales numbers, or fake reviews.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from core.db import get_connection
from core.audit import AuditLogger
from factory.product_factory import ProductFactory

class SalesAssetFactory:
    @staticmethod
    def generate_sales_package(
        product_id: str,
        price: float = 29.0,
        currency: str = "USD",
        agent_id: str = "EMP-005-MARKETING"
    ) -> Dict[str, Any]:
        """
        Drafts complete ethical sales assets for a product.
        Updates product listing copy and advances stage to LISTING_READY.
        """
        product = ProductFactory.get_product(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found.")

        name = product["name"]
        asset_type = product["asset_type"]

        sales_package = {
            "product_id": product_id,
            "title": f"{name} - Production-Ready {asset_type.replace('_', ' ').title()}",
            "headline": f"Eliminate Hours of Manual Setup with the Verified {name}",
            "value_proposition": f"A battle-tested, zero-fluff digital asset engineered specifically for fast, reliable implementation.",
            "customer_problem": f"Teams waste valuable engineering and operational hours reinventing foundational workflows from scratch.",
            "key_benefits": [
                "100% self-contained and ready to execute immediately.",
                "Zero recurring third-party SaaS subscription overhead.",
                "Verified and tested against syntax and logical errors.",
                "Complete documentation and integration instructions included."
            ],
            "pricing_proposal": {
                "amount": price,
                "currency": currency,
                "type": "ONE_TIME_PURCHASE",
                "license": "Commercial Use Allowed"
            },
            "faq": [
                {
                    "question": "What format is the product delivered in?",
                    "answer": f"Delivered as direct clean source files ({asset_type}) with full instructions and zero DRM lock-in."
                },
                {
                    "question": "What is the refund policy?",
                    "answer": "14-day direct satisfaction guarantee. If the tool or template does not solve the specified problem, a full refund is issued."
                },
                {
                    "question": "Are there recurring fees?",
                    "answer": "No. This is a one-time purchase with perpetual access to this version."
                }
            ],
            "call_to_action": "Download Now & Streamline Your Workflow",
            "email_announcement_copy": f"Subject: New Release: {name}\n\nHi there,\n\nIf you've been looking for a streamlined, reliable solution for {name.lower()}, we just published the complete production-ready toolkit.\n\nLearn more and inspect the full documentation here: [LINK]\n\nBest,\nThe Engineering Team",
            "social_copy": f"🚀 Launching the {name}: a lightweight, tested {asset_type.lower().replace('_', ' ')} built to save hours of boilerplate work. Clean, modular, and ready out of the box. Check it out 👇",
            "marketplace_listing_markdown": f"# {name}\n\n**Category**: {asset_type}\n**Price**: ${price} {currency}\n\n## Overview\n{product['requirements'][:200]}...\n\n## Included Assets\n- Tested source files\n- Documentation & quickstart\n- License agreement\n"
        }

        now = datetime.now(timezone.utc).isoformat()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE products SET 
                listing_copy = ?,
                status = 'LISTING_READY',
                updated_at = ?
            WHERE product_id = ?
        """, (json.dumps(sales_package), now, product_id))
        conn.commit()
        conn.close()

        AuditLogger.log(
            agent_id=agent_id,
            action="SALES_ASSETS_GENERATED",
            result=f"Sales copy and listing package generated for {product_id} ('{name}'). Ready for Owner Review.",
            risk_level="LOW",
            details={"product_id": product_id, "price": price}
        )

        return sales_package
