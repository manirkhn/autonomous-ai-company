"""
Audit Logging and Real-Time Event System.
Every important AI action, decision, approval, and firewall event is recorded immutably.
Supports real-time SSE / WebSocket event streaming to the Owner Command Center.
"""

import uuid
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from .db import get_connection

class EventBus:
    """In-memory pub-sub event queue for real-time live feed to dashboard."""
    _subscribers = set()

    @classmethod
    def subscribe(cls, queue: asyncio.Queue):
        cls._subscribers.add(queue)

    @classmethod
    def unsubscribe(cls, queue: asyncio.Queue):
        cls._subscribers.discard(queue)

    @classmethod
    def broadcast(cls, event: Dict[str, Any]):
        for queue in list(cls._subscribers):
            try:
                queue.put_nowait(event)
            except Exception:
                cls._subscribers.discard(queue)

class AuditLogger:
    @staticmethod
    def log(
        agent_id: str,
        action: str,
        result: str,
        risk_level: str = "LOW",
        cost: float = 0.0,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Record an immutable audit log entry and broadcast to real-time feed.
        """
        log_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        details_str = json.dumps(details or {})

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_logs (log_id, timestamp, agent_id, action, result, risk_level, cost, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (log_id, now, agent_id, action, result, risk_level, cost, details_str))
        conn.commit()
        conn.close()

        # Broadcast event to connected dashboard clients
        event_payload = {
            "log_id": log_id,
            "timestamp": now,
            "agent_id": agent_id,
            "action": action,
            "result": result,
            "risk_level": risk_level,
            "cost": cost,
            "details": details or {}
        }
        EventBus.broadcast(event_payload)
        return log_id

    @staticmethod
    def get_recent_logs(limit: int = 50, risk_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        if risk_filter:
            cursor.execute("""
                SELECT * FROM audit_logs WHERE risk_level = ? ORDER BY timestamp DESC LIMIT ?
            """, (risk_filter.upper(), limit))
        else:
            cursor.execute("""
                SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?
            """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for r in rows:
            results.append({
                "log_id": r["log_id"],
                "timestamp": r["timestamp"],
                "agent_id": r["agent_id"],
                "action": r["action"],
                "result": r["result"],
                "risk_level": r["risk_level"],
                "cost": r["cost"],
                "details": json.loads(r["details"]) if r["details"] else {}
            })
        return results
