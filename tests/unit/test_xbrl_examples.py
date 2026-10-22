"""Source-linked regression checks, not independently reviewed financial accuracy."""

import json
from decimal import Decimal
from pathlib import Path

import pytest

from sec_research.contracts.xbrl import SelectionRequest
from sec_research.domain.financial_selection import select_facts
from sec_research.processing.xbrl import normalize_company_facts
from tests.xbrl_helpers import input_facts

EXAMPLES = json.loads(Path("tests/fixtures/xbrl/reported-examples.json").read_bytes())["cases"]


@pytest.mark.parametrize("case", EXAMPLES, ids=[c["case_id"] for c in EXAMPLES])
def test_reported_real_company_example(case: dict[str, str]) -> None:
    # Excerpt checksum is deliberately distinct from the original Bronze artifact checksum.
    body = (
        json.dumps({"cik": int(case["cik"]), "entityName": case["company"]})[:-1]
        + ',"facts":{"us-gaap":{'
        + json.dumps(case["concept"])
        + ':{"units":{"USD":['
        + case["raw_json"]
        + "]}}}}}"
    ).encode()
    result = normalize_company_facts(input_facts(body), body)
    fact = result.observations[0].fact
    assert fact is not None and fact.value == Decimal(case["expected_value"])
    request = SelectionRequest(
        cik=case["cik"], metric=case["metric"], period=fact.period, as_of=fact.filed
    )
    selection = select_facts([fact], request)
    assert selection.status == "selected" and selection.selected[0].id == fact.id
    assert fact.source.sha256 != case["source_sha256"]
    assert case["independent_review"] is None


def test_examples_cover_all_five_companies() -> None:
    assert {c["cik"] for c in EXAMPLES} == {
        "0000019617",
        "0000320193",
        "0000789019",
        "0001018724",
        "0001652044",
    }
