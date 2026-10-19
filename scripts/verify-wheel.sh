#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
scratch_dir="$(mktemp -d)"
trap 'rm -rf -- "$scratch_dir"' EXIT
bash scripts/uv.sh build
bash scripts/uv.sh export --frozen --no-dev --no-emit-project --output-file "$scratch_dir/requirements.txt" >/dev/null
bash scripts/uv.sh venv "$scratch_dir/venv" --python 3.12.14
bash scripts/uv.sh pip install --python "$scratch_dir/venv/bin/python" --require-hashes -r "$scratch_dir/requirements.txt"
bash scripts/uv.sh pip install --python "$scratch_dir/venv/bin/python" --no-deps dist/sec_research-0.1.0-py3-none-any.whl
cd "$scratch_dir"
"$scratch_dir/venv/bin/python" - <<'PY'
import sys
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path
from pydantic import SecretStr
import sec_research
from sec_research.api.app import create_app
from sec_research.settings import Settings

assert version("sec-research") == "0.1.0"
assert Path(sec_research.__file__).is_relative_to(Path(sys.prefix))
assert files("sec_research").joinpath("py.typed").is_file()
settings = Settings(database_url=SecretStr("postgresql+psycopg://test:test@localhost/test"))
assert set(create_app(settings).openapi()["paths"]) == {"/health/live", "/health/ready"}
print("Installed wheel validated outside the source checkout; typed contracts and API import succeed.")
PY
