"""
Decides how the AI employee answers an incoming WhatsApp message.

Safety first (lessons from the Kapso bot loop):
- Owner can send STOP BOT / START BOT / STATUS from an owner number.
- WA_AUTOREPLY=off logs messages but never answers.
- Optional allowlist (e.g. only Saira staff numbers).
- Loop guard: at most N replies per contact per window, and no reply to
  messages that look automated or that echo our own last reply.
"""

import re
from typing import Any, Dict, Optional

from providers.llm import LLMManager

from . import store
from .config import WhatsAppConfig

PERSONAS: Dict[str, Dict[str, str]] = {
    "saira_procurement": {
        "name": "Saira Buyer",
        "system": (
            "You are the procurement assistant of Saira Carpentry Contracting LLC, Dubai. "
            "You talk only with Saira staff on WhatsApp. Your job: take material requests "
            "(item, size/spec, quantity, site, needed-by date), confirm the details back, and say the "
            "purchase team will share supplier quotes for approval. Also accept punch-card photos for "
            "attendance and confirm receipt. Never promise prices, never place orders, never approve "
            "purchases: a Saira approver decides. Reply in the language the staff member used "
            "(English, Hindi/Urdu or Arabic), short and clear, max 4 lines. If you are an AI and asked, say so."
        ),
        "fallback": "Received. Please send item, size/spec, quantity, site and needed-by date. "
                    "The purchase team will share quotes for approval.",
    },
    "designrite_aanya": {
        "name": "Aanya",
        "system": (
            "You are Aanya, the AI assistant of Designrite Consultancy (Chartered Engineer cost consultancy). "
            "Help enquiries about BOQ/quote review, cost estimates, interior design support and CE certificates. "
            "Collect name, city, project type, stage and ask them to share their quote or drawings. "
            "Never quote fees, never give legal or structural opinions. Use natural urban Hinglish or English, "
            "max 4 lines. Always say you are an AI if asked."
        ),
        "fallback": "Thank you for your message. Please share your name, city and project details, "
                    "and our team will get back to you.",
    },
}

AUTOMATED_HINTS = re.compile(
    r"(auto[- ]?reply|automated message|ai assistant|this is an automatic|do not reply|"
    r"welcome to .* official whatsapp|thank you for contacting|chatbot)",
    re.IGNORECASE,
)
MATERIAL_HINTS = re.compile(
    r"\b(need|required|send|supply|order|qty|quantity|pcs|nos|sheets?|kg|ltr|litre|meter|mtr|sqm|"
    r"board|mdf|plywood|laminate|hinge|screw|glue|paint|veneer|edge ?band)\b",
    re.IGNORECASE,
)
PUNCH_HINTS = re.compile(r"\b(punch|attendance|time ?card|card)\b", re.IGNORECASE)


def _owner_command(cfg: WhatsAppConfig, contact: str, text: str) -> Optional[str]:
    if contact not in cfg.owner_numbers:
        return None
    cmd = text.strip().upper()
    if cmd == "STOP BOT":
        store.set_state("paused", "1")
        return "Bot paused. Messages are still saved. Send START BOT to resume."
    if cmd == "START BOT":
        store.set_state("paused", "0")
        return "Bot resumed."
    if cmd == "STATUS":
        paused = store.get_state("paused", "0") == "1"
        open_reqs = len(store.list_requests("new"))
        return f"Bot {'paused' if paused else 'running'} ({cfg.persona}). Open requests: {open_reqs}."
    return None


def classify(msg_type: str, text: str) -> Optional[str]:
    if msg_type == "image" and PUNCH_HINTS.search(text or ""):
        return "punch_card"
    if msg_type in ("image", "document"):
        return "material_request"
    if text and MATERIAL_HINTS.search(text):
        return "material_request"
    return None


def decide_reply(cfg: WhatsAppConfig, inbound: Dict[str, Any]) -> Dict[str, Any]:
    """
    inbound: {contact, name, type, text, media_id}
    Returns {"reply": str|None, "reason": str, "request_id": int|None}
    """
    contact, text, msg_type = inbound["contact"], inbound.get("text") or "", inbound.get("type", "text")

    cmd = _owner_command(cfg, contact, text)
    if cmd:
        return {"reply": cmd, "reason": "owner_command", "request_id": None}
    if not cfg.autoreply:
        return {"reply": None, "reason": "autoreply_off", "request_id": None}
    if store.get_state("paused", "0") == "1":
        return {"reply": None, "reason": "paused", "request_id": None}
    if cfg.allowed_numbers and contact not in cfg.allowed_numbers and contact not in cfg.owner_numbers:
        return {"reply": None, "reason": "not_allowed", "request_id": None}
    if text and AUTOMATED_HINTS.search(text):
        return {"reply": None, "reason": "looks_automated", "request_id": None}
    last_out = store.last_outbound_body(contact)
    if text and last_out and text.strip().lower() == last_out.strip().lower():
        return {"reply": None, "reason": "echo_loop", "request_id": None}
    if store.outbound_count_since(contact, cfg.window_minutes) >= cfg.max_replies_per_window:
        return {"reply": None, "reason": "rate_limited", "request_id": None}

    request_id = None
    kind = classify(msg_type, text)
    if cfg.persona == "saira_procurement" and kind:
        request_id = store.add_request(kind, contact, text or f"[{msg_type}]",
                                       inbound.get("name"), inbound.get("media_id"))
        if kind == "punch_card":
            return {"reply": f"Punch card received (ref #{request_id}). HR will process the hours.",
                    "reason": "punch_card", "request_id": request_id}

    persona = PERSONAS.get(cfg.persona, PERSONAS["saira_procurement"])
    history = store.recent_messages(contact, limit=10)
    transcript = "\n".join(
        f"{'Staff' if m['direction'] == 'in' else persona['name']}: {m['body'] or '[' + (m['msg_type'] or '') + ']'}"
        for m in history
    )
    prompt = (
        f"Conversation so far:\n{transcript}\n\n"
        f"Latest message from {inbound.get('name') or 'contact'}: {text or '[' + msg_type + ']'}\n"
        + (f"(Logged as request #{request_id}.)\n" if request_id else "")
        + "Write the next WhatsApp reply only."
    )
    result = LLMManager.generate(prompt, system_instruction=persona["system"])
    reply = (result.get("text") or "").strip()
    if result.get("fallback_used") or not reply:
        reply = persona["fallback"]
    if request_id and f"#{request_id}" not in reply:
        reply = f"{reply}\n(Ref #{request_id})"
    return {"reply": reply[:1500], "reason": "replied", "request_id": request_id}
