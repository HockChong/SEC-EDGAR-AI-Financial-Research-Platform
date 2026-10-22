"""Explicit contract-to-Arrow encoding and create-only local derived storage."""

import hashlib
import os
import tempfile
from collections.abc import Sequence
from datetime import datetime
from functools import cache
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from sec_research.contracts.canonical import (
    CANONICAL_MODELS,
    CanonicalFiling,
    Company,
    ContentBlock,
    DatasetObject,
    DocumentVersion,
    FinancialFact,
    MetricDefinition,
    QualityEvent,
    Record,
    Section,
    SourceProvenance,
    StructuredTable,
    TableCell,
    canonical_bytes,
)
from sec_research.contracts.datasets import (
    Citation,
    DatasetError,
    ParseMetadata,
    ResearchEvidence,
    SelectionEvidence,
    SourceConcept,
    SourceEntry,
    SourceOccurrence,
    TableDetail,
    TableRepresentation,
)
from sec_research.contracts.schemas import schema_bundle

MODELS: dict[str, type[Record]] = {
    "silver_sources": SourceEntry,
    "silver_companies": Company,
    "silver_filings": CanonicalFiling,
    "silver_documents": DocumentVersion,
    "silver_sections": Section,
    "silver_content_blocks": ContentBlock,
    "silver_tables": StructuredTable,
    "silver_table_cells": TableCell,
    "silver_table_details": TableDetail,
    "silver_table_text": TableRepresentation,
    "silver_parse_metadata": ParseMetadata,
    "silver_xbrl_facts": FinancialFact,
    "silver_xbrl_occurrences": SourceOccurrence,
    "silver_xbrl_concepts": SourceConcept,
    "silver_provenance": SourceProvenance,
    "silver_parse_quality": QualityEvent,
    "gold_research_evidence": ResearchEvidence,
    "gold_tables": StructuredTable,
    "gold_table_text": TableRepresentation,
    "gold_reported_facts": FinancialFact,
    "gold_metric_definitions": MetricDefinition,
    "gold_selections": SelectionEvidence,
    "gold_citations": Citation,
}


@cache
def row_schema(model: type[Record]) -> dict[str, Any]:
    if model in CANONICAL_MODELS:
        schemas: Any = schema_bundle()["schemas"]
        return dict(schemas[model.__name__])
    schema = model.model_json_schema(mode="serialization")
    schema["properties"]["id"] = {"type": "string"}
    schema["required"] = sorted(model.model_fields)
    return schema


def _field(name: str, spec: dict[str, Any], defs: dict[str, Any], path: tuple[str, ...]) -> Any:
    if "$ref" in spec:
        spec = defs[spec["$ref"].split("/")[-1]]
    nullable = False
    if "anyOf" in spec:
        choices = spec["anyOf"]
        nullable = any(c.get("type") == "null" for c in choices)
        nonnull = [c for c in choices if c.get("type") != "null"]
        if len(nonnull) != 1:
            raise DatasetError("unsupported_arrow_union")
        spec = nonnull[0]
        if "$ref" in spec:
            spec = defs[spec["$ref"].split("/")[-1]]
    kind = spec.get("type")
    if kind == "object":
        dtype = pa.struct(
            [_field(key, value, defs, (*path, key)) for key, value in spec["properties"].items()]
        )
    elif kind == "array":
        dtype = pa.list_(_field("element", spec["items"], defs, (*path, "element")))
    elif kind == "integer":
        dtype = pa.int64()
    elif kind == "boolean":
        dtype = pa.bool_()
    elif kind == "string":
        fmt = spec.get("format")
        if fmt == "date":
            dtype = pa.date32()
        elif fmt == "date-time" and not {"source", "fetch", "filing"}.intersection(path):
            dtype = pa.timestamp("us", tz="UTC")
        else:
            dtype = pa.string()
    else:
        raise DatasetError("unsupported_arrow_type")
    return pa.field(name, dtype, nullable=nullable)


@cache
def arrow_schema(model: type[Record]) -> Any:
    schema = row_schema(model)
    return pa.schema(
        [_field(k, v, schema.get("$defs", {}), (k,)) for k, v in schema["properties"].items()],
        metadata={
            b"contract": b"canonical-1",
            b"encoding": b"arrow-1",
            b"record": model.__name__.encode(),
            b"schema_sha256": hashlib.sha256(canonical_bytes(schema)).hexdigest().encode(),
        },
    )


def _physical(value: Any, dtype: Any) -> Any:
    if value is None:
        return None
    if pa.types.is_struct(dtype):
        return {field.name: _physical(value[field.name], field.type) for field in dtype}
    if pa.types.is_list(dtype):
        return [_physical(item, dtype.value_type) for item in value]
    if pa.types.is_date32(dtype):
        from datetime import date

        return date.fromisoformat(value)
    if pa.types.is_timestamp(dtype):
        return datetime.fromisoformat(value)
    return value


class LocalDatasets:
    """Derived root must be separate from Bronze; objects/manifests are never replaced."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def path(self, relative: str) -> Path:
        if (
            "\\" in relative
            or ":" in relative
            or any(p in {"", ".", ".."} for p in relative.split("/"))
        ):
            raise DatasetError("unsafe_dataset_path")
        path = self.root / relative
        if not path.resolve().is_relative_to(self.root):
            raise DatasetError("unsafe_dataset_path")
        return Path("\\\\?\\" + str(path)) if os.name == "nt" else path

    def put(self, relative: str, body: bytes) -> None:
        target = self.path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                dir=target.parent, prefix=".stage-", delete=False
            ) as f:
                temporary = f.name
                f.write(body)
                f.flush()
                os.fsync(f.fileno())
            try:
                os.link(temporary, target)
            except FileExistsError:
                if target.read_bytes() != body:
                    raise DatasetError("immutable_dataset_conflict") from None
            if os.name != "nt":
                fd = os.open(target.parent, os.O_RDONLY)
                try:
                    os.fsync(fd)
                finally:
                    os.close(fd)
        finally:
            if temporary is not None:
                Path(temporary).unlink(missing_ok=True)

    def write(self, dataset: str, partition: str, rows: Sequence[Record]) -> DatasetObject:
        model = MODELS[dataset]
        checked = [model.model_validate(r.model_dump(mode="json")) for r in rows]
        checked.sort(key=lambda r: r.id or "")
        if len({r.id for r in checked}) != len(checked):
            raise DatasetError("duplicate_record_id")
        schema = arrow_schema(model)
        physical = [
            {f.name: _physical(row[f.name], f.type) for f in schema}
            for row in (r.model_dump(mode="json") for r in checked)
        ]
        sink = pa.BufferOutputStream()
        pq.write_table(  # type: ignore[no-untyped-call]
            pa.Table.from_pylist(physical, schema=schema),
            sink,
            version="2.6",
            compression="zstd",
            compression_level=3,
            use_dictionary=False,
            write_statistics=True,
            row_group_size=4096,
            data_page_version="1.0",
            store_schema=True,
        )
        body = sink.getvalue().to_pybytes()
        checksum = hashlib.sha256(body).hexdigest()
        item = DatasetObject(
            dataset=dataset,
            path=f"objects/{dataset}/{partition}/{checksum}.parquet",
            sha256=checksum,
            row_count=len(checked),
            schema_sha256=hashlib.sha256(canonical_bytes(row_schema(model))).hexdigest(),
        )
        self.put(item.path, body)
        if self.read(item) != checked:
            raise DatasetError("lossy_parquet_roundtrip")
        return item

    def read(self, item: DatasetObject) -> list[Record]:
        item = DatasetObject.model_validate(item.model_dump())
        model = MODELS[item.dataset]
        body = self.path(item.path).read_bytes()
        if hashlib.sha256(body).hexdigest() != item.sha256:
            raise DatasetError("dataset_checksum_mismatch")
        if hashlib.sha256(canonical_bytes(row_schema(model))).hexdigest() != item.schema_sha256:
            raise DatasetError("dataset_schema_mismatch")
        table = pq.read_table(pa.BufferReader(body))  # type: ignore[no-untyped-call]
        if not table.schema.equals(arrow_schema(model), check_metadata=True):
            raise DatasetError("arrow_schema_mismatch")
        rows = [model.model_validate(r) for r in table.to_pylist()]
        ids = [r.id for r in rows]
        if len(rows) != item.row_count or ids != sorted(set(ids), key=lambda x: x or ""):
            raise DatasetError("dataset_count_or_identity_mismatch")
        return rows
