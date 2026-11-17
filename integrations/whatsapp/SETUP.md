# Own WhatsApp line — setup

Direct connection to Meta's official WhatsApp Business Cloud API. No Kapso, no monthly middleman fee.
Meta only charges per conversation for business-started (template) messages; replies inside 24 hours of a
customer message are free.

## 1. Meta side (one time, owner does the account steps)
1. developers.facebook.com → My Apps → Create app → type **Business** → add the **WhatsApp** product.
2. WhatsApp → API Setup: add the Saira business phone number (a number NOT already on the WhatsApp app)
   and verify it by SMS/call.
3. Business Settings → System users → create a system user → add the app → generate a **permanent token**
   with `whatsapp_business_messaging` and `whatsapp_business_management`.
4. Copy: **Phone number ID**, **permanent token**, **App secret** (App settings → Basic).

## 2. Server side (Render)
Set these environment variables:

| Variable | Value |
|---|---|
| WA_ACCESS_TOKEN | permanent system-user token |
| WA_PHONE_NUMBER_ID | from API Setup |
| WA_APP_SECRET | App settings → Basic |
| WA_VERIFY_TOKEN | any long random text you choose |
| WA_OWNER_NUMBERS | owner numbers, e.g. 971555472571 |
| WA_ALLOWED_NUMBERS | Saira staff numbers (comma-separated); empty = anyone |
| WA_PERSONA | saira_procurement, designrite_aanya or layla_dts |
| WA_NEW_CONTACTS_ONLY | on = never auto-reply contacts who chatted before go-live |
| WA_LIVE_SINCE | go-live time, e.g. 2026-11-17T00:00:00+00:00 |
| WA_SKIP_NUMBERS | extra numbers that must never get auto-replies |
| WA_HUMAN_PAUSE_HOURS | hours the bot stays quiet after a person replies from the app (default 12) |
| WA_AUTOREPLY | on / off |

## 3. Connect the webhook
WhatsApp → Configuration → Webhook:
- Callback URL: `https://<your-render-app>.onrender.com/whatsapp/webhook`
- Verify token: same as WA_VERIFY_TOKEN
- Subscribe to the **messages** field.

## 4. Use
- Staff send material requests or punch-card photos → logged in `/whatsapp/requests`, AI replies with a ref number.
- Owner sends **STOP BOT**, **START BOT** or **STATUS** from an owner number.
- Check health: `GET /whatsapp/status`.

## Safety built in
Signed webhooks only (X-Hub-Signature-256), duplicate-message protection, staff allowlist, max 5 replies
per contact per 10 minutes, no replies to automated/bot messages or echoes of our own reply.

## Layla (Designrite Technical Services, +971 55 547 2571) with the WhatsApp Business app kept (coexistence)
- Onboard the number through Meta's Embedded Signup with the WhatsApp Business app option, so the app keeps
  working on the phone and the Cloud API gets the same messages. Subscribe the webhook to **messages**,
  **smb_message_echoes** and **history**.
- Existing chats synced from the app are added to the skip list automatically; the bot never answers them.
- If a person replies from the app, the bot stays quiet for that contact (WA_HUMAN_PAUSE_HOURS).
- Owner commands from an owner number: STOP BOT, START BOT, STATUS, SKIP <number>, UNSKIP <number>.
- Set WA_PERSONA=layla_dts, WA_NEW_CONTACTS_ONLY=on, WA_LIVE_SINCE=<go-live time>.
