"""WP3.4 source occurrences and selected results; canonical facts stay unchanged."""

import json
from datetime import date
from decimal import Decimal
from typing import Literal, Self

from pydantic import model_validator

from sec_research.contracts.canonical import (
    Cik,
    Company,
    FinancialFact,
    QualityState,
    RecordId,
    ReportingPeriod,
    SourceLocator,
    SourceProvenance,
    Text,
    ValueModel,
    canonical_bytes,
    stable_id,
)
from sec_research.domain.periods import PeriodAssessment, assess_period


class ConceptMetadata(ValueModel):
    taxonomy: Text
    concept: Text
    label: str | None
    description: str | None
    locator: SourceLocator


class FactOccurrence(ValueModel):
    id: RecordId
    locator: SourceLocator
    # Compact source JSON retains numeric lexemes and all unrecognized source fields.
    raw_json: str
    fact: FinancialFact | None
    period_assessment: PeriodAssessment | None
    quality: QualityState
    reasons: tuple[Text, ...]

    @model_validator(mode="after")
    def disposition(self) -> Self:
        if (self.fact is None) != (self.quality == "failed"):
            raise ValueError("only rejected occurrences may lack a canonical fact")
        if self.fact is not None:
            if self.fact.locator != self.locator or self.fact.quality != self.quality:
                raise ValueError("occurrence and fact disagree")
            if self.period_assessment != assess_period(self.fact.period):
                raise ValueError("period diagnostic mismatch")
        elif self.period_assessment is not None:
            raise ValueError("rejected occurrence cannot assert a period")
        return self


class NormalizedFacts(ValueModel):
    schema_version: Literal["xbrl-result-1"] = "xbrl-result-1"
    normalizer_version: Literal["company-facts-1"] = "company-facts-1"
    company: Company
    concepts: tuple[ConceptMetadata, ...]
    observations: tuple[FactOccurrence, ...]
    provenance: SourceProvenance

    @model_validator(mode="after")
    def graph(self) -> Self:
        source = self.company.source
        if source.source.kind != "company_facts" or self.company.pipeline_version != "xbrl-1":
            raise ValueError("Company Facts envelope requires its versioned source company")
        if (
            self.provenance.source != source
            or self.provenance.entity_id != self.company.id
            or self.provenance.locator is not None
        ):
            raise ValueError("Company Facts provenance mismatch")
        pointers: set[str] = set()
        concepts = {(c.taxonomy, c.concept): c for c in self.concepts}
        if len(concepts) != len(self.concepts):
            raise ValueError("duplicate concept metadata")
        for metadata in self.concepts:
            expected_path = "/facts/" + "/".join(
                token.replace("~", "~0").replace("/", "~1")
                for token in (metadata.taxonomy, metadata.concept)
            )
            if metadata.locator.kind != "json_pointer" or metadata.locator.path != expected_path:
                raise ValueError("concept source pointer mismatch")
        for row in self.observations:
            if row.locator.path in pointers:
                raise ValueError("duplicate source pointer")
            pointers.add(row.locator.path)
            expected = occurrence_id(source.sha256, row.locator.path, row.raw_json)
            if row.id != expected:
                raise ValueError("occurrence identity mismatch")
            if row.fact is not None and (
                row.fact.source != source
                or row.fact.cik != self.company.cik
                or row.fact.normalizer_version != self.normalizer_version
            ):
                raise ValueError("fact ownership mismatch")
            if row.fact is not None:
                fact = row.fact
                concept = concepts.get((fact.taxonomy, fact.concept))
                unit_token = fact.unit.replace("~", "~0").replace("/", "~1")
                if concept is None or not row.locator.path.startswith(
                    concept.locator.path + "/units/" + unit_token + "/"
                ):
                    raise ValueError("fact concept metadata mismatch")
                raw = json.loads(row.raw_json, parse_float=Decimal, parse_int=Decimal)
                if not isinstance(raw, dict) or any(
                    (
                        raw.get("val") != fact.value,
                        raw.get("accn") != fact.accession,
                        raw.get("form") != fact.form,
                        raw.get("filed") != fact.filed.isoformat(),
                        raw.get("start")
                        != (fact.period.start.isoformat() if fact.period.start else None),
                        raw.get("end") != fact.period.end.isoformat(),
                        raw.get("fy") != fact.fy,
                        raw.get("fp") != fact.fp,
                        raw.get("frame") != fact.frame,
                        fact.context_status != "unknown",
                        fact.pipeline_version != "xbrl-1",
                    )
                ):
                    raise ValueError("canonical fact differs from retained source observation")
        return self

    def logical_bytes(self) -> bytes:
        return canonical_bytes(self.model_dump(mode="json", exclude={"provenance"}))


def occurrence_id(checksum: str, pointer: str, raw_json: str) -> str:
    return stable_id("occurrence", ["company-facts-1", checksum, pointer, raw_json])


class SelectionRequest(ValueModel):
    cik: Cik
    metric: Text
    period: ReportingPeriod
    as_of: date
    form: Literal["10-K", "10-Q", "10-K/A", "10-Q/A"] | None = None
    mode: Literal["original", "latest_as_of", "compare_versions"] = "latest_as_of"
    # Source scope does not pretend to verify missing XBRL dimensions.
    context_policy: Literal["company_facts_entity", "verified_consolidated"] = (
        "company_facts_entity"
    )


class CandidateDecision(ValueModel):
    fact_id: RecordId
    observation_id: RecordId
    eligible: bool
    reasons: tuple[Text, ...]


class FactSelection(ValueModel):
    schema_version: Literal["fact-selection-1"] = "fact-selection-1"
    policy_version: Literal["fact-selection-1"] = "fact-selection-1"
    catalog_version: Literal["reported-metrics-1"] = "reported-metrics-1"
    request: SelectionRequest
    metric_id: RecordId | None
    status: Literal["selected", "compared", "unsupported", "unavailable", "ambiguous"]
    quality: QualityState
    selected: tuple[FinancialFact, ...] = ()
    alternatives: tuple[FinancialFact, ...] = ()
    decisions: tuple[CandidateDecision, ...] = ()
    reasons: tuple[Text, ...]

    @model_validator(mode="after")
    def selected_state(self) -> Self:
        if self.status == "selected" and len(self.selected) != 1:
            raise ValueError("selected result requires exactly one fact")
        if self.status not in {"selected", "compared"} and self.selected:
            raise ValueError("abstention must not promote facts")
        return self
