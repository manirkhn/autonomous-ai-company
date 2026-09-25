"""
Persistent Corporate Memory & Knowledge Base.
Maintains company wisdom, successful patterns, failed experiment retrospectives,
and policy guidelines to prevent repeating past mistakes.
"""

import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core.db import get_connection
from core.audit import AuditLogger

VALID_CATEGORIES = {
    "STRATEGY", "EXPERIMENT", "PRODUCT", "CUSTOMER",
    "MARKETING", "LESSONS_LEARNED", "FAILED_APPROACH",
    "SUCCESSFUL_APPROACH", "PRICING_EXPERIMENT", "CUSTOMER_FEEDBACK",
    "OPERATING_PROCEDURE", "AUTOMATION_WORKFLOW", "APPROVED_POLICY",
    "FINANCIAL_PERFORMANCE", "DECISION_RECORD"
}

class CorporateMemory:
    @staticmethod
    def store_memory(
        category: str,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        author_agent: str = "SYSTEM"
    ) -> str:
        cat = category.upper()
        if cat not in VALID_CATEGORIES:
            cat = "LESSONS_LEARNED"

        memory_id = f"MEM-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO memory (memory_id, category, title, content, metadata, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            memory_id, cat, title, content,
            json.dumps(metadata or {}),
            json.dumps(tags or []),
            now, now
        ))
        conn.commit()
        conn.close()

        AuditLogger.log(
            agent_id=author_agent,
            action="MEMORY_STORED",
            result=f"Memory committed [{cat}]: {title}",
            risk_level="LOW",
            details={"memory_id": memory_id, "category": cat}
        )
        return memory_id

    @staticmethod
    def search_memories(
        query: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        sql = "SELECT * FROM memory WHERE 1=1"
        params = []

        if category:
            sql += " AND category = ?"
            params.append(category.upper())
        if query:
            sql += " AND (title LIKE ? OR content LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])
        if tag:
            sql += " AND tags LIKE ?"
            params.append(f"%{tag}%")

        sql += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        conn.close()

        results = []
        for r in rows:
            results.append({
                "memory_id": r["memory_id"],
                "category": r["category"],
                "title": r["title"],
                "content": r["content"],
                "metadata": json.loads(r["metadata"]) if r["metadata"] else {},
                "tags": json.loads(r["tags"]) if r["tags"] else [],
                "created_at": r["created_at"],
                "updated_at": r["updated_at"]
            })
        return results

    @staticmethod
    def check_past_failure(approach_keyword: str) -> Optional[Dict[str, Any]]:
        """Check if an approach has previously failed, ensuring lessons are surfaced."""
        failures = CorporateMemory.search_memories(
            query=approach_keyword,
            category="FAILED_APPROACH",
            limit=5
        )
        return failures[0] if failures else None
