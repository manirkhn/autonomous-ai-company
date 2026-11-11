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
| WA_PERSONA | saira_procurement or designrite_aanya |
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
