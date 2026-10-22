"""Offline dataset build/verify and explicit PostgreSQL activation."""

import argparse
import json
from datetime import datetime
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from sec_research.adapters.postgres.database import create_database_engine
from sec_research.adapters.postgres.datasets import DatasetCatalog
from sec_research.adapters.storage.local import LocalBronze
from sec_research.adapters.storage.parquet import LocalDatasets
from sec_research.contracts.datasets import BuildSpec, DatasetError
from sec_research.contracts.sec import IngestionError
from sec_research.contracts.xbrl import SelectionRequest
from sec_research.processing.corpus import audit_bronze
from sec_research.processing.datasets import (
    build_snapshot,
    load_snapshot,
    make_spec,
    record_counts,
    verify_snapshot,
)
from sec_research.settings import ConfigurationError, load_settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser(
        "prepare", help="Pin code, dependencies, requests and logical run clock"
    )
    prepare.add_argument("--code-revision", required=True)
    prepare.add_argument("--run-at", type=datetime.fromisoformat, required=True)
    prepare.add_argument("--requests", type=Path, required=True)
    prepare.add_argument("--lock", type=Path, default=Path("uv.lock"))
    prepare.add_argument("--spec", type=Path, required=True)
    build = sub.add_parser("build")
    build.add_argument("--artifact-root", type=Path, default=Path(".runtime/artifacts"))
    build.add_argument("--inventory", type=Path, default=Path("docs/bronze-corpus-inventory.json"))
    build.add_argument("--spec", type=Path, required=True)
    build.add_argument("--dataset-root", type=Path, required=True)
    for name in ("verify", "activate"):
        command = sub.add_parser(name)
        command.add_argument("--dataset-root", type=Path, required=True)
        command.add_argument("--snapshot-id", required=True)
        if name == "activate":
            command.add_argument("--expected-active", required=True, help="Snapshot ID or 'none'")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            requests = [
                SelectionRequest.model_validate(r) for r in json.loads(args.requests.read_bytes())
            ]
            spec = make_spec(args.code_revision, args.lock, args.run_at, requests)
            args.spec.parent.mkdir(parents=True, exist_ok=True)
            # Specifications are create-only too; never replace a prior run definition.
            with args.spec.open("xb") as output:
                output.write(spec.model_dump_json(indent=2).encode())
            print(json.dumps({"spec": str(args.spec), "code_sha256": spec.code_sha256}))
            return 0
        store = LocalDatasets(args.dataset_root)
        if args.command == "build":
            bronze = LocalBronze(args.artifact_root)
            fetches = audit_bronze(bronze, args.inventory)
            spec = BuildSpec.model_validate_json(args.spec.read_bytes())
            snapshot = build_snapshot(bronze, store, fetches, spec)
            audit_bronze(bronze, args.inventory)
        else:
            snapshot = load_snapshot(store, args.snapshot_id)
            if args.command == "verify":
                verify_snapshot(store, snapshot)
            else:
                engine = create_database_engine(load_settings())
                try:
                    DatasetCatalog(engine).activate(
                        store,
                        args.snapshot_id,
                        expected_active=None
                        if args.expected_active == "none"
                        else args.expected_active,
                    )
                finally:
                    engine.dispose()
        print(
            json.dumps(
                {
                    "snapshot_id": snapshot.id,
                    "dataset_version": snapshot.silver.dataset_version,
                    "command": args.command,
                    "record_counts": record_counts(snapshot),
                    "quality": "warning",
                    "limitations": snapshot.limitations,
                    "independent_financial_accuracy": "not_performed",
                },
                sort_keys=True,
            )
        )
        return 0
    except (DatasetError, IngestionError) as error:
        print(json.dumps({"status": "failed", "code": error.code}))
    except (ValidationError, ConfigurationError):
        print(json.dumps({"status": "failed", "code": "invalid_dataset_contract"}))
    except SQLAlchemyError:
        print(json.dumps({"status": "failed", "code": "dataset_catalog_unavailable"}))
    except (OSError, ValueError, KeyError):
        print(json.dumps({"status": "failed", "code": "dataset_io_or_integrity"}))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
