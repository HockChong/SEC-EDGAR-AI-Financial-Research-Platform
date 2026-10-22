import hashlib
from decimal import Decimal, localcontext
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import ValidationError

from sec_research.contracts.xbrl import NormalizedFacts
from sec_research.processing.xbrl import (
    XbrlError,
    compact_json,
    normalize_company_facts,
    resolve_pointer,
    source_json,
)
from tests.xbrl_helpers import body_for, input_facts, raw_fact


def test_canonical_fixture_replay_precision_and_lineage() -> None:
    body = Path("tests/fixtures/canonical/company_facts.json").read_bytes()
    fetch = input_facts(body)
    with localcontext() as context:
        context.prec = 4
        result = normalize_company_facts(fetch, body)
    assert len(result.observations) == 11
    facts = [r.fact for r in result.observations if r.fact is not None]
    assert len(facts) == 10
    assert any(f.value == Decimal("1234500000.1250000001") for f in facts)
    assert sum("duplicate_observation" in r.reasons for r in result.observations) == 1
    assert sum(r.quality == "failed" for r in result.observations) == 1
    assert NormalizedFacts.model_validate_json(result.model_dump_json()) == result
    assert result.logical_bytes() == normalize_company_facts(fetch, body).logical_bytes()
    assert all(f.source.sha256 == hashlib.sha256(body).hexdigest() for f in facts)
    data = source_json(body)
    for row in result.observations:
        assert compact_json(resolve_pointer(data, row.locator.path)) == row.raw_json
    changed = fetch.model_copy(update={"id": UUID(int=3)})
    assert normalize_company_facts(changed, body).logical_bytes() == result.logical_bytes()


@pytest.mark.parametrize(
    ("updates", "reason"),
    [
        ({"val": True}, "invalid_value"),
        ({"val": "1.2"}, "invalid_value"),
        ({"end": "2024-02-30"}, "invalid_dates"),
        ({"start": "2025-01-01"}, "invalid_dates"),
        ({"start": None}, "invalid_dates"),
        ({"end": None}, "invalid_dates"),
        ({"filed": None}, "missing_filing_metadata"),
        ({"form": None}, "missing_filing_metadata"),
        ({"filed": "2024-02-01"}, "invalid_dates"),
        ({"accn": None}, "missing_accession"),
        ({"accn": "broken"}, "invalid_observation_metadata"),
        ({"fy": True}, "invalid_fiscal_metadata"),
        ({"fp": 4}, "invalid_observation_metadata"),
    ],
)
def test_rejections_preserve_raw(updates: dict[str, object], reason: str) -> None:
    body = body_for([raw_fact(**updates)])
    row = normalize_company_facts(input_facts(body), body).observations[0]
    assert row.quality == "failed" and row.fact is None
    assert row.reasons == (reason,)
    assert row.raw_json


@pytest.mark.parametrize("amount", [0, -42, 123456789012345678901234567890])
def test_signed_exact_integers(amount: int) -> None:
    body = body_for([raw_fact(val=amount)])
    fact = normalize_company_facts(input_facts(body), body).observations[0].fact
    assert fact is not None and fact.value == Decimal(amount)


def test_exponent_lexeme_and_missing_optional_fields() -> None:
    row = raw_fact()
    for key in ("fy", "fp"):
        row.pop(key)
    body = body_for([row]).replace(b'"val": 42', b'"val": -1.23000e+4')
    result = normalize_company_facts(input_facts(body), body)
    fact = result.observations[0].fact
    assert fact is not None and fact.raw_value == "-1.23000e+4"
    assert fact.value == Decimal("-12300") and fact.fy is None and fact.frame is None
    assert result.concepts[0].label is None


def test_unknown_concepts_units_and_json_escaping() -> None:
    body = body_for([raw_fact()], concept="Odd/Name~", taxonomy="custom", unit="EUR/shares")
    result = normalize_company_facts(input_facts(body), body)
    row = result.observations[0]
    assert row.fact is not None and row.fact.unit == "EUR/shares"
    assert "unsupported_metric_concept" in row.reasons and "unsupported_unit" in row.reasons
    assert "Odd~1Name~0" in row.locator.path and "EUR~1shares" in row.locator.path
    assert compact_json(resolve_pointer(source_json(body), row.locator.path)) == row.raw_json


def test_period_kind_is_not_inferred_from_fiscal_metadata() -> None:
    row = raw_fact(fy=2026, fp="Q3", frame="CY2026Q3")
    body = body_for([row], concept="Assets")
    result = normalize_company_facts(input_facts(body), body)
    assert result.observations[0].reasons == ("incompatible_period_type",)
    row.pop("start")
    body = body_for([row])
    assert normalize_company_facts(input_facts(body), body).observations[0].fact is None
    body = body_for([row], concept="Assets")
    fact = normalize_company_facts(input_facts(body), body).observations[0].fact
    assert fact is not None and fact.period.end.isoformat() == "2024-12-31"
    assert fact.period.kind == "instant" and fact.fy == 2026


@pytest.mark.parametrize("body", [b'{"cik":1,"cik":2}', b'{"x":NaN}', b"[]", b"\xff"])
def test_bad_json_is_structured_failure(body: bytes) -> None:
    with pytest.raises(XbrlError, match="invalid_json"):
        source_json(body)


def test_checksum_identity_and_envelope_tampering() -> None:
    body = body_for([raw_fact()])
    fetch = input_facts(body)
    with pytest.raises(XbrlError, match="source_integrity"):
        normalize_company_facts(fetch, body + b" ")
    with pytest.raises(XbrlError, match="source_integrity"):
        normalize_company_facts(fetch.model_copy(update={"processing_status": "quarantined"}), body)
    result = normalize_company_facts(fetch, body)
    data = result.model_dump(mode="json")
    data["observations"][0]["id"] = "occurrence:" + "0" * 64
    with pytest.raises(ValidationError, match="identity mismatch"):
        NormalizedFacts.model_validate(data)


def test_source_value_cannot_be_changed_in_envelope() -> None:
    body = body_for([raw_fact()])
    data = normalize_company_facts(input_facts(body), body).model_dump(mode="json")
    data["observations"][0]["fact"].update({"id": None, "value": "99", "raw_value": "99"})
    with pytest.raises(ValidationError, match="differs from retained source"):
        NormalizedFacts.model_validate(data)


def test_source_unit_cannot_be_changed_in_envelope() -> None:
    body = body_for([raw_fact()])
    data = normalize_company_facts(input_facts(body), body).model_dump(mode="json")
    data["observations"][0]["fact"].update({"id": None, "unit": "EUR", "currency": None})
    with pytest.raises(ValidationError, match="concept metadata mismatch"):
        NormalizedFacts.model_validate(data)


def test_empty_source_labels_preserved() -> None:
    import json

    data = json.loads(body_for([raw_fact()]))
    data["facts"]["us-gaap"]["NetIncomeLoss"].update({"label": "", "description": ""})
    body = json.dumps(data).encode()
    concept = normalize_company_facts(input_facts(body), body).concepts[0]
    assert concept.label == concept.description == ""


@pytest.mark.parametrize("field", ["facts", "entityName", "cik"])
def test_invalid_root_fields(field: str) -> None:
    import json

    data = json.loads(body_for([raw_fact()]))
    data[field] = None
    body = json.dumps(data).encode()
    fetch = input_facts(body_for([raw_fact()])).model_copy(
        update={"sha256": hashlib.sha256(body).hexdigest(), "byte_count": len(body)}
    )
    with pytest.raises(XbrlError, match="invalid_company_metadata"):
        normalize_company_facts(fetch, body)
