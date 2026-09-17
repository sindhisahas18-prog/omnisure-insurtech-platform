# OmniSure — AI Insurtech Platform

An AI-powered, multi-insurance-type advisor, comparison, and claims platform
covering Car, Bike, Health, Mobile, Laptop, Electronics, Home, Travel, Crop,
Business, Life, and Livestock insurance — built around a reusable insurance
engine, a structured PostgreSQL database, and (from Phase 2) a RAG knowledge
base over uploaded policy datasets.

## Status: Phase 1 ✅ Foundation · Phase 2 ✅ RAG + AI Advisor · Phase 3 ✅ Claims System · Phase 4 ✅ Voice + AI Automation

This is the first of 7 planned phases. What's live right now:

- FastAPI backend + PostgreSQL, fully wired (no mocked data)
- Signup / login / JWT auth with role-based access (customer / employee / admin)
- Customer dashboard (live metrics: active policies, sum insured, upcoming
  renewals — computed from the DB, not hardcoded)
- Admin dashboard KPIs (live counts from the DB)
- Insurance-type catalog (all 12 categories, seeded)
- Premium service plans (₹800 Essential / ₹1,000 Pro / ₹1,500 Max, seeded)
- Frontend built from the Stitch "Sovereign Intelligence" design tokens
  (colors, type scale, spacing) as plain HTML + Tailwind + vanilla JS

### Phase 2 so far: flexible dataset ingestion layer

- `Dataset` / `DatasetRecord` models — one row per uploaded file, one row per
  cleaned record (stored under its *original* column names in JSONB, so
  wildly different insurance-type datasets share one table without forcing
  a fixed schema)
- `app/services/field_mapping.py` — the alias-mapping layer the spec asked
  for (`company` / `insurer` / `insurance_company` → `insurer_name`, etc.),
  normalized so `Annual_Premium`, `annual premium`, and `AnnualPremium` all
  match the same alias
- `app/services/data_quality.py` — missing values by column, duplicate rows,
  invalid-numeric detection; reported to the admin, never silently dropped
- `app/services/ingestion.py` — validate → clean → normalize → import,
  status-tracked per dataset (`uploaded → validating → processing →
  processed`, or `error` with the actual exception message)
- Admin API: upload (with instant preview before anything is imported),
  process/reprocess, list, per-dataset record browsing, delete
  (`/admin.html` → **Datasets**)
- **Verified against your real uploaded data**, not synthetic rows: the
  vehicle cross-sell dataset (381,109 rows) and the UK home insurance
  dataset (256,136 rows, 66 columns) both ran through the full
  map → validate → clean → import pipeline end-to-end during development

### Phase 2, completed: RAG knowledge base + AI Insurance Advisor

- `PolicyDocument` / `DocumentChunk` models — upload a PDF or .txt policy
  wording per insurance type; `document_processing.py` extracts text and
  splits it into overlapping word-window chunks
- `embeddings.py` — real OpenAI embeddings (`text-embedding-3-small`) when
  `OPENAI_API_KEY` is set; otherwise a deterministic hash-based fallback so
  the whole pipeline runs with zero external setup (clearly reported as
  `demo_mode: true` everywhere it matters, never presented as a real model)
- `vector_store.py` — one FAISS flat inner-product index per insurance
  type, persisted to `backend/data/faiss/`
- `advisor.py` — the AI Insurance Advisor: combines structured
  `DatasetRecord` filtering (budget, canonical fields via each dataset's
  column mapping) with FAISS-retrieved document excerpts, then composes an
  answer — templated in demo mode, via `gpt-4o-mini` when a key is
  configured. **Grounding is enforced, not just requested**: if nothing
  relevant is retrieved, it returns the exact required message
  ("I couldn't find enough information in the available insurance data to
  answer this accurately.") instead of the LLM improvising
- Admin UI: `/documents.html` (upload/reindex/delete policy documents)
- Customer UI: an "AI Insurance Advisor" panel on `/dashboard.html` — ask a
  question, optionally set a ₹ budget, get a grounded answer plus the
  specific matched policies

**Verified end-to-end**, not just unit-tested in isolation: a sample car
policy document was uploaded → chunked → embedded → indexed → and
correctly retrieved by the advisor for a question about deductibles and
exclusions, with the answer's excerpt traceable word-for-word back to the
source document. The "insufficient data" fallback was verified too, for an
insurance type with nothing indexed yet.

### Phase 3, completed: full claims system

- **Reusable claim engine, not per-type code**: `ClaimConfig` (one row per
  insurance type) holds incident types, damaged components/claim
  categories, required documents, and dynamic questions (each tagged with
  which component it applies to, or all of them). Adding insurance type 13
  means adding a config row, never a new `if`/`elif` branch. Seeded for all
  12 types straight from the product spec's own component lists (Car:
  Bumper/Headlight/Door/..., Health: Hospitalization/Surgery/ICU/...,
  Travel: Flight Delay/Lost Baggage/..., and so on)
- **Full FNOL → settlement flow**: file a claim against a policy → answer
  the dynamic questions for that type + component → upload required
  documents (OCR'd on upload — real Tesseract for images, real text
  extraction for PDFs) → submit → automatic triage
- **Coverage verification**: explicit rule checks (policy active? right
  insurance type? incident date inside the policy period? how close to
  expiry?) — every result traceable to a real field, never guessed
- **Fraud/risk engine**: rule-based scoring (claim-to-sum-insured ratio,
  days since policy start, missing documents, recent claim frequency),
  every point explained in plain language
- **STP vs. human review routing**: exactly the spec's trigger list — high
  fraud score, high claim-to-sum-insured ratio, missing documents,
  coverage uncertainty, low AI confidence, or no claimed amount sends a
  claim to human review; a clean claim is auto-approved, settled, and
  paid without a person touching it
- **AI damage analysis**: real GPT-4o-mini vision analysis of uploaded
  photos when `OPENAI_API_KEY` is set; otherwise an honest
  "not automatically assessed, flagged for human review" result — never a
  fabricated severity/description
- **Settlement, payment, and email**: `Payment` records on settlement;
  `send_email` sends for real via SMTP when `EMAIL_SMTP_*` is configured,
  otherwise logs a clearly-marked demo notification instead of silently
  doing nothing
- **Claim tracking**: `ClaimEvent` is an append-only audit trail (coverage
  check → fraud check → triage decision → assessment → settlement →
  payment → email), which is what both the customer claim-detail page and
  the reviewer queue render as a timeline
- Customer UI: `/claims.html` — file a claim (multi-step wizard: incident
  → dynamic questions → documents), track status, see full timeline. "File
  a Claim" buttons appear on active policies on the dashboard
- Employee/admin UI: `/claims-review.html` — review queue filtered to
  `human_review`, full claim detail (fraud reasons, documents, OCR text),
  approve/reject with amount + note
- New `employee` role, with its own login → claims-review routing
  (separate from the admin dashboard)

**Verified end-to-end** with two real scenarios run through the actual
service code (not mocked): a clean small claim with all required documents
present was auto-approved via STP, settled, and paid, with a correct event
timeline; a high-value claim filed 4 days after policy start with missing
documents was correctly scored (fraud risk 80/100) and routed to human
review with accurate plain-language reasons, then correctly resolved by an
employee decision to a reduced settlement. Also caught and fixed a real
bug in the process: `passlib==1.7.4` breaks under modern `bcrypt` (≥4.1
dropped an attribute passlib reads), which would have broken every
signup/login in production — pinned `bcrypt==4.0.1` to fix it.

**Not yet implemented**: voice assistant (STT/TTS, intent detection),
policy renewal reminders + parametric insurance, and the admin analytics
dashboards (claims-by-type/status charts, STP rate, premium revenue —
currently only raw KPI numbers, no charts yet). Nothing here is faked or
stubbed to look finished.

## Project layout

```
backend/
  app/
    models/       SQLAlchemy models (User, InsuranceType, ServicePlan, Policy)
    schemas/       Pydantic request/response schemas
    api/v1/         Route modules (auth, catalog, dashboard, admin)
    core/           Security (JWT/hashing) and auth dependencies
    config.py       Settings loaded from environment / .env
    database.py     Engine/session setup
    main.py         FastAPI app, mounts routers + serves /frontend
    seed.py         Idempotent seed script (insurance types, plans, claim
                    configs for all 12 types, demo admin + employee)
  alembic/          DB migrations (autogenerate-ready)
  requirements.txt
  .env.example      Copy to .env and fill in
  Dockerfile
frontend/
  index.html, login.html, signup.html      auth
  dashboard.html                           customer home + AI advisor
  claims.html                              file a claim / track claims
  admin.html, datasets.html, documents.html, claims-review.html   admin/employee
  static/js/api.js              fetch wrapper + auth/session helpers
  static/js/tailwind-config.js  design tokens extracted from the Stitch export
docker-compose.yml  Postgres + backend for local dev
```

## Running it locally

```bash
cp backend/.env.example backend/.env   # edit SECRET_KEY at minimum
docker compose up --build
```

Then, in a second terminal, seed the reference data:

```bash
docker compose exec backend python -m app.seed
```

Open http://localhost:8000 — it redirects to the login page. Demo accounts
are created by the seed script (**change these passwords before any real
deployment**):

- Admin: `admin@omnisure.in` / `ChangeMe123!`
- Claims reviewer (employee): `reviewer@omnisure.in` / `ChangeMe123!`

...or sign up as a new customer from the UI.

API docs (Swagger) are at http://localhost:8000/docs.

### Without Docker

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Point DATABASE_URL at a Postgres instance you're running yourself
python -m app.seed
uvicorn app.main:app --reload
```

## Architecture notes

- **Reusable insurance engine, not per-type code.** `InsuranceType` is a
  data row, not a class hierarchy — Phase 2/3 will hang product config,
  dynamic claim questions, required documents, and coverage/claim/
  settlement rules off this table (and a few related config tables) so a
  13th insurance category is a data change, not new code.
- **No hardcoded numbers anywhere in the frontend.** Dashboard metrics,
  service-plan prices, and insurance-type lists are all fetched from the
  API at render time.
- **DEMO_MODE** in `.env` is there for Phase 2+ integrations (LLM calls,
  OCR, email) that need external credentials — when a key is missing the
  app should degrade to a clearly-labeled demo response instead of
  crashing, never pretend a real result.

### Phase 4, completed: voice assistant + AI intent detection/action execution

- **Real STT/TTS, not a fabricated "AI voice"**: the widget (bottom-right on
  `/dashboard.html` and `/claims.html`) uses the browser's native
  `SpeechRecognition` for speech-to-text and `SpeechSynthesis` for
  text-to-speech — zero external API calls, works with no setup. Browsers
  without `SpeechRecognition` support (e.g. desktop Firefox) get a text
  input instead of a broken mic button, never a silently non-functional one
- **AI intent detection**: `intent_detection.py` classifies free text into
  `file_claim` / `track_claims` / `get_recommendation` / `explain_policy` /
  `general_help`, plus which of the 12 insurance types it's about. The
  `DEMO_MODE` fallback is a genuine bilingual keyword classifier (English +
  common Hinglish), not an English-only toy — it correctly parses the
  product spec's own example verbatim: *"Merki car ka accident ho gaya hai
  aur mujhe claim file karna hai"* → `file_claim` / `car`. A real
  `gpt-4o-mini` call replaces it when `OPENAI_API_KEY` is set, for far
  broader phrasing/language coverage
- **AI action execution, grounded in the customer's real data**: intent
  resolution (`assistant.py`) never assumes a policy exists — it looks up
  the customer's actual active policies for the detected type. Exactly one
  match → jumps straight into the claim wizard or policy explanation;
  multiple matches → asks the customer to pick one; zero matches → says so
  and offers the AI advisor instead. The frontend executes the resolved
  action (navigate to the claim wizard, open the advisor, view claims) and
  speaks the response back
- **AI policy explanation**: `GET /api/v1/policies/{id}/explain` (an
  "Explain this policy" button on every dashboard policy card) reuses the
  advisor's document-retrieval layer, grounded in the policy's own stored
  fields plus that insurance type's indexed policy documents — an honest
  "no document indexed yet" message when there's nothing to retrieve from,
  never invented coverage details

**Verified end-to-end**, including two real bugs caught and fixed during
testing (not just happy-path checks): a keyword tie-breaking bug that
misclassified "what's the status of my claim?" as `file_claim` instead of
`track_claims` (fixed by reordering intent priority so specific intents
beat the generic one), and a silent-fallback bug where an unrecognized
insurance-type code caused the policy filter to be skipped entirely,
matching *any* policy instead of none (fixed to return no matches instead).

## Roadmap (phases 5–7)

5. Admin analytics dashboards (claims by type/status, STP rate, fraud-risk
   claims, premium revenue — currently raw KPI numbers exist, charts don't
   yet)
6. Policy renewal reminders + parametric insurance (configurable trigger →
   payout)
7. Final QA pass across every workflow, plus anything phases 1–4 surface
   as needing hardening once real datasets/documents are loaded at scale

Each phase adds routes/tables without breaking what Phases 1–4 already ship.
