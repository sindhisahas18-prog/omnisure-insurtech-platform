# OmniSure — AI Insurtech Platform

An AI-powered, multi-insurance-type advisor, comparison, and claims platform
covering Car, Bike, Health, Mobile, Laptop, Electronics, Home, Travel, Crop,
Business, Life, and Livestock insurance — built around a reusable insurance
engine, a structured PostgreSQL database, and (from Phase 2) a RAG knowledge
base over uploaded policy datasets.

## Status: Phase 1 — Foundation ✅

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

**Not yet implemented** (later phases, see below) — nothing here is faked or
stubbed to look finished: the claims system, RAG/AI advisor, OCR, fraud/risk
engine, voice assistant, and analytics charts simply don't have routes yet.
The dashboard's "Open Claims" metric returns real `0` because there's no
claims table yet, not a placeholder number.

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

## Roadmap (phases 2–7)

2. Dataset ingestion, cleaning, validation + structured DB import; policy
   PDF processing; FAISS-based RAG; AI insurance advisor, recommendation,
   and comparison
3. Full claims system: FNOL, dynamic per-insurance-type questions, document
   upload + OCR, AI damage analysis, coverage verification, triage
4. Voice assistant (STT/TTS), AI intent detection and action execution
5. Fraud/risk engine, STP vs. human-review routing, assessment, settlement
6. Admin analytics dashboards (claims by type/status, STP rate, fraud-risk
   claims, premium revenue — all DB-driven)
7. Policy renewal reminders + parametric insurance (configurable trigger →
   payout)

Each phase adds routes/tables without breaking what Phase 1 already ships.
