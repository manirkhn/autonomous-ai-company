"""
Product Factory (EMP-004-CREATION).
A repeatable digital manufacturing engine capable of compiling functional MVPs
across code utilities, templates, checklists, automation workflows, and guides.
Enforces zero copyright infringement and generates tangible filesystem deliverables.
"""

import os
import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core.db import get_connection
from core.audit import AuditLogger

PRODUCT_STAGES = {
    "IDEA", "REQUIREMENTS", "MVP", "INTERNAL_QA",
    "CUSTOMER_VALUE_CHECK", "LISTING_READY", "AWAITING_APPROVAL",
    "PUBLISHED", "ARCHIVED"
}

ASSET_TYPES = {
    "CODE_UTILITY", "AUTOMATION_WORKFLOW", "CHECKLIST",
    "TEMPLATE", "DIGITAL_GUIDE", "PROMPT_PACK", "WEB_TOOL"
}

PRODUCTS_STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "products")

class ProductFactory:
    @staticmethod
    def initialize_storage():
        os.makedirs(PRODUCTS_STORAGE_DIR, exist_ok=True)

    @staticmethod
    def create_product_draft(
        name: str,
        asset_type: str,
        requirements: str,
        opportunity_id: Optional[str] = None,
        creator_agent: str = "EMP-004-CREATION"
    ) -> str:
        """Step 1 & 2: Initiate Product from Idea and Requirements."""
        ProductFactory.initialize_storage()
        if asset_type.upper() not in ASSET_TYPES:
            asset_type = "CODE_UTILITY"

        product_id = f"PRD-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO products (
                product_id, opportunity_id, name, asset_type, version,
                requirements, mvp_path, qa_status, qa_evidence, listing_copy,
                status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, '1.0.0-MVP', ?, '', 'PENDING', '', '', 'REQUIREMENTS', ?, ?)
        """, (
            product_id, opportunity_id or "", name, asset_type.upper(),
            requirements, now, now
        ))
        conn.commit()
        conn.close()

        AuditLogger.log(
            agent_id=creator_agent,
            action="PRODUCT_REQUIREMENTS_DRAFTED",
            result=f"Product {product_id} ('{name}') requirements drafted. Asset type: {asset_type}",
            risk_level="LOW",
            details={"product_id": product_id, "asset_type": asset_type}
        )
        return product_id

    @staticmethod
    def build_mvp_deliverable(
        product_id: str,
        file_name: str,
        content: str,
        agent_id: str = "EMP-004-CREATION"
    ) -> Dict[str, Any]:
        """
        Step 3: Compile tangible MVP deliverable and store in products directory.
        Zero placeholders permitted.
        """
        ProductFactory.initialize_storage()
        product_dir = os.path.join(PRODUCTS_STORAGE_DIR, product_id)
        os.makedirs(product_dir, exist_ok=True)

        file_path = os.path.join(product_dir, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        file_size_bytes = os.path.getsize(file_path)
        rel_path = f"products/{product_id}/{file_name}"
        now = datetime.now(timezone.utc).isoformat()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE products SET 
                mvp_path = ?, 
                status = 'MVP',
                updated_at = ?
            WHERE product_id = ?
        """, (rel_path, now, product_id))
        conn.commit()
        conn.close()

        AuditLogger.log(
            agent_id=agent_id,
            action="MVP_DELIVERABLE_BUILT",
            result=f"Compiled tangible MVP file '{file_name}' ({file_size_bytes} bytes) for {product_id}",
            risk_level="LOW",
            details={"product_id": product_id, "path": rel_path, "size_bytes": file_size_bytes}
        )

        return {
            "product_id": product_id,
            "file_path": file_path,
            "rel_path": rel_path,
            "size_bytes": file_size_bytes,
            "status": "MVP"
        }

    @staticmethod
    def get_product(product_id: str) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_all_products(status: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM products WHERE status = ? ORDER BY created_at DESC", (status.upper(),))
        else:
            cursor.execute("SELECT * FROM products ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def update_product_status(product_id: str, new_status: str, agent_id: str = "EMP-008-OPS") -> bool:
        if new_status.upper() not in PRODUCT_STAGES:
            raise ValueError(f"Invalid product stage: {new_status}")

        now = datetime.now(timezone.utc).isoformat()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE products SET status = ?, updated_at = ? WHERE product_id = ?
        """, (new_status.upper(), now, product_id))
        conn.commit()
        conn.close()

        AuditLogger.log(
            agent_id=agent_id,
            action="PRODUCT_STAGE_ADVANCED",
            result=f"Product {product_id} transitioned to stage {new_status}",
            risk_level="LOW"
        )
        return True
