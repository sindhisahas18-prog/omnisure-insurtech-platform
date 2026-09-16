# OmniSure — AI Insurtech Platform

An AI-powered, multi-insurance-type advisor, comparison, and claims platform
covering Car, Bike, Health, Mobile, Laptop, Electronics, Home, Travel, Crop,
Business, Life, and Livestock insurance — built around a reusable insurance
engine, a structured PostgreSQL database, and (from Phase 2) a RAG knowledge
base over uploaded policy datasets.

## Status: Phase 1 ✅ Foundation · Phase 2 ✅ RAG + AI Advisor

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

**Not yet implemented**: the claims system (FNOL, dynamic questions,
document upload + OCR, damage analysis, coverage verification, triage),
fraud/risk engine, STP vs. human review, voice assistant, renewal +
parametric insurance, and analytics dashboards. Nothing here is faked or
stubbed to look finished — the customer dashboard's "Open Claims" metric
returns real `0` because there's no claims table yet, not a placeholder
number.

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
    seed.py         Idempotent seed script (insurance types, plans, demo admin)
  alembic/          DB migrations (autogenerate-ready)
  requirements.txt
  .env.example      Copy to .env and fill in
  Dockerfile
frontend/
  index.html, login.html, signup.html, dashboard.html, admin.html
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

Open http://localhost:8000 — it redirects to the login page. A demo admin
account is created by the seed script (`admin@omnisure.in` /
`ChangeMe123!` — **change this password before any real deployment**), or
sign up as a new customer from the UI.

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

## Roadmap (phases 3–7)

3. Full claims system: FNOL, dynamic per-insurance-type questions, document
   upload + OCR, AI damage analysis, coverage verification, triage
4. Voice assistant (STT/TTS), AI intent detection and action execution
5. Fraud/risk engine, STP vs. human-review routing, assessment, settlement
6. Admin analytics dashboards (claims by type/status, STP rate, fraud-risk
   claims, premium revenue — all DB-driven)
7. Policy renewal reminders + parametric insurance (configurable trigger →
   payout)

Each phase adds routes/tables without breaking what Phases 1–2 already ship.
