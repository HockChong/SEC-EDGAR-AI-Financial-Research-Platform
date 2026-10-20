"""Run with python -m sec_research.ingestion.cli; no network activity on import/help."""

import argparse
import json
import os
from datetime import date, timedelta
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from sec_research.adapters.postgres.database import PostgresDatabase
from sec_research.adapters.postgres.ingestion import PostgresLimiter, PostgresManifest
from sec_research.adapters.sec.client import SecClient, SecPolicy
from sec_research.adapters.storage.local import LocalBronze
from sec_research.contracts.sec import IngestionCode, IngestionError, Source
from sec_research.ingestion.acquisition import Acquisition, reconcile
from sec_research.ingestion.companies import resolve_company
from sec_research.ingestion.company_facts import ingest_company_facts
from sec_research.ingestion.filings import discover_filings
from sec_research.observability.logging import configure_logging
from sec_research.settings import ConfigurationError, load_settings


def positive_int(raw: str) -> int:
    value = int(raw)
    if not 1 <= value <= 1000:
        raise argparse.ArgumentTypeError("limit must be between 1 and 1000")
    return value


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Immutable SEC Bronze acquisition (no parsing)")
    commands = result.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest", help="Resume bounded filing and Company Facts ingestion")
    ingest.add_argument(
        "--company", action="append", required=True, help="CIK, exact ticker or name"
    )
    ingest.add_argument("--from-date", type=date.fromisoformat)
    ingest.add_argument("--to-date", type=date.fromisoformat)
    ingest.add_argument("--max-companies", type=positive_int, default=5)
    ingest.add_argument(
        "--max-filings", type=positive_int, default=20, help="Per company, newest first"
    )
    ingest.add_argument("--max-history-files", type=positive_int, default=100)
    ingest.add_argument("--include-amendments", action="store_true")
    ingest.add_argument(
        "--refresh", action="store_true", help="Revalidate even fresh cached sources"
    )
    ingest.add_argument("--max-age-hours", type=float, default=24)
    ingest.add_argument("--without-facts", action="store_true")
    commands.add_parser(
        "reconcile", help="Verify bytes/manifests and count orphan objects; no deletion"
    )
    return result


def ingest_companies(acquisition: Acquisition, args: argparse.Namespace) -> dict[str, object]:
    if len(args.company) > args.max_companies or not 0 <= args.max_age_hours <= 8760:
        raise IngestionError(IngestionCode.INVALID_METADATA)
    if args.from_date and args.to_date and args.from_date > args.to_date:
        raise IngestionError(IngestionCode.INVALID_METADATA)
    seen: set[str] = set()
    successes = 0
    facts = 0
    errors: list[str] = []
    for query in args.company:
        try:
            cik = resolve_company(query, acquisition)
            if cik in seen:
                continue
            seen.add(cik)
            filings = discover_filings(
                acquisition,
                cik,
                start=args.from_date,
                end=args.to_date,
                include_amendments=args.include_amendments,
                max_filings=args.max_filings,
                max_history_files=args.max_history_files,
            )
            for filing in filings:
                try:
                    acquisition.get(
                        Source(kind="filing", cik=cik, filing=filing, url=filing.source_url)
                    )
                    successes += 1
                except IngestionError as error:
                    if error.code in {
                        IngestionCode.ACCESS_DENIED,
                        IngestionCode.RATE_LIMITED,
                        IngestionCode.DEADLINE,
                    }:
                        raise
                    errors.append(error.code.value)
            if not args.without_facts:
                ingest_company_facts(acquisition, cik)
                facts += 1
        except IngestionError as error:
            errors.append(error.code.value)
            if error.code in {
                IngestionCode.ACCESS_DENIED,
                IngestionCode.RATE_LIMITED,
                IngestionCode.DEADLINE,
            }:
                break
    return {"companies": len(seen), "filings": successes, "company_facts": facts, "errors": errors}


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    database: PostgresDatabase | None = None
    try:
        settings = load_settings()
        if args.command == "ingest" and settings.db_pool_size < 2:
            raise ConfigurationError("Ingestion requires at least two database connections")
        configure_logging(settings.log_level)
        database = PostgresDatabase(settings)
        if database.readiness() is not None:
            raise ConfigurationError("Apply migrations and verify database readiness")
        manifest = PostgresManifest(database.engine)
        store = LocalBronze(settings.artifact_root)
        if args.command == "reconcile":
            print(json.dumps(reconcile(store, manifest), sort_keys=True))
            return 0
        policy = SecPolicy.model_validate(
            {
                "user_agent": os.environ.get("SEC_USER_AGENT", ""),
                "requests_per_second": os.environ.get("SEC_REQUESTS_PER_SECOND", "5"),
                "timeout": os.environ.get("SEC_TIMEOUT_SECONDS", "15"),
                "deadline": os.environ.get("SEC_DEADLINE_SECONDS", "120"),
                "max_attempts": os.environ.get("SEC_MAX_ATTEMPTS", "4"),
                "max_bytes": os.environ.get("SEC_MAX_BYTES", str(32 * 1024 * 1024)),
            }
        )
        client = SecClient(
            policy, limiter=PostgresLimiter(database.engine, policy.requests_per_second)
        )
        run_id = uuid4()
        acquisition = Acquisition(
            client,
            store,
            manifest,
            run_id,
            refresh=args.refresh,
            max_age=timedelta(hours=args.max_age_hours),
        )
        # Identity and credentials never enter run configuration or console output.
        manifest.begin_run(
            run_id,
            {
                "options": vars(args),
                "schema_version": "1",
                "transport": policy.model_dump(exclude={"user_agent"}),
            },
        )
        failed = True
        try:
            summary = ingest_companies(acquisition, args)
            failed = bool(summary["errors"])
            print(json.dumps({"run_id": str(run_id), **summary}, sort_keys=True))
            return 1 if failed else 0
        finally:
            manifest.finish_run(run_id, failed=failed)
    except (ConfigurationError, ValidationError, ValueError, OverflowError):
        print(json.dumps({"error": "invalid_configuration"}))
        return 2
    except IngestionError as error:
        print(json.dumps({"error": error.code.value, "retryable": error.retryable}))
        return 1
    except SQLAlchemyError:
        print(json.dumps({"error": "database_unavailable", "retryable": True}))
        return 1
    finally:
        if database is not None:
            database.close()


if __name__ == "__main__":
    raise SystemExit(main())
