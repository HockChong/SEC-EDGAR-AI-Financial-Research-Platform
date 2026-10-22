"""Deterministic Company Facts normalization. No network, database or HTML authority."""

import json
from decimal import Decimal
from typing import cast

from pydantic import ValidationError

from sec_research.contracts.bronze import validated_source
from sec_research.contracts.canonical import (
    Company,
    FinancialFact,
    ReportingPeriod,
    SourceLocator,
    SourceProvenance,
    SourceReference,
)
from sec_research.contracts.sec import IngestionError, normalize_cik
from sec_research.contracts.xbrl import (
    ConceptMetadata,
    FactOccurrence,
    NormalizedFacts,
    occurrence_id,
)
from sec_research.domain.metrics import concept_kind
from sec_research.domain.periods import assess_period
from sec_research.ingestion.payloads import iso_date
from sec_research.ingestion.ports import Fetch

NORMALIZER_VERSION = "company-facts-1"
MAX_BYTES = 32 * 1024 * 1024
MAX_OBSERVATIONS = 250_000


class XbrlError(Exception):
    """Recoverable whole-artifact failure; original Bronze bytes remain authoritative."""

    quality = "failed"

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class NumberToken(str):
    """JSON numeric lexeme, kept separate from quoted strings."""


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _nonfinite(value: str) -> None:
    raise ValueError("nonfinite JSON token")


def source_json(body: bytes) -> dict[str, object]:
    try:
        value: object = json.loads(
            body,
            parse_int=NumberToken,
            parse_float=NumberToken,
            parse_constant=_nonfinite,
            object_pairs_hook=_unique,
        )
        return _object(value)
    except (ValueError, UnicodeError, RecursionError):
        raise XbrlError("invalid_json") from None


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("expected object")
    return cast(dict[str, object], value)


def compact_json(value: object) -> str:
    """Preserve exact numbers and unknown fields in rejected and accepted occurrences."""
    if isinstance(value, NumberToken):
        return str(value)
    if isinstance(value, dict):
        return (
            "{"
            + ",".join(json.dumps(k) + ":" + compact_json(v) for k, v in sorted(value.items()))
            + "}"
        )
    if isinstance(value, list):
        return "[" + ",".join(compact_json(v) for v in value) + "]"
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def resolve_pointer(data: object, pointer: str) -> object:
    current = data
    for token in pointer.split("/")[1:]:
        key = token.replace("~1", "/").replace("~0", "~")
        current = current[int(key)] if isinstance(current, list) else _object(current)[key]
    return current


def _optional_text(data: dict[str, object], key: str, *, allow_blank: bool = False) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if (
        not isinstance(value, str)
        or isinstance(value, NumberToken)
        or (not allow_blank and not value.strip())
    ):
        raise ValueError("invalid optional text")
    return value


def _fact(
    source: SourceReference,
    taxonomy: str,
    concept: str,
    unit: str,
    locator: SourceLocator,
    raw: object,
) -> FinancialFact:
    data = _object(raw)
    value = data.get("val")
    if not isinstance(value, NumberToken):
        raise XbrlError("invalid_value")
    if not data.get("filed") or not data.get("form"):
        raise XbrlError("missing_filing_metadata")
    try:
        end = iso_date(data.get("end"))
        start = iso_date(data["start"]) if "start" in data else None
        filed = iso_date(data.get("filed"))
        period = ReportingPeriod(
            kind="instant" if start is None else "duration",
            start=start,
            end=end,
            duration_class=None if start is None else "unknown",
        )
        if filed < end:
            raise ValueError("end after availability")
    except (IngestionError, ValueError):
        raise XbrlError("invalid_dates") from None
    expected_kind = concept_kind(taxonomy, concept)
    if expected_kind is not None and period.kind != expected_kind:
        raise XbrlError("incompatible_period_type")
    if not data.get("accn"):
        raise XbrlError("missing_accession")
    if not data.get("form"):
        raise XbrlError("missing_filing_metadata")
    fy = data.get("fy")
    if fy is not None:
        if not isinstance(fy, NumberToken) or not fy.isdigit():
            raise XbrlError("invalid_fiscal_metadata")
        fy = int(fy)
    return FinancialFact.model_validate(
        {
            "pipeline_version": "xbrl-1",
            "cik": source.source.cik,
            "taxonomy": taxonomy,
            "concept": concept,
            "raw_value": str(value),
            "value": Decimal(value),
            "unit": unit,
            "currency": "USD" if unit in {"USD", "USD/shares"} else None,
            "period": period,
            "accession": data["accn"],
            "form": data["form"],
            "filed": filed,
            "fy": fy,
            "fp": _optional_text(data, "fp"),
            "frame": _optional_text(data, "frame"),
            "context_status": "unknown",
            "source": source,
            "locator": locator,
            "normalizer_version": NORMALIZER_VERSION,
            "quality": "warning",
        }
    )


def normalize_company_facts(fetch: Fetch, body: bytes) -> NormalizedFacts:
    try:
        source = validated_source(fetch, body)
    except ValueError:
        raise XbrlError("source_integrity") from None
    if source.source.kind != "company_facts":
        raise XbrlError("wrong_source_kind")
    if len(body) > MAX_BYTES:
        raise XbrlError("source_too_large")
    data = source_json(body)
    try:
        raw_cik = data.get("cik")
        if not isinstance(raw_cik, str) or normalize_cik(raw_cik) != source.source.cik:
            raise ValueError("CIK mismatch")
        company = Company.model_validate(
            {
                "pipeline_version": "xbrl-1",
                "cik": source.source.cik,
                "legal_name": data.get("entityName"),
                "source": source,
            }
        )
        taxonomies = _object(data.get("facts"))
    except (ValueError, IngestionError):
        raise XbrlError("invalid_company_metadata") from None
    concepts: list[ConceptMetadata] = []
    observations: list[FactOccurrence] = []
    seen: set[str] = set()
    try:
        for taxonomy, raw_concepts in sorted(taxonomies.items()):
            for concept, raw_definition in sorted(_object(raw_concepts).items()):
                definition = _object(raw_definition)
                base = f"/facts/{pointer_token(taxonomy)}/{pointer_token(concept)}"
                concepts.append(
                    ConceptMetadata(
                        taxonomy=taxonomy,
                        concept=concept,
                        label=_optional_text(definition, "label", allow_blank=True),
                        description=_optional_text(definition, "description", allow_blank=True),
                        locator=SourceLocator(kind="json_pointer", path=base),
                    )
                )
                for unit, rows in sorted(_object(definition.get("units")).items()):
                    if not isinstance(rows, list):
                        raise ValueError("units must contain arrays")
                    for index, raw in enumerate(rows):
                        if len(observations) >= MAX_OBSERVATIONS:
                            raise XbrlError("too_many_observations")
                        locator = SourceLocator(
                            kind="json_pointer", path=f"{base}/units/{pointer_token(unit)}/{index}"
                        )
                        raw_json = compact_json(raw)
                        fact: FinancialFact | None = None
                        reasons: list[str] = []
                        try:
                            fact = _fact(source, taxonomy, concept, unit, locator, raw)
                        except XbrlError as error:
                            reasons.append(error.code)
                        except (ValueError, KeyError):
                            reasons.append("invalid_observation_metadata")
                        if fact is not None:
                            reasons.append("company_facts_context_unknown")
                            if fact.observation_id in seen:
                                reasons.append("duplicate_observation")
                            seen.add(fact.observation_id)
                            if concept_kind(taxonomy, concept) is None:
                                reasons.append("unsupported_metric_concept")
                            if unit not in {"USD", "shares", "USD/shares", "pure"}:
                                reasons.append("unsupported_unit")
                            if fact.fy is None or fact.fp is None:
                                reasons.append("missing_fiscal_metadata")
                            if fact.form not in {"10-K", "10-Q", "10-K/A", "10-Q/A"}:
                                reasons.append("unsupported_filing_form")
                        observations.append(
                            FactOccurrence(
                                id=occurrence_id(source.sha256, locator.path, raw_json),
                                locator=locator,
                                raw_json=raw_json,
                                fact=fact,
                                period_assessment=assess_period(fact.period) if fact else None,
                                quality="warning" if fact else "failed",
                                reasons=tuple(reasons),
                            )
                        )
    except (ValueError, ValidationError):
        raise XbrlError("invalid_concept_structure") from None
    assert company.id is not None
    return NormalizedFacts(
        company=company,
        concepts=tuple(concepts),
        observations=tuple(observations),
        provenance=SourceProvenance(
            pipeline_version="xbrl-1",
            entity_id=company.id,
            source=source,
            fetch_id=fetch.id,
            fetched_at=fetch.fetched_at,
        ),
    )
