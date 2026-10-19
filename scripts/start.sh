#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://sec_research:sec_research_dev@127.0.0.1:${DATABASE_PORT:-5432}/sec_research}"
exec bash scripts/uv.sh run --frozen uvicorn sec_research.api.app:app_factory \
    --factory --host 127.0.0.1 --port "${API_PORT:-8000}" --no-access-log
