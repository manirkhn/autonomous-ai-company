"""
Internal Capability Marketplace (Part 24).
Catalogs all available technologies, libraries, tools, and skills.
Tracks provider types, security ratings, setup times, and free vs paid classifications.
"""

from typing import Dict, Any, List, Optional
from core.db import get_connection

DEFAULT_MARKETPLACE_ITEMS = [
    {
        "item_id": "CAP-001-SQLITE",
        "name": "SQLite Zero-Config Database",
        "description": "Embedded, zero-dependency relational database engine.",
        "provider": "SQLite.org",
        "type": "NATIVE_OSS",
        "is_paid": 0,
        "cost": 0.0,
        "dependencies": "python standard library",
        "reliability": 1.0,
        "security_score": 1.0,
        "permissions": "filesystem_read_write",
        "setup_time": "Instant (0 min)",
        "maintenance": "Zero",
        "business_value": "Core corporate persistent data store with zero hosting bill.",
        "status": "INSTALLED"
    },
    {
        "item_id": "CAP-002-FASTAPI",
        "name": "FastAPI Web Framework",
        "description": "High-performance asynchronous REST API and SSE streaming gateway.",
        "provider": "Tiangolo / Open Source",
        "type": "OSS_LIBRARY",
        "is_paid": 0,
        "cost": 0.0,
        "dependencies": "fastapi, uvicorn, pydantic",
        "reliability": 0.99,
        "security_score": 0.98,
        "permissions": "network_listen_local",
        "setup_time": "1 minute",
        "maintenance": "Low",
        "business_value": "Powers the Owner Command Center and real-time live telemetry stream.",
        "status": "INSTALLED"
    },
    {
        "item_id": "CAP-003-WHISPER",
        "name": "OpenAI Whisper (Local Speech-to-Text)",
        "description": "State-of-the-art open-source audio transcription running locally.",
        "provider": "OpenAI / whisper.cpp",
        "type": "OSS_MODEL",
        "is_paid": 0,
        "cost": 0.0,
        "dependencies": "whisper.cpp / ffmpeg",
        "reliability": 0.96,
        "security_score": 1.0,
        "permissions": "cpu_compute",
        "setup_time": "5 minutes",
        "maintenance": "Low",
        "business_value": "Zero-cost voicemail and customer call transcription.",
        "status": "AVAILABLE"
    },
    {
        "item_id": "CAP-004-PIPER",
        "name": "Piper Neural TTS (Local Speech Synthesis)",
        "description": "Fast, high-quality, local neural text-to-speech voice generator.",
        "provider": "Rhasspy OSS",
        "type": "OSS_MODEL",
        "is_paid": 0,
        "cost": 0.0,
        "dependencies": "piper-tts",
        "reliability": 0.97,
        "security_score": 1.0,
        "permissions": "cpu_compute",
        "setup_time": "5 minutes",
        "maintenance": "Low",
        "business_value": "Zero-cost voice prompt generation for customer support and tutorials.",
        "status": "AVAILABLE"
    },
    {
        "item_id": "CAP-005-PLAYWRIGHT",
        "name": "Playwright Headless Browser Sandbox",
        "description": "Cross-browser automation engine for market research and verification.",
        "provider": "Microsoft OSS",
        "type": "OSS_FRAMEWORK",
        "is_paid": 0,
        "cost": 0.0,
        "dependencies": "playwright",
        "reliability": 0.98,
        "security_score": 0.95,
        "permissions": "sandbox_browser_network",
        "setup_time": "3 minutes",
        "maintenance": "Medium",
        "business_value": "Enables automated verification and compliant public research gathering.",
        "status": "AVAILABLE"
    }
]

class CapabilityMarketplaceCatalog:
    @staticmethod
    def initialize_marketplace():
        conn = get_connection()
        cursor = conn.cursor()
        for item in DEFAULT_MARKETPLACE_ITEMS:
            cursor.execute("SELECT item_id FROM capability_marketplace WHERE item_id = ?", (item["item_id"],))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO capability_marketplace (
                        item_id, name, description, provider, type, is_paid,
                        cost, dependencies, reliability, security_score,
                        permissions, setup_time, maintenance, business_value, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item["item_id"], item["name"], item["description"], item["provider"],
                    item["type"], item["is_paid"], item["cost"], item["dependencies"],
                    item["reliability"], item["security_score"], item["permissions"],
                    item["setup_time"], item["maintenance"], item["business_value"], item["status"]
                ))
        conn.commit()
        conn.close()

    @staticmethod
    def get_catalog() -> List[Dict[str, Any]]:
        CapabilityMarketplaceCatalog.initialize_marketplace()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM capability_marketplace ORDER BY item_id ASC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
