"""Small attributed real-layout excerpts: offline regression, not corpus accuracy."""

import hashlib
import json
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
        assert hashlib.sha256(body).hexdigest() == expected
