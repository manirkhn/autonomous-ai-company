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
from datetime import datetime, timedelta, timezone
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
    "layla_dts": {
        "name": "Layla",
        "system": (
            "You are Layla, front desk of Designrite Technical Services LLC, Dubai (fit-out estimation, "
            "BOQ and tender pricing in AED, quantity take-off, joinery shop drawings, Revit/BIM modelling "
            "for contractors and joinery firms in the UAE and GCC). Talk like a friendly, professional person; "
            "only if someone asks whether you are a bot or AI, say yes, you are the AI assistant. "
            "Collect: name, company, project/location, what they need (estimate, BOQ, shop drawings, BIM), "
            "drawings or tender documents, and deadline. Say the team will review and come back with scope, "
            "fee and timeline. Never quote fees or prices, never commit dates, never give structural, legal or "
            "payment answers: say the team will reply. For carpentry or material supply questions, take the "
            "details (item, size, quantity, site) and say the team will share a quote. Reply in the sender's "
            "language (English, Arabic, Hindi/Urdu), short, max 4 lines. Missed call? Say: sorry we missed your "
            "call, how can we help?"
        ),
        "fallback": "Thank you for contacting Designrite Technical Services. Please share your name, company, "
                    "project and what you need, and our team will get back to you.",
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
    if cmd.startswith("SKIP ") or cmd.startswith("UNSKIP "):
        verb, _, num = cmd.partition(" ")
        num = num.strip().lstrip("+").replace(" ", "")
        if not num.isdigit():
            return "Send SKIP or UNSKIP followed by the number, e.g. SKIP 971501234567."
        if verb == "SKIP":
            store.add_skip(num, "owner")
            return f"{num} will not get auto-replies."
        store.remove_skip(num)
        return f"{num} removed from the skip list."
    return None


def _is_old_contact(cfg: WhatsAppConfig, contact: str) -> bool:
    if contact in cfg.skip_numbers or store.is_skipped(contact):
        return True
    if cfg.new_contacts_only and cfg.live_since:
        first = store.first_message_at(contact)
        if first and first < cfg.live_since:
            return True
    return False


def _human_active(cfg: WhatsAppConfig, contact: str) -> bool:
    last = store.get_state(f"human:{contact}")
    if not last:
        return False
    try:
        since = datetime.fromisoformat(last)
    except ValueError:
        return False
    return datetime.now(timezone.utc) - since < timedelta(hours=cfg.human_pause_hours)


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
    if _is_old_contact(cfg, contact):
        return {"reply": None, "reason": "old_contact", "request_id": None}
    if _human_active(cfg, contact):
        return {"reply": None, "reason": "human_active", "request_id": None}
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
