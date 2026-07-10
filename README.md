# SmartBid AI

B2B web app that automates technical evaluation of vendor proposals against RFP documents: upload an RFP and vendor datasheets, extract structured requirements/specifications, compare them, and generate a compliance matrix exportable to Excel/PDF.

## Stack

- **Backend**: FastAPI (Python 3.12), SQLAlchemy (async) + Alembic, Claude API for document extraction, Voyage AI for embeddings, pgvector for semantic matching.
- **Frontend**: Next.js (App Router, TypeScript), Supabase Auth.
- **Infra**: Supabase (Postgres, Storage, Auth).

## Repo layout

```
frontend/   Next.js app
backend/    FastAPI service
supabase/   SQL migrations mirrored for the Supabase CLI (optional; Alembic is source of truth)
```

## Local development

1. Copy `.env.example` to `.env` (backend) and set the `NEXT_PUBLIC_*` vars in `frontend/.env.local`. Fill in your Supabase project's URL/keys and your Anthropic/Voyage API keys.
2. `docker-compose up` to run backend + frontend together, or run each independently:
   - Backend: `cd backend && uv sync && uv run alembic upgrade head && uv run uvicorn app.main:app --reload`
   - Frontend: `cd frontend && npm install && npm run dev`

See `AGENTS.md`-equivalent context in the plan doc for architecture details (data model, extraction pipeline, matching engine, phasing).
