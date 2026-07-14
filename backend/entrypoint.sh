#!/usr/bin/env bash
set -euo pipefail

# The container has a single role, chosen by the first argument:
#   api    -> run DB migrations (if configured) then serve the FastAPI app
#   worker -> run the Celery worker
role="${1:-api}"

run_migrations() {
    if [[ -n "${ALEMBIC_DATABASE_URL:-}" ]]; then
        echo "[entrypoint] Running Alembic migrations..."
        alembic upgrade head
    else
        echo "[entrypoint] ALEMBIC_DATABASE_URL not set; skipping migrations."
    fi
}

case "$role" in
    api)
        run_migrations
        exec uvicorn app.main:app --host 0.0.0.0 --port 8000
        ;;
    worker)
        exec celery -A app.core.celery_app worker --loglevel=info
        ;;
    *)
        # Allow arbitrary commands: `docker run ... alembic upgrade head`
        exec "$@"
        ;;
esac
