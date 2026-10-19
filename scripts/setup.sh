#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
bash scripts/uv.sh sync --frozen
bash scripts/docker.sh compose config --quiet
bash scripts/docker.sh compose up -d --wait db
export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://sec_research:sec_research_dev@127.0.0.1:${DATABASE_PORT:-5432}/sec_research}"
# This is an explicit setup/migration action, never an API startup side effect.
bash scripts/uv.sh run --frozen alembic upgrade head
echo 'Foundation dependencies, PostgreSQL and schema are ready.'
