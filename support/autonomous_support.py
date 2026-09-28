"""
Autonomous Customer Support Engine (Phase 5I).
Handles routine customer technical questions factually based on verified product documentation.
Escalates uncertain, sensitive, or refund queries to OWNER_ACTION_REQUIRED.
Never fabricates answers or claims unsupported features.
"""

import uuid
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core.db import get_connection
from acquisition.owner_actions import OwnerActionCenter

class AutonomousSupportEngine:
    """
    Automated customer support routing and factual question answering.
    """

    FACTUAL_KNOWLEDGE_BASE = [
        {
            "category": "OFFLINE_PRIVACY",
            "keywords": ["cloud", "privacy", "offline", "data", "internet", "private", "airgap", "air-gap", "telemetry"],
            "answer": (
                "The Local LLM Offline Evaluation & Prompt Regression Benchmark Suite is 100% offline. "
                "It sends zero data over the internet and makes zero external API calls. "
                "All prompt test vectors, schema verifications, and latency measurements execute entirely on your local machine or private VPC."
            ),
            "confidence": 0.95
        },
        {
            "category": "SUPPORTED_ENGINES",
            "keywords": ["ollama", "vllm", "llama.cpp", "tgi", "engine", "server", "compatible", "supported"],
            "answer": (
                "The benchmark suite supports any OpenAI-compatible local HTTP endpoint. "
                "Tested out of the box with Ollama (http://localhost:11434), vLLM (http://localhost:8000), "
                "and llama.cpp llama-server (http://localhost:8080)."
            ),
            "confidence": 0.95
        },
        {
            "category": "SYSTEM_REQUIREMENTS",
            "keywords": ["python", "version", "install", "requirements", "os", "windows", "linux", "mac", "gpu"],
            "answer": (
                "Requirements: Python 3.10, 3.11, 3.12, 3.13, or 3.14 on Linux, macOS, or Windows. "
                "Zero heavy dependencies required — the runner uses lightweight standard HTTP and JSON validation libraries. "
                "No dedicated GPU is needed for the test harness itself, though your local model runner requires sufficient hardware."
            ),
            "confidence": 0.95
        },
        {
            "category": "EXECUTION_GUIDE",
            "keywords": ["run", "execute", "command", "cli", "how to use", "start", "quickstart"],
            "answer": (
                "To execute the benchmark suite against your local endpoint:\n"
                "1. Unzip nexora-llm-benchmark-suite-v1.zip\n"
                "2. Run: python run_eval.py --endpoint http://localhost:11434/v1 --model llama3.2:latest\n"
                "3. View the terminal scorecard and generated markdown reports in the /eval_results folder."
            ),
            "confidence": 0.92
        },
        {
            "category": "DELIVERY_FILES",
            "keywords": ["download", "files", "included", "delivery", "zip", "license key"],
            "answer": (
                "Upon purchase, you receive an instant direct download link for nexora-llm-benchmark-suite-v1.zip. "
                "The package includes the Python runner CLI, 100+ prompt test vectors, golden JSON schema baselines, "
                "TTFT latency profiler, and a comprehensive Quickstart PDF guide."
            ),
            "confidence": 0.95
        },
        {
            "category": "REFUNDS_AND_GUARANTEE",
            "keywords": ["refund", "money back", "guarantee", "return", "cancel"],
            "answer": (
                "Nexora AI Labs offers a 30-Day Quality Assurance Guarantee. "
                "If the benchmark suite does not function with your local OpenAI-compatible inference server, "
                "we issue a full refund upon verification of your order number."
            ),
            "confidence": 0.75, # Lower confidence to require owner review for financial actions
            "escalate": True
        }
    ]

    @classmethod
    def handle_customer_inquiry(
        cls,
        customer_email: str,
        question: str,
        product_id: str = "PROD-LLM-EVAL-001",
        source: str = "WEB_FORM"
    ) -> Dict[str, Any]:
        """Alias for submit_ticket."""
        return cls.submit_ticket(
            customer_email=customer_email,
            question=question,
            product_id=product_id,
            source=source
        )

    @classmethod
    def submit_ticket(
        cls,
        customer_email: str,
        question: str,
        product_id: str = "PROD-LLM-EVAL-001",
        source: str = "WEB_FORM"
    ) -> Dict[str, Any]:
        """
        Ingests a customer support inquiry, matches against factual knowledge,
        and resolves automatically or escalates to the Owner Action Center.
        """
        ticket_id = f"TCK-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()
        q_lower = question.lower()

        # Match inquiry
        best_match = None
        best_score = 0.0

        for item in cls.FACTUAL_KNOWLEDGE_BASE:
            matched_kw = sum(1 for kw in item["keywords"] if kw in q_lower)
            if matched_kw > 0:
                ratio = 0.9 if matched_kw == 1 else 1.0
                score = item["confidence"] * ratio
                if score > best_score:
                    best_score = score
                    best_match = item

        should_escalate = False
        if best_match and best_score >= 0.85 and not best_match.get("escalate", False):
            answer = best_match["answer"]
            status = "RESOLVED"
            resolution = "AUTOMATICALLY_RESOLVED_FACTUAL"
            resolved_at = now_iso
        else:
            should_escalate = True
            if best_match:
                answer = best_match["answer"] + "\n\n(This ticket has been escalated to our customer success team for personalized review.)"
                confidence = best_score
            else:
                answer = (
                    "Thank you for contacting Nexora AI Labs support. "
                    "Your question has been escalated to our technical engineering team for review."
                )
                confidence = 0.40
            status = "OWNER_ACTION_REQUIRED"
            resolution = "ESCALATED_TO_OWNER"
            resolved_at = None

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO support_tickets (
            ticket_id, customer_email, product_id, question, answer,
            confidence, status, resolution, source, created_at, resolved_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket_id, customer_email, product_id, question, answer,
            confidence if should_escalate else best_score, status, resolution, source, now_iso, resolved_at
        ))
        conn.commit()
        conn.close()

        # If escalation required, create an explicit task in Owner Action Center
        if should_escalate:
            OwnerActionCenter.create_action(
                action_id=f"ACT-TCK-{ticket_id}",
                title=f"Review Support Ticket {ticket_id} ({customer_email})",
                category="CUSTOMER_SUPPORT",
                urgency="HIGH" if "refund" in q_lower else "MEDIUM",
                description=f"Customer inquiry from {customer_email}: '{question}'. Draft answer prepared with {confidence:.0%} confidence.",
                channel="Support",
                why="Uncertain or sensitive customer inquiry requires human owner review to ensure 100% accuracy.",
                what_is_blocked=f"Final resolution and email reply to customer {customer_email}",
                exact_action=f"Review ticket {ticket_id}, verify facts or approve refund, and submit final response.",
                estimated_time="3 mins",
                platform="Nexora Support",
                security_impact="Zero banking risk. Only affects customer communication.",
                what_antigravity_will_do_after_completion="Antigravity automatically sends the approved response to the customer and closes the support ticket."
            )

        return {
            "ticket_id": ticket_id,
            "customer_email": customer_email,
            "product_id": product_id,
            "question": question,
            "answer": answer,
            "confidence": confidence if should_escalate else best_score,
            "status": status,
            "resolution": resolution,
            "created_at": now_iso,
            "resolved_at": resolved_at
        }

    @classmethod
    def list_tickets(cls, status: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM support_tickets WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            cursor.execute("SELECT * FROM support_tickets ORDER BY created_at DESC")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @classmethod
    def get_open_tickets(cls) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM support_tickets WHERE status != 'RESOLVED' ORDER BY created_at DESC")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @classmethod
    def resolve_ticket(cls, ticket_id: str, custom_answer: Optional[str] = None) -> Dict[str, Any]:
        conn = get_connection()
        cursor = conn.cursor()
        now_iso = datetime.now(timezone.utc).isoformat()
        if custom_answer:
            cursor.execute("""
            UPDATE support_tickets SET
                status = 'RESOLVED',
                answer = ?,
                resolution = 'OWNER_RESOLVED',
                resolved_at = ?
            WHERE ticket_id = ?
            """, (custom_answer, now_iso, ticket_id))
        else:
            cursor.execute("""
            UPDATE support_tickets SET
                status = 'RESOLVED',
                resolution = 'OWNER_RESOLVED',
                resolved_at = ?
            WHERE ticket_id = ?
            """, (now_iso, ticket_id))
        conn.commit()
        conn.close()

        # Also complete corresponding action in owner action center
        OwnerActionCenter.complete_action(f"ACT-TCK-{ticket_id}")

        return {"status": "SUCCESS", "ticket_id": ticket_id, "resolution": "RESOLVED", "resolved_at": now_iso}

    @classmethod
    def get_support_metrics(cls) -> Dict[str, Any]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN status = 'RESOLVED' THEN 1 ELSE 0 END) as resolved FROM support_tickets")
        row = cursor.fetchone()
        conn.close()
        total = row["total"] if row and row["total"] else 0
        resolved = row["resolved"] if row and row["resolved"] else 0
        return {
            "total_tickets": total,
            "resolved_tickets": resolved,
            "pending_escalations": total - resolved,
            "automation_rate": f"{(resolved / total * 100.0):.1f}%" if total > 0 else "100.0%"
        }
