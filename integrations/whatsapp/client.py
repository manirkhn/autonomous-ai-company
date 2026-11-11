"""Thin client for Meta's WhatsApp Cloud API (official, no middleman)."""

from typing import Any, Dict, List, Optional

import httpx

from .config import WhatsAppConfig


class WhatsAppError(RuntimeError):
    pass


class WhatsAppClient:
    def __init__(self, config: Optional[WhatsAppConfig] = None, http: Optional[httpx.Client] = None):
        self.config = config or WhatsAppConfig()
        self._http = http

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.config.can_send:
            raise WhatsAppError("WhatsApp not configured: set WA_ACCESS_TOKEN and WA_PHONE_NUMBER_ID")
        headers = {"Authorization": f"Bearer {self.config.access_token}"}
        url = f"{self.config.graph_base}/{path}"
        http = self._http or httpx.Client(timeout=20.0)
        try:
            resp = http.post(url, json=payload, headers=headers)
        finally:
            if self._http is None:
                http.close()
        data = resp.json() if resp.content else {}
        if resp.status_code >= 400:
            msg = data.get("error", {}).get("message", resp.text)
            raise WhatsAppError(f"Graph API {resp.status_code}: {msg}")
        return data

    def send_text(self, to: str, body: str, reply_to: Optional[str] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": body[:4096]},
        }
        if reply_to:
            payload["context"] = {"message_id": reply_to}
        return self._post("messages", payload)

    def send_template(self, to: str, name: str, language: str = "en",
                      body_params: Optional[List[str]] = None) -> Dict[str, Any]:
        """Business-initiated message (outside the 24h window) must use an approved template."""
        template: Dict[str, Any] = {"name": name, "language": {"code": language}}
        if body_params:
            template["components"] = [{
                "type": "body",
                "parameters": [{"type": "text", "text": p} for p in body_params],
            }]
        return self._post("messages", {
            "messaging_product": "whatsapp", "to": to, "type": "template", "template": template,
        })

    def mark_read(self, message_id: str) -> Dict[str, Any]:
        return self._post("messages", {
            "messaging_product": "whatsapp", "status": "read", "message_id": message_id,
        })
