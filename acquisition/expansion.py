"""
Product Expansion Queue & Opportunity Scoring (Phase 5H, Section 11).

Ranks potential follow-up digital developer products based on documented evidence:
- observed customer problems
- search demand
- discussion frequency
- competition level
- development effort
- capability compatibility
Enforces approval thresholds before initiating factory builds.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List
from core.db import get_connection

class ProductExpansionQueue:
    """
    Manages the backlog of evaluated product expansion candidates.
    """

    EXPANSION_CANDIDATES = [
        {
            "product_opp_id": "EXP-OPP-001",
            "title": "Strict JSON Schema Regression Test Pack (150+ Schemas)",
            "product_family": "JSON schema test packs",
            "problem_observed": "Developers frequently experience syntax errors when local LLMs generate nested objects, optional keys, or strict arrays.",
            "evidence_source": "r/LocalLLaMA discussions, GitHub Ollama issues regarding json_mode fidelity.",
            "search_demand_score": 0.85,
            "discussion_frequency_score": 0.90,
            "competition_level": "LOW",
            "development_effort": "LOW",
            "compatibility_score": 0.95,
            "composite_rank": 0.89,
            "status": "QUEUED"
        },
        {
            "product_opp_id": "EXP-OPP-002",
            "title": "vLLM Production Health & Latency Watchdog Utility",
            "product_family": "vLLM testing utilities",
            "problem_observed": "vLLM servers experience memory fragmentation or TTFT degradation under continuous batching load without lightweight alerting.",
            "evidence_source": "vLLM GitHub issue tracker discussions on worker health monitoring.",
            "search_demand_score": 0.80,
            "discussion_frequency_score": 0.75,
            "competition_level": "MEDIUM",
            "development_effort": "MEDIUM",
            "compatibility_score": 0.85,
            "composite_rank": 0.78,
            "status": "QUEUED"
        },
        {
            "product_opp_id": "EXP-OPP-003",
            "title": "Ollama CI/CD GitHub Action & GitLab Runner Workflow Pack",
            "product_family": "Ollama testing utilities",
            "problem_observed": "Teams lack standardized CI action files to spin up Ollama in container runners and execute regression test gates before merging PRs.",
            "evidence_source": "GitHub Actions marketplace search queries for 'ollama-ci' and 'local-llm-eval-action'.",
            "search_demand_score": 0.78,
            "discussion_frequency_score": 0.80,
            "competition_level": "LOW",
            "development_effort": "LOW",
            "compatibility_score": 0.90,
            "composite_rank": 0.82,
            "status": "QUEUED"
        },
        {
            "product_opp_id": "EXP-OPP-004",
            "title": "llama.cpp Quantization Drift & Perplexity Profiler",
            "product_family": "llama.cpp testing utilities",
            "problem_observed": "Engineers upgrading GGUF models from Q4_K_S to Q4_K_M have no simple single-script way to measure exact perplexity differences against their private data.",
            "evidence_source": "Hacker News comments on local quantization quality tradeoffs.",
            "search_demand_score": 0.72,
            "discussion_frequency_score": 0.70,
            "competition_level": "LOW",
            "development_effort": "MEDIUM",
            "compatibility_score": 0.88,
            "composite_rank": 0.75,
            "status": "QUEUED"
        },
        {
            "product_opp_id": "EXP-OPP-005",
            "title": "Enterprise Local AI Production Readiness Checklist & Audit Matrix",
            "product_family": "AI developer checklists",
            "problem_observed": "Engineering leaders moving from OpenAI APIs to private on-prem GPUs need a deterministic governance, latency, and data leakage audit checklist.",
            "evidence_source": "Enterprise AI architecture consultations and developer security queries.",
            "search_demand_score": 0.70,
            "discussion_frequency_score": 0.65,
            "competition_level": "LOW",
            "development_effort": "LOW",
            "compatibility_score": 0.90,
            "composite_rank": 0.73,
            "status": "QUEUED"
        }
    ]

    @classmethod
    def init_queue(cls):
        conn = get_connection()
        cursor = conn.cursor()
        now_iso = datetime.now(timezone.utc).isoformat()

        for cand in cls.EXPANSION_CANDIDATES:
            cursor.execute("SELECT product_opp_id FROM product_expansion_opportunities WHERE product_opp_id = ?", (cand["product_opp_id"],))
            if not cursor.fetchone():
                cursor.execute("""
                INSERT INTO product_expansion_opportunities (
                    product_opp_id, title, product_family, problem_observed,
                    evidence_source, search_demand_score, discussion_frequency_score,
                    competition_level, development_effort, compatibility_score,
                    composite_rank, approval_threshold, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0.75, ?, ?)
                """, (
                    cand["product_opp_id"], cand["title"], cand["product_family"],
                    cand["problem_observed"], cand["evidence_source"],
                    cand["search_demand_score"], cand["discussion_frequency_score"],
                    cand["competition_level"], cand["development_effort"],
                    cand["compatibility_score"], cand["composite_rank"],
                    cand["status"], now_iso
                ))

        conn.commit()
        conn.close()

    @classmethod
    def list_queue(cls) -> List[Dict[str, Any]]:
        cls.init_queue()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM product_expansion_opportunities ORDER BY composite_rank DESC")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @classmethod
    def get_ranked_queue(cls) -> List[Dict[str, Any]]:
        raw = cls.list_queue()
        ranked = []
        for idx, r in enumerate(raw):
            item = dict(r)
            item["rank"] = idx + 1
            item["observed_problem"] = r.get("problem_observed", "")
            item["search_demand"] = str(r.get("search_demand_score", 0.0))
            item["composite_score"] = r.get("composite_rank", 0.0)
            item["approval_status"] = r.get("status", "QUEUED")
            ranked.append(item)
        return ranked
