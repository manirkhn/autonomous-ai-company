"""Tests for the in-house WhatsApp integration (Meta Cloud API direct)."""

import hashlib
import hmac
import json
import os
import unittest
import uuid

from fastapi.testclient import TestClient

from server.app import app
from integrations.whatsapp import store
from integrations.whatsapp.agent import decide_reply, classify
from integrations.whatsapp.config import WhatsAppConfig
from integrations.whatsapp.router import extract_messages, process_inbound, verify_signature


def _payload(frm, text=None, mtype="text", mid=None, caption=None):
    msg = {"from": frm, "id": mid or f"wamid.{uuid.uuid4().hex}", "type": mtype}
    if mtype == "text":
        msg["text"] = {"body": text}
    else:
        msg[mtype] = {"id": "MEDIA1", "caption": caption or ""}
    return {"entry": [{"changes": [{"value": {
        "contacts": [{"wa_id": frm, "profile": {"name": "Test"}}], "messages": [msg]}}]}]}


class FakeClient:
    def __init__(self):
        self.sent = []

    def mark_read(self, mid):
        return {}

    def send_text(self, to, body, reply_to=None):
        self.sent.append((to, body))
        return {"messages": [{"id": f"wamid.out.{uuid.uuid4().hex}"}]}


def _cfg(**kw):
    c = WhatsAppConfig()
    c.access_token, c.phone_number_id = "t", "p"
    c.app_secret, c.verify_token = "secret", "vt"
    c.owner_numbers, c.allowed_numbers = ["971500000001"], []
    c.autoreply, c.persona = True, "saira_procurement"
    c.max_replies_per_window, c.window_minutes = 3, 10
    for k, v in kw.items():
        setattr(c, k, v)
    return c


class TestWhatsApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        store.init_whatsapp_tables()

    def setUp(self):
        store.set_state("paused", "0")
        self.contact = "9715" + uuid.uuid4().hex[:8]

    def test_signature(self):
        body = b'{"a":1}'
        sig = "sha256=" + hmac.new(b"secret", body, hashlib.sha256).hexdigest()
        self.assertTrue(verify_signature("secret", body, sig))
        self.assertFalse(verify_signature("secret", body, "sha256=bad"))
        self.assertFalse(verify_signature("", body, sig))

    def test_extract(self):
        msgs = extract_messages(_payload(self.contact, "need 10 sheets mdf 18mm"))
        self.assertEqual(msgs[0]["contact"], self.contact)
        self.assertEqual(msgs[0]["text"], "need 10 sheets mdf 18mm")

    def test_classify(self):
        self.assertEqual(classify("text", "need 20 pcs hinges"), "material_request")
        self.assertEqual(classify("image", "punch card week 45"), "punch_card")
        self.assertIsNone(classify("text", "hello"))

    def test_material_request_logged_and_replied(self):
        fc = FakeClient()
        msg = extract_messages(_payload(self.contact, "need 10 sheets plywood 18mm for site JVC"))[0]
        d = process_inbound(msg, _cfg(), fc)
        self.assertEqual(d["reason"], "replied")
        self.assertTrue(d["request_id"])
        self.assertEqual(len(fc.sent), 1)
        self.assertIn(f"#{d['request_id']}", fc.sent[0][1])

    def test_duplicate_ignored(self):
        fc = FakeClient()
        msg = extract_messages(_payload(self.contact, "hello", mid="wamid.fixed." + self.contact))[0]
        process_inbound(msg, _cfg(), fc)
        d2 = process_inbound(msg, _cfg(), fc)
        self.assertEqual(d2["reason"], "duplicate")

    def test_loop_guards(self):
        cfg = _cfg()
        self.assertEqual(decide_reply(cfg, {"contact": self.contact, "text": "Welcome to RBI's Official WhatsApp Channel"})["reason"], "looks_automated")
        fc = FakeClient()
        reasons = []
        for i in range(5):
            m = extract_messages(_payload(self.contact, f"question {i}"))[0]
            reasons.append(process_inbound(m, cfg, fc)["reason"])
        self.assertIn("rate_limited", reasons)
        self.assertLessEqual(len(fc.sent), 3)

    def test_allowlist_and_owner_pause(self):
        cfg = _cfg(allowed_numbers=["971500000099"])
        self.assertEqual(decide_reply(cfg, {"contact": self.contact, "text": "hi"})["reason"], "not_allowed")
        r = decide_reply(cfg, {"contact": "971500000001", "text": "STOP BOT"})
        self.assertEqual(r["reason"], "owner_command")
        self.assertEqual(decide_reply(_cfg(), {"contact": self.contact, "text": "hi"})["reason"], "paused")
        decide_reply(cfg, {"contact": "971500000001", "text": "START BOT"})
        self.assertNotEqual(decide_reply(_cfg(autoreply=False), {"contact": self.contact, "text": "hi"})["reason"], "paused")

    def test_old_contacts_skipped(self):
        cfg = _cfg(persona="layla_dts")
        old = "9715" + uuid.uuid4().hex[:8].translate(str.maketrans("abcdef", "123456"))
        r = decide_reply(cfg, {"contact": "971500000001", "text": f"SKIP {old}"})
        self.assertIn("will not get auto-replies", r["reply"])
        self.assertEqual(decide_reply(cfg, {"contact": old, "text": "hi"})["reason"], "old_contact")
        decide_reply(cfg, {"contact": "971500000001", "text": f"UNSKIP {old}"})
        self.assertNotEqual(decide_reply(cfg, {"contact": old, "text": "hi"})["reason"], "old_contact")
        self.assertEqual(decide_reply(_cfg(skip_numbers=[old]), {"contact": old, "text": "hi"})["reason"], "old_contact")

    def test_new_contacts_only_by_date(self):
        c = "9716" + uuid.uuid4().hex[:8].translate(str.maketrans("abcdef", "123456"))
        store.save_message("in", c, "old chat", "text", f"wamid.{uuid.uuid4().hex}")
        cfg = _cfg(new_contacts_only=True, live_since="2999-01-01T00:00:00+00:00")
        self.assertEqual(decide_reply(cfg, {"contact": c, "text": "hi"})["reason"], "old_contact")

    def test_history_and_human_echo(self):
        c = "9717" + uuid.uuid4().hex[:8].translate(str.maketrans("abcdef", "123456"))
        payload = {"entry": [{"changes": [{"value": {"history": [{"threads": [{"id": c}]}]}}]}]}
        fc = FakeClient()
        for m in extract_messages(payload):
            process_inbound(m, _cfg(), fc)
        self.assertTrue(store.is_skipped(c))
        h = "9718" + uuid.uuid4().hex[:8].translate(str.maketrans("abcdef", "123456"))
        echo = {"entry": [{"changes": [{"value": {"message_echoes": [
            {"from": "971555472571", "to": h, "id": f"wamid.{uuid.uuid4().hex}", "type": "text",
             "text": {"body": "I will call you"}}]}}]}]}
        for m in extract_messages(echo):
            self.assertEqual(process_inbound(m, _cfg(), fc)["reason"], "human_reply_logged")
        self.assertEqual(decide_reply(_cfg(), {"contact": h, "text": "ok"})["reason"], "human_active")
        self.assertEqual(fc.sent, [])

    def test_webhook_endpoints(self):
        os.environ.update({"WA_VERIFY_TOKEN": "vt", "WA_APP_SECRET": "secret", "WA_AUTOREPLY": "off"})
        client = TestClient(app)
        r = client.get("/whatsapp/webhook", params={"hub.mode": "subscribe", "hub.verify_token": "vt", "hub.challenge": "42"})
        self.assertEqual(r.text, "42")
        self.assertEqual(client.get("/whatsapp/webhook", params={"hub.mode": "subscribe", "hub.verify_token": "x"}).status_code, 403)
        body = json.dumps(_payload(self.contact, "hi")).encode()
        self.assertEqual(client.post("/whatsapp/webhook", content=body, headers={"X-Hub-Signature-256": "sha256=bad"}).status_code, 401)
        sig = "sha256=" + hmac.new(b"secret", body, hashlib.sha256).hexdigest()
        r = client.post("/whatsapp/webhook", content=body, headers={"X-Hub-Signature-256": sig, "Content-Type": "application/json"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("configured", client.get("/whatsapp/status").json())


if __name__ == "__main__":
    unittest.main()
