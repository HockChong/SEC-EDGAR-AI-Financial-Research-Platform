#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
scratch_dir="$(mktemp -d)"
trap 'rm -rf -- "$scratch_dir"' EXIT
bash scripts/uv.sh build
bash scripts/uv.sh export --frozen --no-dev --no-emit-project --output-file "$scratch_dir/requirements.txt" >/dev/null
bash scripts/uv.sh venv "$scratch_dir/venv" --python 3.12.14
if [[ -f "$scratch_dir/venv/Scripts/python.exe" ]]; then
    wheel_python="$scratch_dir/venv/Scripts/python.exe"
else
    wheel_python="$scratch_dir/venv/bin/python"
fi
bash scripts/uv.sh pip install --python "$wheel_python" --require-hashes -r "$scratch_dir/requirements.txt"
bash scripts/uv.sh pip install --python "$wheel_python" --no-deps dist/sec_research-0.1.0-py3-none-any.whl
cp uv.lock "$scratch_dir/uv.lock"
cd "$scratch_dir"
"$wheel_python" - <<'PY'
import sys
import subprocess
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path
from pydantic import SecretStr
import sec_research
from sec_research.api.app import create_app
from sec_research.contracts.canonical import CANONICAL_MODELS, ReportingPeriod
from sec_research.contracts.schemas import schema_bundle
from sec_research.settings import Settings
from sec_research.ingestion.ports import Fetch
from sec_research.processing.html import parse_html
from sec_research.processing.tables import extract_tables
from sec_research.contracts.tables import TableExtraction
from sec_research.contracts.sec import Source
from datetime import datetime, UTC
from uuid import UUID
import hashlib

assert version("sec-research") == "0.1.0"
assert Path(sec_research.__file__).is_relative_to(Path(sys.prefix))
assert files("sec_research").joinpath("py.typed").is_file()
assert len(CANONICAL_MODELS) == 13
assert schema_bundle()["schema_version"] == "canonical-1"
period = ReportingPeriod.model_validate({"kind": "instant", "end": "2024-12-28"})
assert ReportingPeriod.model_validate_json(period.model_dump_json()) == period
settings = Settings(database_url=SecretStr("postgresql+psycopg://test:test@localhost/test"))
assert set(create_app(settings).openapi()["paths"]) == {"/health/live", "/health/ready"}
help_result = subprocess.run(
    [sys.executable, "-m", "sec_research.ingestion.cli", "--help"],
    check=True, capture_output=True, text=True,
)
assert "reconcile" in help_result.stdout and "ingest" in help_result.stdout
source = Source.model_validate({
    "kind": "filing", "cik": "0000000001",
    "url": "https://www.sec.gov/Archives/edgar/data/1/000000000125000001/demo.htm",
    "filing": {"cik": "0000000001", "accession": "0000000001-25-000001",
               "form": "10-K", "filing_date": "2025-02-01", "primary_document": "demo.htm"},
})
body = b"<html><body><h1>Item 1. Business</h1><p>Wheel parser smoke.</p></body></html>"
fetch = Fetch(
    id=UUID(int=1), run_id=UUID(int=2), source=source, sha256=hashlib.sha256(body).hexdigest(),
    storage_uri="file:///synthetic/source", manifest_uri="file:///synthetic/manifest",
    fetched_at=datetime(2026, 10, 20, tzinfo=UTC), byte_count=len(body),
    http_status=200, media_type="text/html", attempts=1,
)
parsed = parse_html(fetch, body)
assert parsed.sections[0].item == "1"
assert parsed.logical_bytes() == parse_html(fetch, body).logical_bytes()
assert "lxml-" in parsed.document.parser_version
table_body = b"<table><tr><th>2025</th></tr><tr><td>42</td></tr></table>"
table_fetch = fetch.model_copy(update={
    "sha256": hashlib.sha256(table_body).hexdigest(), "byte_count": len(table_body),
})
tables = extract_tables(table_fetch, table_body)
assert TableExtraction.model_validate_json(tables.model_dump_json()) == tables
assert len(tables.tables[0].cells) == 2
assert tables.normalization_complete
assert tables.tables[0].contexts[1].normalization.status == "parsed"
assert tables.tables[0].cells[1].value == 42
subprocess.run([sys.executable, "-m", "sec_research.processing.corpus", "--help"],
               check=True, capture_output=True, text=True)
from sec_research.processing.xbrl import normalize_company_facts
from sec_research.domain.financial_selection import select_facts
from sec_research.contracts.xbrl import SelectionRequest
import json

xbrl_body = json.dumps({"cik": 1, "entityName": "Wheel Synthetic", "facts": {"us-gaap": {
    "Assets": {"units": {"USD": [{"end": "2024-12-31", "val": 42,
        "accn": "0000000001-25-000001", "filed": "2025-02-01", "form": "10-K"}]}}
}}}).encode()
xbrl_fetch = fetch.model_copy(update={
    "source": Source(kind="company_facts", cik="0000000001",
        url="https://data.sec.gov/api/xbrl/companyfacts/CIK0000000001.json"),
    "sha256": hashlib.sha256(xbrl_body).hexdigest(), "byte_count": len(xbrl_body),
    "media_type": "application/json",
})
normalized = normalize_company_facts(xbrl_fetch, xbrl_body)
fact = normalized.observations[0].fact
assert fact is not None and fact.value == 42
selection = select_facts([fact], SelectionRequest.model_validate({
    "cik": "0000000001", "metric": "total_assets", "period": fact.period,
    "as_of": "2025-02-01",
}))
assert selection.status == "selected"
subprocess.run([sys.executable, "-m", "sec_research.processing.xbrl_corpus", "--help"],
               check=True, capture_output=True, text=True)
from sec_research.adapters.storage.local import LocalBronze
from sec_research.adapters.storage.parquet import LocalDatasets
from sec_research.processing.datasets import build_snapshot, make_spec, load_snapshot

bronze = LocalBronze(Path("bronze-root"))
derived = LocalDatasets(Path("derived"))
checksum, uri = bronze.put(xbrl_body)
xbrl_fetch = xbrl_fetch.model_copy(update={"storage_uri": uri})
bronze.put_manifest(xbrl_fetch.id.hex,
                    xbrl_fetch.model_dump_json(exclude={"manifest_uri"}).encode())
spec = make_spec("wheel-validation", Path("uv.lock"), datetime(2026, 10, 22, tzinfo=UTC),
                 [selection.request])
snapshot = build_snapshot(bronze, derived, [xbrl_fetch], spec)
assert snapshot.id is not None and load_snapshot(derived, snapshot.id) == snapshot
assert build_snapshot(bronze, derived, [xbrl_fetch], spec) == snapshot
subprocess.run([sys.executable, "-m", "sec_research.processing.dataset_cli", "--help"],
               check=True, capture_output=True, text=True)
print("Installed wheel validated outside checkout, including deterministic Silver/Gold Parquet replay.")
PY
