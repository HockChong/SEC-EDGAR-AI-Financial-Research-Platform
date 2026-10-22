"""Portable storage row schemas; emit with python -m sec_research.contracts.schemas."""

import json

from sec_research.contracts.canonical import CANONICAL_MODELS, Record, canonical_bytes


def schema_bundle() -> dict[str, object]:
    """Describe Decimal strings, nested structs and arrays for storage.

    Physical Arrow allocation and Parquet writing belong to WP3.5. Do not infer
    fixed Decimal precision/scale or nullability from sample data.
    """
    schemas: dict[str, object] = {}
    for model in CANONICAL_MODELS:
        schema = model.model_json_schema(mode="serialization")
        # Input can omit the computed identity; persisted rows must carry it.
        schema["properties"]["id"] = {
            "type": "string",
            "pattern": rf"^{model.namespace}:[0-9a-f]{{64}}$",
        }
        schema["required"] = sorted(model.model_fields)
        schemas[model.__name__] = schema
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "schema_version": "canonical-1",
        "identity_version": "id-1",
        "decimal_encoding": "string",
        "schemas": schemas,
    }


def storage_row(record: Record) -> bytes:
    """Revalidate before storage, including model_copy/model_construct objects."""
    checked = type(record).model_validate(record.model_dump(mode="json"))
    return canonical_bytes(checked.model_dump(mode="json"))


if __name__ == "__main__":
    print(json.dumps(schema_bundle(), indent=2, ensure_ascii=False, sort_keys=True))
