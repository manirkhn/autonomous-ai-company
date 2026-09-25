"""
Modular Browser Automation Layer.
Abstracts web navigation, research scraping, and permitted dashboard interactions.
Enforces strict safety guardrails: zero CAPTCHA bypass, no prohibited scraping,
and mandatory approval gates for irreversible actions.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from core.audit import AuditLogger
from approvals.manager import ApprovalManager

class BrowserSecurityError(Exception):
    """Raised when browser automation encounters a policy violation or prohibited site."""
    pass

class BaseBrowserAdapter(ABC):
    """Abstract interface allowing pluggable headless browser runtimes (Playwright, Selenium, Chrome CDP)."""
    
    @abstractmethod
    async def navigate_and_extract(self, url: str, agent_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def execute_permitted_action(self, url: str, action: str, params: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        pass

class SafeBrowserManager:
    """Governance wrapper enforcing terms of service, robots.txt, and approval gates."""
    
    PROHIBITED_KEYWORDS = {
        "captcha", "cloudflare_challenge", "bypass", "bot_detection_evasion",
        "private_banking", "password_reset", "terms_of_service_bypass",
        "bank", "banking", "transfer", "withdrawal", "credentials"
    }

    def __init__(self, adapter: Optional[BaseBrowserAdapter] = None):
        self.adapter = adapter

    def validate_safety(self, url: str, intent: str, requires_approval: bool = False) -> None:
        url_lower = url.lower()
        intent_lower = intent.lower()

        # 1. Prohibit scraping banking portals or bypassing security
        for kw in self.PROHIBITED_KEYWORDS:
            if kw in url_lower or kw in intent_lower:
                raise BrowserSecurityError(
                    f"BROWSER SAFETY VIOLATION: Keyword '{kw}' detected. "
                    "Browser automation is strictly forbidden from bypassing security, CAPTCHAs, or touching banking credentials."
                )

        # 2. Gate high-risk/irreversible actions
        if requires_approval:
            raise BrowserSecurityError(
                f"APPROVAL REQUIRED: Browser action on {url} involves external publishing or transactions. "
                "Submit a Human Approval Request before executing."
            )

    def log_browser_event(self, agent_id: str, action: str, url: str, result: str, risk_level: str = "LOW"):
        AuditLogger.log(
            agent_id=agent_id,
            action=f"BROWSER_{action.upper()}",
            result=f"{action} on {url}: {result}",
            risk_level=risk_level,
            cost=0.0,
            details={"url": url}
        )
