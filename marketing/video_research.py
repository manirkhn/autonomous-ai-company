"""
Move 1: Video Research & Hook Decoding Engine (AI Social Media Operating System).
Scrapes viral competitor videos across YouTube Shorts, Instagram Reels, and TikTok.
Decodes hooks into archetypes, extracts value structures, and ranks content ideas by retention potential.
"""

import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from core.db import get_connection
from core.audit import AuditLogger

class VideoResearchEngine:
    HOOK_ARCHETYPES = {
        "CURIOSITY_GAP": "Withholds the key insight until the end, creating an irresistible open loop.",
        "CONTRARIAN": "Directly contradicts popular conventional wisdom or common industry advice.",
        "TOOL_TEARDOWN": "Showcases a game-changing or newly released AI tool solving a painful friction point.",
        "WARNING_MISTAKE": "Alerts the viewer of a critical mistake they are currently making.",
        "SECRET_BLUEPRINT": "Reveals an elite insider framework or step-by-step repeatable system."
    }

    @staticmethod
    def init_schema():
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS social_video_research (
                    id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    creator TEXT,
                    title TEXT,
                    transcript TEXT,
                    hook_text TEXT,
                    hook_archetype TEXT,
                    retention_score REAL DEFAULT 0.0,
                    topics_json TEXT,
                    analyzed_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hook_library (
                    id TEXT PRIMARY KEY,
                    archetype TEXT NOT NULL,
                    hook_template TEXT NOT NULL,
                    example_usage TEXT,
                    historical_ctr REAL DEFAULT 0.0,
                    use_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    @classmethod
    def decode_hook(cls, transcript: str) -> Dict[str, Any]:
        """
        Extracts the first 1-3 sentences (first 3-5 seconds of spoken content)
        and classifies its hook archetype and emotional triggers.
        """
        sentences = [s.strip() for s in re.split(r'[.!?\n]', transcript) if s.strip()]
        hook_candidate = " ".join(sentences[:2]) if len(sentences) >= 2 else (sentences[0] if sentences else "")

        archetype = "CURIOSITY_GAP"
        lower = hook_candidate.lower()
        if any(w in lower for w in ["stop", "don't", "mistake", "wrong", "lie", "waste"]):
            archetype = "WARNING_MISTAKE"
        elif any(w in lower for w in ["nobody talks about", "truth about", "why most", "actually"]):
            archetype = "CONTRARIAN"
        elif any(w in lower for w in ["tool", "ai", "github", "open-source", "released", "dropped"]):
            archetype = "TOOL_TEARDOWN"
        elif any(w in lower for w in ["system", "blueprint", "framework", "step", "how to"]):
            archetype = "SECRET_BLUEPRINT"

        # Retention score estimation (0-100) based on urgency and clarity
        word_count = len(hook_candidate.split())
        brevity_score = max(0, 40 - abs(15 - word_count) * 2) # ideal is 10-18 words
        impact_keywords = sum(1 for kw in ["secret", "money", "free", "automated", "fastest", "drop", "crazy"] if kw in lower)
        retention_score = min(99.0, 50.0 + brevity_score + (impact_keywords * 10))

        return {
            "hook_text": hook_candidate,
            "archetype": archetype,
            "retention_score": round(retention_score, 1),
            "word_count": word_count
        }

    @classmethod
    def ingest_video_content(cls, platform: str, url: str, creator: str, title: str, transcript: str) -> Dict[str, Any]:
        cls.init_schema()
        analysis = cls.decode_hook(transcript)
        record_id = f"RES-{int(datetime.now(timezone.utc).timestamp())}"
        now_iso = datetime.now(timezone.utc).isoformat()

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO social_video_research 
                (id, platform, source_url, creator, title, transcript, hook_text, hook_archetype, retention_score, topics_json, analyzed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_id, platform, url, creator, title, transcript,
                analysis["hook_text"], analysis["archetype"], analysis["retention_score"],
                json.dumps(["AI", "Automation", "SaaS", "Productivity"]), now_iso
            ))
            conn.commit()

        AuditLogger.log(
            agent_id="EMP-002-RESEARCH",
            action="VIRAL_VIDEO_HOOK_DECODED",
            result=f"Decoded {platform} video '{title}' -> Archetype: {analysis['archetype']} (Score: {analysis['retention_score']})",
            risk_level="LOW"
        )
        return {
            "research_id": record_id,
            "hook_text": analysis["hook_text"],
            "archetype": analysis["archetype"],
            "retention_score": analysis["retention_score"]
        }

    @classmethod
    def get_top_ranked_hooks(cls, limit: int = 5) -> List[Dict[str, Any]]:
        cls.init_schema()
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, platform, creator, title, hook_text, hook_archetype, retention_score, analyzed_at
                FROM social_video_research
                ORDER BY retention_score DESC, analyzed_at DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [
                {
                    "id": r[0], "platform": r[1], "creator": r[2], "title": r[3],
                    "hook_text": r[4], "archetype": r[5], "retention_score": r[6], "analyzed_at": r[7]
                }
                for r in rows
            ]
