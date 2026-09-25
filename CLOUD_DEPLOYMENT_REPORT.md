# CLOUD DEPLOYMENT & 24/7 RUNTIME REPORT

**Project:** Autonomous AI Company  
**Phase:** 5B — Gemini-Powered 24/7 Cloud Company + Daily Email CEO Report  
**Owner:** Manir Khan (`manirkhn@gmail.com`)  
**Deployment Date:** 25 September 2026  
**Status:** 🟢 Ready & Verified (Independent Cloud Architecture)  

---

## 1. Provider & Architecture

The company architecture is designed for autonomous continuous operation, decoupling the business execution runtime from the owner's personal laptop.

```
+-------------------------------------------------------------+
|                      OWNER DEVICE                           |
|       (Mobile / Laptop: Monitoring & Approvals Only)         |
+-------------------------------------------------------------+
                              | (HTTPS)
                              v
+-------------------------------------------------------------+
|                 SECURE CLOUD RUNTIME GATEWAY                |
|               (FastAPI / REST / Web / SSE)                  |
+-------------------------------------------------------------+
         |                      |                     |
         v                      v                     v
+------------------+  +-------------------+  +------------------+
| 24/7 SCHEDULER   |  | 24/7 TASK WORKER  |  | 9-POINT HEARTBEAT|
| (23:00 Dubai)    |  | (Auto-Execution)  |  | (Probes 60s)     |
+------------------+  +-------------------+  +------------------+
         |                      |                     |
         +----------------------+---------------------+
                                |
                                v
+-------------------------------------------------------------+
|               AUTONOMOUS AI WORKFORCE (12+ ROLES)           |
| (CEO, Research, Product, Sales, QA, Finance, Support, Ops)  |
+-------------------------------------------------------------+
         |                                           |
         v                                           v
+--------------------------------+   +------------------------+
| GOOGLE GEMINI / FALLBACK       |   | PERSISTENT DB & LEDGER |
| (Reasoning & Summarization)    |   | (SQLite on Persistent  |
| - gemini-2.5-flash             |   |  Volume Mount)         |
| - Deterministic Synthesizer    |   | - data/company.db      |
+--------------------------------+   +------------------------+
                                                 |
                                                 v
                                     +------------------------+
                                     | DAILY CEO REPORT ENGINE|
                                     | - Section 34 Truth Chk |
                                     | - Markdown & JSON      |
                                     | - Email to manirkhn    |
                                     +------------------------+
```

---

## 2. Infrastructure Cost & Free-Tier Ladder

In strict compliance with the **Free-First Acquisition Ladder** and the **Financial Firewall ($0.00 unapproved spending ceiling)**:

| Component | Target Provider | Tier | Approved Cost | Free Tier Constraints |
| :--- | :--- | :--- | :--- | :--- |
| **Container Engine** | Docker / Render / Fly.io | Free Tier | **$0.00** | 1 CPU, 512MB RAM, 1GB persistent disk |
| **Database** | SQLite3 on persistent volume | Self-Hosted | **$0.00** | Zero cloud database subscription costs |
| **AI LLM** | Google Gemini (`gemini-2.5-flash`) | Free Tier API | **$0.00** | Free tier rate limits with auto-fallback |
| **Email Service** | SMTP / Local Secure Outbox | Free / Self-Hosted | **$0.00** | Standard SMTP provider (Gmail App Pass / Brevo) |
| **Domain / SSL** | Automatic via Cloud Provider | Free Tier | **$0.00** | Managed Let's Encrypt certificates |
| **TOTAL** | — | — | **$0.00** | **100% Bootstrap / Zero Capital at Risk** |

*Policy: If any service ever approaches a paid threshold, the system halts expansion and requests owner approval through the Approval Center.*

---

## 3. Gemini Integration & Account Assessment

- **Subscription Status:** The owner possesses a Google Gemini Pro subscription.
- **API Access Policy:** Consumer web Gemini Pro subscriptions operate under separate quotas from developer API access. To guarantee 100% cost safety, the application accesses Gemini strictly under the **free-tier API quota** using `google-genai` SDK and `gemini-2.5-flash`.
- **Financial Invariant:** The system will **never** automatically activate paid API billing.
- **Fail-Safe Mechanism:** If Gemini API limits are reached, the system engages the built-in `DeterministicFallbackProvider`, allowing all company routines to proceed uninterrupted.
- **Credential Protection:** Secrets are stored strictly in `GEMINI_API_KEY` and are never committed to code or printed in reports.

---

## 4. 24/7 Cloud Background Services

1. **Cloud Web Gateway (`server/app.py`):**
   - Serves the AI Virtual Office and REST endpoints on port `8000`.
   - Accessible from phone, tablet, or laptop browser.
2. **Cloud Scheduler (`cloud/scheduler.py`):**
   - Maintains continuous background timer thread.
   - Calculates target execution at `23:00 Asia/Dubai` (19:00 UTC).
   - Generates daily reports and dispatches emails automatically.
3. **Cloud Worker (`cloud/worker.py`):**
   - Autonomous execution loop processing tasks, advancing projects, and recording genuine activities.
4. **Company Heartbeat Engine (`core/heartbeat.py`):**
   - Continuous diagnostic probe verifying:
     1. Cloud Server (FastAPI gateway)
     2. Background Worker
     3. 24/7 Scheduler
     4. Database persistence
     5. Task queue
     6. Gemini AI Provider
     7. Email service
     8. Revenue system & firewall
     9. AI Virtual Office

---

## 5. Daily CEO Report Delivery to manirkhn@gmail.com

- **Recipient:** `manirkhn@gmail.com`
- **Schedule:** 23:00 Asia/Dubai
- **Subject:** `🏢 AI Company — Daily CEO Progress Report — {DATE}`
- **Section 34 Truth Check:** Before sending, an automated validation verifies that reported revenue matches `revenue_ledger`, expenses match actual expenses, profit equals revenue minus expenses, and customers match verified customer records.
- **Delivery Confirmation:** Tracked in the `email_deliveries` database table and archived in `reports/daily/` and `data/outbox/`.

---

## 6. Security, Banking Air-Gap & Authentication

- **Personal Banking Air-Gap:** AI employees have zero access to the owner's bank account, bank credentials, withdrawal tools, or credit cards.
- **Unapproved Spending Limit:** Enforced at **$0.00** by `FinancialFirewall`.
- **Emergency Stop:** Retained and active in both the backend and AI Virtual Office UI.

---

## 7. Automated Test Suite Results

The comprehensive test suite was executed against all components (Phases 1–5B):

```
Ran 68 tests in 6.665s
OK
```

- **Phase 1 Foundations:** 10/10 Passed
- **Phase 2 Discovery & Validation:** 16/16 Passed
- **Phase 3 Self-Growth & Capability Gaps:** 14/14 Passed
- **Phase 4 Revenue Engine & Firewall:** 10/10 Passed
- **Phase 5A AI Virtual Office:** 10/10 Passed
- **Phase 5B 24/7 Cloud, Gemini & Daily Report:** 8/8 Passed
- **Total Regressions:** **ZERO (0)**

---

## 8. Deployment Configurations Provided

The codebase includes production-grade container manifests:
1. `Dockerfile`: Self-contained Python 3.12 slim container with healthcheck.
2. `docker-compose.yml`: Local or VPS multi-container orchestration with persistent volume mounts.
3. `render.yaml`: Blueprint for one-click deployment on Render with persistent disk.
4. `fly.toml`: Configuration for Fly.io persistent cloud edge deployment.
5. `scripts/run_cloud.py`: Direct headless execution runner.

---

## 9. Owner Action Required

1. **(Optional) Configure External SMTP Credentials:**
   To send outbound emails directly via your preferred email server (e.g. Gmail App Password), set the following environment variables in your cloud hosting provider or `.env`:
   - `SMTP_HOST=smtp.gmail.com`
   - `SMTP_PORT=587`
   - `SMTP_USER=manirkhn@gmail.com`
   - `SMTP_PASSWORD=<your-app-password>`
   *(Note: Until configured, all reports are safely generated, validated, and stored in the secure local outbox at `data/outbox/` and `reports/daily/` with zero data loss).*
2. **Review Dashboard:** Open the dashboard at `http://localhost:8000` (or your cloud URL) from your phone or laptop.
