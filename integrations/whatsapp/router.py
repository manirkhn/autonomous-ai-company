"""FastAPI routes: Meta webhook + owner endpoints."""

import hashlib
import hmac
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from . import store
from .agent import decide_reply
from .client import WhatsAppClient, WhatsAppError
from .config import WhatsAppConfig

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])
_tables_ready = False


def _ensure_tables() -> None:
    global _tables_ready
    if not _tables_ready:
        store.init_whatsapp_tables()
        _tables_ready = True


def verify_signature(app_secret: str, raw_body: bytes, header: Optional[str]) -> bool:
    if not app_secret:
        return False
    if not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(app_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header.split("=", 1)[1])


def extract_messages(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flatten Meta's webhook payload into simple inbound messages."""
    out: List[Dict[str, Any]] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            names = {c.get("wa_id"): c.get("profile", {}).get("name") for c in value.get("contacts", [])}
            for m in value.get("messages", []):
                mtype = m.get("type", "text")
                text, media_id = "", None
                if mtype == "text":
                    text = m.get("text", {}).get("body", "")
                elif mtype in ("image", "document", "video", "audio"):
                    media = m.get(mtype, {})
                    media_id = media.get("id")
                    text = media.get("caption", "") or media.get("filename", "")
                elif mtype == "interactive":
                    inter = m.get("interactive", {})
                    text = (inter.get("button_reply") or inter.get("list_reply") or {}).get("title", "")
                elif mtype == "button":
                    text = m.get("button", {}).get("text", "")
                out.append({
                    "id": m.get("id"), "contact": m.get("from"), "name": names.get(m.get("from")),
                    "type": mtype, "text": text, "media_id": media_id, "raw": m,
                })
    return out


def process_inbound(msg: Dict[str, Any], cfg: WhatsAppConfig, client: WhatsAppClient) -> Dict[str, Any]:
    _ensure_tables()
    is_new = store.save_message("in", msg["contact"], msg.get("text"), msg.get("type", "text"),
                                msg.get("id"), msg.get("name"), msg.get("media_id"), msg.get("raw"))
    if not is_new:
        return {"reason": "duplicate", "reply": None}
    decision = decide_reply(cfg, msg)
    if decision["reply"] and cfg.can_send:
        try:
            if msg.get("id"):
                client.mark_read(msg["id"])
            res = client.send_text(msg["contact"], decision["reply"], reply_to=msg.get("id"))
            out_id = (res.get("messages") or [{}])[0].get("id")
            store.save_message("out", msg["contact"], decision["reply"], "text", out_id)
        except WhatsAppError as exc:
            decision["send_error"] = str(exc)
    elif decision["reply"]:
        # Not configured to send: still record what would have been sent.
        store.save_message("out", msg["contact"], decision["reply"], "text", None)
        decision["send_error"] = "not_configured"
    return decision


@router.get("/webhook")
def verify_webhook(hub_mode: str = Query(None, alias="hub.mode"),
                   hub_token: str = Query(None, alias="hub.verify_token"),
                   hub_challenge: str = Query(None, alias="hub.challenge")):
    cfg = WhatsAppConfig()
    if hub_mode == "subscribe" and cfg.verify_token and hub_token == cfg.verify_token:
        return PlainTextResponse(hub_challenge or "")
    raise HTTPException(status_code=403, detail="verification failed")


@router.post("/webhook")
async def receive_webhook(request: Request, background: BackgroundTasks):
    cfg = WhatsAppConfig()
    raw = await request.body()
    if not verify_signature(cfg.app_secret, raw, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(status_code=401, detail="bad signature")
    payload = json.loads(raw or b"{}")
    client = WhatsAppClient(cfg)
    for msg in extract_messages(payload):
        background.add_task(process_inbound, msg, cfg, client)
    # Meta needs a fast 200, otherwise it retries.
    return {"status": "received"}


class SendRequest(BaseModel):
    to: str
    text: Optional[str] = None
    template: Optional[str] = None
    language: str = "en"
    params: Optional[List[str]] = None


@router.get("/status")
def wa_status():
    _ensure_tables()
    cfg = WhatsAppConfig()
    return {
        "configured": cfg.can_send,
        "webhook_secured": bool(cfg.app_secret and cfg.verify_token),
        "persona": cfg.persona,
        "autoreply": cfg.autoreply,
        "paused": store.get_state("paused", "0") == "1",
        "allowlist_size": len(cfg.allowed_numbers),
        "open_requests": len(store.list_requests("new")),
    }


@router.get("/requests")
def wa_requests(status: Optional[str] = None):
    _ensure_tables()
    return {"requests": store.list_requests(status)}


@router.post("/send")
def wa_send(req: SendRequest):
    """Owner/agent sends a message. Outside 24h of the contact's last message, use a template."""
    _ensure_tables()
    cfg = WhatsAppConfig()
    client = WhatsAppClient(cfg)
    try:
        if req.template:
            res = client.send_template(req.to, req.template, req.language, req.params)
            body = f"[template:{req.template}]"
        elif req.text:
            res = client.send_text(req.to, req.text)
            body = req.text
        else:
            raise HTTPException(status_code=400, detail="text or template required")
    except WhatsAppError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    out_id = (res.get("messages") or [{}])[0].get("id")
    store.save_message("out", req.to.lstrip("+"), body, "text", out_id)
    return {"sent": True, "message_id": out_id}
