#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
bash scripts/uv.sh lock --check
bash scripts/uv.sh run --frozen ruff check src tests migrations
bash scripts/uv.sh run --frozen ruff format --check src tests migrations
bash scripts/uv.sh run --frozen mypy
if [[ -n "${TEST_DATABASE_URL:-}" ]]; then
    bash scripts/uv.sh run --frozen pytest --cov=sec_research --cov-report=term-missing
else
    bash scripts/uv.sh run --frozen pytest -m 'not integration'
    echo 'Integration checks not selected: set TEST_DATABASE_URL to run the full suite.'
fi
