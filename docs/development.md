# Foundation development guide

Phase 1 supports isolated local/cloud development. Phase 2 adds SEC acquisition through the [ingestion CLI](ingestion.md); research endpoints, model access, authentication and a frontend remain future work. Foundation checks need no SEC/model credentials. Live ingestion needs a real SEC contact identity.

## Verified toolchain

| Component | Version |
| --- | --- |
| Python | 3.12.14 (`.python-version`; supported package range 3.12 only) |
| uv | 0.12.23 (enforced in `pyproject.toml`) |
| FastAPI / Pydantic / settings | 0.146.0 / 2.14.1 / 2.16.0 |
| SQLAlchemy / psycopg / Alembic | 2.1.5 / 3.3.6 / 1.20.0 |
| Uvicorn | 0.54.0 |
| PostgreSQL / pgvector | 17.8 / 0.8.1 in the digest-pinned Compose image |
| pytest / Ruff / mypy | 9.1.1 / 0.17.1 / 2.4.0 |
| Starlette test client transport | httpx2 2.14.0 (required by the resolved Starlette 1.9.0) |
| WP3.2 HTML parser / development typing stubs | lxml 6.1.3 / lxml-stubs 0.5.1; backend versions are included in parser identity |
| Validated Docker / Compose | 28.4.0 / 2.40.3 |

All direct Python dependencies and the build backend are pinned; `uv.lock` records transitive versions and artifact hashes. Container bases and GitHub Actions use immutable digests/revisions. Updates require lock/image review and the same checks below.

## Install and run

Use the existing checkout; cloud tasks are already isolated and do not need a worktree. Commands below run from the repository root. Install Python 3.12.14, uv 0.12.23, and Docker with Compose v2 using your platform's supported installer if absent. An existing Python tooling environment can install uv with `python -m pip install uv==0.12.23`; do not modify a managed system interpreter that forbids it.

On Windows with native Python/uv, run the shell commands in Git Bash. Wheel validation selects the temporary environment's `Scripts/python.exe` on Windows or `bin/python` on Unix.

```bash
bash scripts/setup.sh
bash scripts/start.sh
```

`setup.sh` performs a frozen dependency sync, starts the Compose database, and explicitly applies Alembic migrations. It is safe to repeat against the development database. `start.sh` starts Uvicorn in the foreground on loopback; Ctrl-C stops it. The API never creates an extension or migrates its schema during startup.

In another shell, inspect responses using a local client:

```bash
curl --fail --silent http://127.0.0.1:8000/health/live
curl --fail --silent http://127.0.0.1:8000/health/ready
```

Expected JSON is `{"status":"alive"}` and `{"status":"ready"}`. Liveness does not query the database. Readiness checks connectivity, the exact migration head, and pgvector 0.8.1. It returns HTTP 503 with a typed error envelope if unavailable/incompatible; it says nothing about later research datasets/models.

## Process configuration

The app reads process environment variables only. It does not implicitly load `.env`. `.env.example` contains documented, public development values; Compose has matching explicit local defaults. Never replace these committed examples with real credentials. Export overrides in your shell or use secure environment settings.

| Variable | Default / requirement |
| --- | --- |
| `DATABASE_URL` | Required by the app/migrations; `postgresql+psycopg` with host, user and database. `setup.sh`/`start.sh` supply the local Compose URL only when unset. Wrapped in `SecretStr`. |
| `APP_ENV` | `development` or `test`; `production` is rejected until shared-deployment controls exist. |
| `LOG_LEVEL` | `INFO`; also `DEBUG`, `WARNING`, `ERROR`. |
| `DB_CONNECT_TIMEOUT` | 3 seconds; range 1–30. Pool waits are also bounded; statements have a 5-second server timeout. |
| `DB_POOL_SIZE` | 5; range 1–20; no pool overflow. |
| `ARTIFACT_ROOT` | `.runtime/artifacts`; Phase 2 immutable Bronze root; keep this path stable across ingestion runs. |
| `DATABASE_PORT` | Shell/Compose setting, default 5432; reflected in the helper scripts' default URL. |
| `API_PORT` | Shell/Compose setting, default 8000. |
| `TEST_DATABASE_URL` | Opt-in test connection, with a dedicated database name ending in `_test`. |
| `BUILD_CA_BUNDLE` | Optional trusted PEM bundle for package downloads during container builds. `build.sh` uses `SSL_CERT_FILE` when this is unset. |

Shell variables override local defaults. Check which database you selected before explicitly applying migrations. API errors contain a stable code, safe message, retry flag, and server-generated request UUID. Configuration failures omit input values. JSON logging emits only allowlisted event metadata and never arbitrary messages, exception text, request URLs, headers, or nested extras; this deliberately limits diagnostics until safe structured events are added.

## Container workflow

```bash
bash scripts/build.sh
bash scripts/docker.sh compose up -d --wait db
bash scripts/docker.sh compose --profile app run --rm migrate
bash scripts/docker.sh compose --profile app up -d --no-build --wait api
```

Stop any host API already using the selected port before starting the container API. The API image runs as UID/GID 10001 with a read-only filesystem and dropped capabilities. Migration files are owned by that user. Migrations are a separate explicit one-shot service, not an automatic side effect of `api` startup.

The database binds to loopback and uses public disposable development credentials. The local role has database/extension creation privileges for setup and integration tests; it is not a production least-privilege role. The API's internal Docker port listens on all container interfaces, but Compose publishes it only on host loopback.

The optional `compose.ca.yaml` mounts a trusted CA bundle as a BuildKit secret for dependency installation. It does not copy the bundle into the runtime image and does not disable TLS verification. `scripts/docker.sh` relocates writable buildx state into a temporary directory without replacing existing Docker authentication/context. `scripts/uv.sh` uses a writable temporary cache and copy mode for cloud filesystems.

```bash
bash scripts/docker.sh compose --profile app stop api db
bash scripts/docker.sh compose --profile app up -d --no-build --wait db api
bash scripts/docker.sh compose --profile app down
```

Stopping or taking the stack down preserves the named PostgreSQL volume. `down --volumes` destroys its data; use that only for intentionally disposable environments. A cloud snapshot may preserve checkout/dependencies but must not be assumed to capture Docker daemon volumes or processes. The current Phase 1 schema can be recreated from migrations; future source data requires explicit backup/storage design.

## Migrations and database tests

Revision `0001_foundation` enables pgvector. Revision `0002_ingestion` adds source work, fetch manifests, run/attempt history and aggregate SEC rate coordination. Readiness requires the current head. Downgrading to `base` removes the revision marker but deliberately retains the extension and any vector data. Extension removal is an administrator action, never `DROP ... CASCADE` in this migration. Reapply restores readiness. Phase 2 refuses downgrade when ingestion runs or sources exist; empty-schema rollback remains supported. Back up and plan an explicit data migration before rolling back nonempty provenance.

```bash
export DATABASE_URL='postgresql+psycopg://sec_research:sec_research_dev@127.0.0.1:5432/sec_research'
bash scripts/uv.sh run --frozen alembic current
bash scripts/uv.sh run --frozen alembic upgrade head
```

For first-time integration-test setup, create a dedicated disposable connection database once:

```bash
bash scripts/docker.sh compose exec -T db createdb -U sec_research sec_research_test
export TEST_DATABASE_URL='postgresql+psycopg://sec_research:sec_research_dev@127.0.0.1:5432/sec_research_test'
bash scripts/check.sh
```

Skip `createdb` if that database already exists. Tests connect through it to create uniquely named temporary databases, migrate only those databases, and drop them afterward. The configured database is never migrated or erased. The test role needs CREATEDB; a missing server, denied privileges, or bad connection fails rather than silently passing. A missing `TEST_DATABASE_URL` makes direct pytest integration fixtures skip; `scripts/test-integration.sh` instead requires it explicitly. Never use a production account here.

## Verification commands

WP3.4 adds the offline [Company Facts audit](xbrl-normalization.md), including
all-five-company replay, source resolution and reported-metric selection examples.
Its outputs remain diagnostic JSON outside Bronze; physical publication is deferred.

WP3.2 offline corpus parsing and source-boundary checks are documented in
[HTML parsing](html-parsing.md). They reuse the stored Bronze corpus without
network access or migrations; large diagnostic outputs stay in `.runtime/`.
On checkouts where the existing pytest cache is protected, set
`PYTEST_ADDOPTS='-o cache_dir=.runtime/pytest-wp32'` before running checks.

WP3.3 adds the offline [table diagnostics command](table-extraction.md) and
[preserved exercises](../exercises/wp33/README.md). Hands-on assignments are paused;
Codex maintains the integrated normalizer and multi-period tests. Optional practice
cases run with `pytest exercises/wp33`; production regressions are in `tests/`.
Use `PYTEST_ADDOPTS='-p no:cacheprovider'` if the existing cache is protected.

```bash
bash scripts/check.sh
bash scripts/test-integration.sh       # requires TEST_DATABASE_URL
bash scripts/verify-wheel.sh
bash scripts/build.sh
```

`check.sh` checks lock consistency, Ruff lint/format, strict mypy, and tests. Without the test URL it selects offline tests and clearly reports integration deselection; with the URL it runs all tests and reports coverage. `verify-wheel.sh` builds wheel/sdist, installs hash-verified locked runtime dependencies into a temporary clean environment, installs the wheel, and verifies its typed contracts/API from outside the checkout. Coverage is diagnostic, not a substitute for critical assertions.

CI has a Python job with a real PostgreSQL/pgvector service and a container job that explicitly migrates and checks both health responses. Distribution artifacts are uploaded by CI; nothing is deployed or pushed to a registry. Actions are pinned and have read-only repository permissions. The workflow has been checked locally; an actual hosted Actions run requires publishing the branch/PR and is not claimed by local verification.

## Troubleshooting and limits

- Read-only home: use the provided wrappers, which relocate only cache/buildx state.
- Build certificate error: provide the approved PEM trust bundle through `BUILD_CA_BUNDLE`; never disable verification or add untrusted certificates.
- HTTP 503 `schema_not_ready`: apply explicit migrations and check the pinned extension/version. Startup does not repair a schema automatically.
- HTTP 503 `database_unavailable`: check the Compose database, selected URL/port, and role permissions. Error responses intentionally do not echo connection details.
- Port occupied: stop only the service you own or choose `DATABASE_PORT`/`API_PORT`; keep test URLs aligned.
- Containers missing after a new cloud task: rerun setup, then start the API and check both health responses. Do not assume process or volume restoration.
- This is an isolated development foundation. No authentication, deployed cloud service, financial claims or retrieval quality is established. Phase 2 ingestion has deterministic verification; a user-executed live one-company smoke check also passed; see the Phase 2 review.

## WP3.5 datasets

See [dataset publication](dataset-publication.md) for pinned build specifications,
offline Silver/Gold builds, verification, explicit activation and rollback.
PyArrow 24.0.0 is the only new dependency. Migration `0003_datasets` adds the
transactional catalog and rebuildable Gold serving projections; Bronze is unchanged.
Research APIs and chunking remain future packages.
