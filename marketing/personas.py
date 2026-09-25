"""
Customer Persona Engine & Grounded Target Segmentation (Phase 5E, Section 11).

Researches and structures legitimate customer personas for:
'Local LLM Offline Evaluation & Prompt Regression Benchmark Suite' ($29 USD / AED 106.50).

CRITICAL INVARIANT:
Clearly distinguish VERIFIED_SIGNAL (observed developer pain points) from HYPOTHESIS.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core.db import get_connection

DEFAULT_PERSONAS = [
    {
        "persona_id": "PER-001-LOCAL-DEV",
        "name": "Local LLM Software Engineer",
        "target_problem": "Cannot deterministically measure prompt regression when switching or quantizing local models (Ollama, llama.cpp, vLLM).",
        "evidence_type": "VERIFIED_SIGNAL",
        "evidence_notes": "Observed in GitHub issues & r/LocalLLaMA: developers complain about silent prompt degradation after updating local model weights.",
        "likely_use_case": "Automated CLI test suite run before deploying internal enterprise tools.",
        "relevant_channel": "GitHub Repositories, r/LocalLLaMA, Hacker News",
        "acquisition_method": "Free technical benchmarking guide + open-source CLI runner.",
        "objections": "Can I build this myself in Python? (Answer: Yes, but this saves 40+ engineering hours with pre-packaged regression test cases).",
        "offer_angle": "Instant offline benchmark suite with zero cloud API token leakage."
    },
    {
        "persona_id": "PER-002-AI-APP-BUILDER",
        "name": "Production AI Application Builder",
        "target_problem": "Client applications break when system prompts are modified, with no automated CI/CD safety net.",
        "evidence_type": "VERIFIED_SIGNAL",
        "evidence_notes": "Observed on Discord AI dev groups: teams struggle to test prompt variations across multiple test datasets.",
        "likely_use_case": "Pre-commit hook and GitHub Actions regression validation.",
        "relevant_channel": "AI Developer Communities, LangChain/LlamaIndex forums",
        "acquisition_method": "Educational comparison posts showing regression catch rate.",
        "objections": "Is this compatible with Ollama? (Answer: Native Ollama and REST API support out of the box).",
        "offer_angle": "Never ship a broken prompt update to production again."
    },
    {
        "persona_id": "PER-003-ENTERPRISE-CONSULTANT",
        "name": "AI Technical Consultant / Solutions Architect",
        "target_problem": "Needs to provide empirical, offline benchmarking proof to privacy-conscious enterprise clients.",
        "evidence_type": "HYPOTHESIS",
        "evidence_notes": "Consultants pitch local on-premise AI deployments to regulated banks/healthcare, needing objective performance evidence.",
        "likely_use_case": "Client audit reports and local model bake-offs.",
        "relevant_channel": "LinkedIn Technical Articles, Direct B2B Outreach",
        "acquisition_method": "Whitepaper / sample offline evaluation report deliverable.",
        "objections": "Does it require cloud internet access? (Answer: 100% offline, zero telemetry).",
        "offer_angle": "Client-ready offline evaluation reports for air-gapped deployments."
    }
]

class CustomerPersonaEngine:
    """
    Manages grounded customer personas and segmentation hypotheses.
    """

    @classmethod
    def initialize_personas(cls) -> List[Dict[str, Any]]:
        """Seeds default grounded personas if none exist."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM customer_personas")
        cnt = cursor.fetchone()["cnt"]

        if cnt == 0:
            now = datetime.now(timezone.utc).isoformat()
            for p in DEFAULT_PERSONAS:
                cursor.execute("""
                INSERT INTO customer_personas (
                    persona_id, name, target_problem, evidence_type,
                    evidence_notes, likely_use_case, relevant_channel,
                    acquisition_method, objections, offer_angle, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    p["persona_id"], p["name"], p["target_problem"], p["evidence_type"],
                    p["evidence_notes"], p["likely_use_case"], p["relevant_channel"],
                    p["acquisition_method"], p["objections"], p["offer_angle"], now
                ))
            conn.commit()

        cursor.execute("SELECT * FROM customer_personas ORDER BY persona_id ASC")
        rows = []
        for r in cursor.fetchall():
            d = dict(r)
            d["signal_type"] = d.get("evidence_type", "HYPOTHESIS")
            d["problem"] = d.get("target_problem", "")
            d["potential_offer_angle"] = d.get("offer_angle", "")
            rows.append(d)
        conn.close()
        return rows

    @classmethod
    def get_all_personas(cls) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customer_personas ORDER BY persona_id ASC")
        rows = []
        for r in cursor.fetchall():
            d = dict(r)
            d["signal_type"] = d.get("evidence_type", "HYPOTHESIS")
            d["problem"] = d.get("target_problem", "")
            d["potential_offer_angle"] = d.get("offer_angle", "")
            rows.append(d)
        conn.close()
        if not rows:
            return cls.initialize_personas()
        return rows
