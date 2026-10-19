# Phase 1 — Engineering foundation review

Scope: packages 1A–1C under explicit whole-phase authorization. Phase 2 has not started. Work is on the local `feat/phase-1-foundation` branch; no commit, push, hosted Actions run, or cloud deployment is included in this assignment.

## Repository audit and implementation

The starting `main` checkout was clean and contained the approved Phase 0 documents only. There were no existing code modules or tests to duplicate. The architecture, `AGENTS.md`, roadmap, testing strategy, and deployment decisions were reused. Python 3.12.14, uv 0.12.23, Docker 28.4.0 and Compose 2.40.3 were available. Required database configuration bindings were absent; isolated Compose development defaults require no private credentials.

| Package | Delivered scope | Review outcome |
| --- | --- | --- |
| 1A | `src` package, `py.typed`, pinned `pyproject.toml`/`uv.lock`, Python pin, ignore rules, error contract, pytest/Ruff/mypy | Frozen install, initial 4 tests, lint/type checks and wheel/sdist build passed; final suite expands this below. |
| 1B | Typed settings, secret-safe JSON logs/errors, health API, bounded connection pool, explicit Alembic migration, digest-pinned Compose/PostgreSQL/pgvector, non-root image | Real database, migration rollback/reapply, vector data preservation, container migration and health requests validated. |
| 1C | GitHub Actions workflow, setup/start/build/check/wheel scripts, developer documentation and current-status updates, reusable cloud setup/start instructions | Final consolidated validation and configuration-save evidence recorded below. |

## Architecture decisions

- ADR-001/002 are accepted for the foundation: one typed Python package and a verified locked toolchain. Framework boundaries remain small; no later-phase placeholder services or unused application modules were created.
- The health-only API exercises error/config/database infrastructure without implementing research features. Its schema is validated in contract tests.
- PostgreSQL 17.8 and pgvector 0.8.1 are fixed by image digest. Initial migration enables the extension; rollback preserves it and user vector data. No SEC/research schema is introduced.
- Application configuration is explicit process environment, with secret-wrapped database URL, bounded pool/timeouts, and unsupported production mode rejected.
- Structured logging allowlists metadata rather than trying to redact arbitrary strings. Runtime migrations remain separate from API startup.
- Build-only CA injection preserves TLS verification in this cloud's network environment. No CA or credentials are baked into the runtime image.
- CI builds/test-validates artifacts; production delivery and authentication remain in Phase 7 as approved.

## Files created or modified

- Packaging/configuration: `pyproject.toml`, `uv.lock`, `.python-version`, `.gitignore`, `.env.example`, `.dockerignore`.
- Runtime: `src/sec_research/{settings.py,py.typed}`, contracts for errors/health, PostgreSQL database adapter, safe logging, and FastAPI application factory, with package initializers.
- Database/container: `alembic.ini`, migration environment/template/initial revision, `compose.yaml`, optional `compose.ca.yaml`, `Dockerfile`.
- Tests: root isolation fixture, unit configuration/logging/error cases, API contracts, and temporary-database integration fixtures/tests.
- Tooling/delivery: `.github/workflows/ci.yml`; `scripts/{uv,docker,setup,start,build,check,test-integration,verify-wheel}.sh`.
- Documentation: README, AGENTS, roadmap, conventions, architecture status notes, testing strategy, ADR status/evidence, this review, and the development guide.

## Verification evidence

| Executed check | Actual outcome |
| --- | --- |
| `scripts/check.sh` with dedicated `TEST_DATABASE_URL` | Lock check, Ruff lint/format, strict mypy (21 source files), **33 tests passed**, 0 failed/skipped/xfail; **97% coverage**. Tests comprise 22 unit, 6 API contract, and 5 integration cases. |
| Frozen sync into a separate empty virtual environment, then offline pytest | **28 passed, 5 integration tests deliberately deselected**. The full suite above supplies integration evidence. |
| `scripts/verify-wheel.sh` | Wheel and sdist built; locked runtime dependencies installed with hash checking into a separate environment; wheel imports, `py.typed`, and API schema verified from outside the checkout. |
| Distribution inspection | No virtual environment, cache, or private `.env` included in the sdist; wheel contains the typing marker. |
| PostgreSQL integration | Real PostgreSQL 17.8 / pgvector 0.8.1; readiness before/after migration; repeated upgrade; rollback/reapply retaining vector data; vector distance calculation; incompatible/missing schema handling; unreachable connection handling all passed. |
| `scripts/setup.sh` repeated twice | Both succeeded, reusing the database and current revision without destructive state changes. |
| `scripts/build.sh` and explicit container migration | Both images built with verified TLS and digest-pinned bases; migration succeeded under UID/GID 10001. |
| Container functional requests and restart | Both health routes returned HTTP 200 and expected JSON; stopping and restarting API/database retained schema and restored readiness. |
| `API_PORT=8001 bash scripts/start.sh` | Host API returned correct live/ready JSON and valid server-generated request UUIDs; temporary host test process was then stopped. |
| Alembic offline SQL generation | Succeeded without credentials or a live connection. |
| Workflow/shell/Compose validation | actionlint 1.7.7 (official archive checksum verified), `bash -n` on every shell script, and Compose config validation passed. |
| Documentation validation | 27 Markdown documents and 83 local links checked; no broken local links or unbalanced fences. |

The current-instance Compose database and API are left running and healthy. The full suite contains no expected failures or skipped cases when the test database is configured. No benchmark or later-phase application behavior is claimed by these checks.

## Reusable cloud configuration

The cloud configuration tool confirmed `status: saved` for **`install_script`** and **`start_skill`**. The installation script runs tested setup and container-build steps from the repository root. Startup instructions cover the existing isolated checkout, restarting/recreating services, explicit migrations, actual health responses, tests, trusted build CA handling, and host/container development options. Existing repository membership, network rules, and credential requirements were preserved.

The tool returned `requires_publish: true`. **Review and save the draft in environment settings, then publish the environment** to activate its prepared snapshot/configuration. Saving this draft did not publish it, restart services, or validate restoration in a new task.

## Phase 1 acceptance

- [x] Reproducible pinned package/toolchain and clean frozen installation.
- [x] Typed configuration, stable errors, and secret-safe logging.
- [x] Real PostgreSQL/pgvector development environment and explicit migration/rollback behavior.
- [x] Non-root container build, functional health requests, and service restart validation.
- [x] Meaningful unit/contract/integration tests, lint/format, strict typing, and distribution checks.
- [x] CI workflow with local command/workflow validation and artifact build; hosted execution remains unrun.
- [x] Developer instructions, phase review, and reusable cloud install/start fields saved.
- [x] Stop before Phase 2; no SEC ingestion or research features introduced.

## Diagnosed and corrected failures

1. uv/buildx initially attempted writes under the read-only home. Wrappers now place only writable caches/state under a temporary directory and retain existing authentication.
2. The resolved Starlette test client deprecated `httpx`; strict warnings exposed the mismatch. Its supported `httpx2` dependency is now pinned instead of suppressing the warning.
3. Container dependency downloads lacked the platform trust root. A BuildKit-mounted trusted CA bundle fixed verification without disabling TLS.
4. Non-root migration startup could not read root-owned files copied from the restricted workspace. The image now assigns migration/config ownership to its runtime user; rerun succeeded.
5. Initial lint formatting and mypy namespace resolution issues were corrected; tests/config were not weakened to hide failures.

## Limits and next gate

GitHub-hosted CI has not run; local equivalent checks and workflow validation are distinct evidence. No hosted deployment, authentication, SEC access, ingestion, model integration, frontend, financial computation, or AI evaluation was attempted. Cloud draft persistence does not publish an environment or prove restoration in a new task. Docker volumes/processes cannot be assumed to survive a new machine.

The development database role and credentials are intentionally disposable and privileged enough for extension creation and temporary test databases. Production role separation belongs to Phase 7. Logging omits arbitrary messages/tracebacks by design; future observability must add approved structured events. Readiness validates the foundation schema/extension only.

Recommended next assignment after review: **Phase 2A, SEC transport and contracts**, including real SEC identity and current access-policy verification before live requests. **Stop after Phase 1; do not start Phase 2 without explicit authorization.**
