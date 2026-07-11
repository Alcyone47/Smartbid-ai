# SmartBid AI

B2B web app that automates technical evaluation of vendor proposals against RFP documents: upload an RFP and vendor datasheets, extract structured requirements/specifications, compare them, and generate a compliance matrix exportable to Excel/PDF.

## Stack

- **Backend**: FastAPI (Python 3.12), SQLAlchemy (async) + Alembic, Claude API for document extraction, Voyage AI for embeddings, pgvector for semantic matching.
- **Frontend**: React + TypeScript + Vite, Tailwind CSS, Shadcn UI, TanStack Router/Query/Table, React Hook Form, Zod, Supabase Auth.
- **Infra**: Supabase (Postgres, Storage, Auth), Redis (Celery broker).

## Repo layout

```
frontend/   React + Vite app
backend/    FastAPI service
supabase/   SQL migrations mirrored for the Supabase CLI (optional; Alembic is source of truth)
```

## Local development

1. Copy `.env.example` to `.env` (backend) and copy `frontend/.env.example` to `frontend/.env`. Fill in your Supabase project's URL/keys and your Anthropic/Voyage API keys.
2. `docker-compose up redis` for the Celery broker, plus run each service independently:
   - Backend: `cd backend && uv sync && uv run alembic upgrade head && uv run uvicorn app.main:app --reload`
   - Celery worker: `cd backend && uv run celery -A app.core.celery_app worker --loglevel=info`
   - Frontend: `cd frontend && npm install && npm run dev`

See `AGENTS.md`-equivalent context in the plan doc for architecture details (data model, extraction pipeline, matching engine, phasing).
