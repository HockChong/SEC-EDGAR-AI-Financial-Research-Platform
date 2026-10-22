"""Small attributed real-layout excerpts: offline regression, not corpus accuracy."""

import hashlib
import json
import tomllib
from pathlib import Path

import pytest

from sec_research.processing.benchmark import Benchmark, CorpusSplit
from sec_research.processing.html import parse_html
from tests.parsing_helpers import input_html

FIXTURES = Path(__file__).parents[1] / "fixtures/parsing"


@pytest.mark.parametrize(
    "filename", ["amazon-layout.htm", "microsoft-running.htm", "jpmorgan-ambiguous.htm"]
)
def test_source_layout_regression(filename: str) -> None:
    metadata = json.loads((FIXTURES / "excerpts.json").read_bytes())
    entry = next(e for e in metadata["fixtures"] if e["path"] == filename)
    body = (FIXTURES / filename).read_bytes()
    assert hashlib.sha256(body).hexdigest() == entry["sha256"]
    assert entry["synthetic_assembly"] is True
    result = parse_html(
        *input_html(body, fixture="annual.htm" if "amazon" in filename else "quarter.htm")
    )
    assert [[s.part, s.item] for s in result.sections if s.classification == "classified"] == entry[
        "expected_classified"
    ]
    if "jpmorgan" in filename:
        assert sum(s.classification == "ambiguous" for s in result.sections) == 2


def test_frozen_benchmark_contract_and_split_integrity() -> None:
    split = CorpusSplit.model_validate_json((FIXTURES / "corpus-split.json").read_bytes())
    labels = Benchmark.model_validate_json((FIXTURES / "boundaries.json").read_bytes())
    assert len({c.accession for c in split.filings}) == len(split.filings) == 18
    assert sum(c.split == "development" for c in split.filings) == 10
    assert sum(c.split == "held_out" for c in split.filings) == 8
    for labeled in labels.cases:
        case = next(c for c in split.filings if c.accession == labeled.accession)
        assert case.source_sha256 == labeled.source_sha256
        assert case.split == labeled.split


def test_heuristics_remain_frozen_after_held_out_annotation() -> None:
    frozen = json.loads((FIXTURES / "heuristic-freeze.json").read_bytes())
    root = Path(__file__).parents[2]
    for name, expected in frozen["files"].items():
        body = (root / name).read_bytes().replace(b"\r\n", b"\n")
        if name == "uv.lock":
            # ADR-003/WP3.5 adds only Arrow. Reconstruct the exact historical lock;
            # every prior package, artifact hash, and dependency must remain frozen.
            packages = body.split(b"[[package]]\n")
            arrow = [p for p in packages if p.startswith(b'name = "pyarrow"\n')]
            assert len(arrow) == 1
            added = tomllib.loads(arrow[0].decode())
            assert added["version"] == "24.0.0" and "dependencies" not in added
            body = b"[[package]]\n".join(p for p in packages if p not in arrow)
            for addition in (
                b'    { name = "pyarrow" },\n',
                b'    { name = "pyarrow", specifier = "==24.0.0" },\n',
            ):
                assert body.count(addition) == 1
                body = body.replace(addition, b"")
        assert hashlib.sha256(body).hexdigest() == expected
