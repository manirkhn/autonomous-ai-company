"""
Own WhatsApp integration (no Kapso / no third-party inbox).
Talks directly to Meta's official WhatsApp Business Cloud API.

Modules:
- config.py  : settings read from environment variables (no secrets in code)
- client.py  : send text / template / mark-read through the Graph API
- store.py   : SQLite tables for messages, contacts, requests and bot state
- agent.py   : persona replies (Gemini) + loop / spam guards
- router.py  : FastAPI webhook (GET verify, POST receive) + owner endpoints
"""
