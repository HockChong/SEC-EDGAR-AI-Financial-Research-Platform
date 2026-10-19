# Security architecture

Status: proposed threat model and controls. Controls require implementation and adversarial tests; no security certification or completed assessment is claimed.

## Trust boundaries and threats

| Boundary | Main threats | Required controls and verification |
| --- | --- | --- |
| Browser → API | Unauthorized access, cross-user reports, abuse | Verified identity, server-derived actor scope, per-object authorization, request limits, isolation tests |
| API/worker → SEC | SSRF, redirect escape, access-policy violation | Fixed host/path policies, redirect validation, verified TLS, aggregate limiter, identifying User-Agent |
| Source bytes → parser | Malformed HTML, resource exhaustion, embedded scripts | Size/time/depth limits, no script execution or external entity/resource loading, parser fixtures |
| Evidence/model → tools | Prompt injection, arbitrary queries, privilege escalation | Typed allowlisted tools, application authorization, bounded arguments, no shell/SQL/expression tool |
| Application → providers | Secret leakage, data retention, uncontrolled cost | Scoped secret bindings, approved HTTPS destinations, minimum data sent, provider policy review, usage caps |
| Reports → UI | Stored XSS, unsafe links, deceptive citations | Safe text rendering, sanitized markup, allowlisted source links, evidence resolver, browser tests |
| Jobs/checkpoints → persistence | Cross-tenant resume, poisoned state, double execution | Owner-bound records, schema validation, lease concurrency, idempotency, controlled state migration |
| CI → deployment | Exfiltration from untrusted PRs, compromised dependencies | Least-privilege workflow permissions, frozen locks, reviewed actions, scanning, trusted release path |

## Authorization and identity

Phase 1–6 development may run without user authentication only in an isolated local environment. Before any shared or public deployment, use an OIDC-compatible identity provider and enforce owner/tenant access on jobs, reports, evidence endpoints, and checkpoints. Public SEC artifacts may be shared, but user questions, histories, and run metadata are private. A guessed run ID cannot grant access.

Client-provided tenant IDs, model tool arguments, and retrieved documents cannot alter actor scope. Apply authorization in application services and database queries, including retrieval and parent expansion. Use least-privilege database/service roles. Row-level security can add defense in depth if introduced with integration tests; it does not replace API authorization. Define CORS explicitly; cookie authentication requires CSRF protection and secure cookie settings.

## Prompt injection and evidence safety

SEC content, retrieved excerpts, table text, user questions, and model outputs are untrusted. Delimit content in prompts, but enforce permissions outside the model. Do not let instructions in a filing select a new tool, change a destination, override a budget, or disclose secrets. The model gets evidence IDs and safe data, never raw credentials.

Resolve citations only through the registry. Validate generated schema, allowed tool names/arguments, numeric outputs, source availability, and claim support. Fail closed on unresolvable evidence and unauthorized operations. Evaluate malicious instructions embedded in narrative, table cells, metadata, and retrieved neighbors, including requests to exfiltrate data or ignore historical filters.

## Network and parser controls

Define destination policies per adapter: official SEC sources for ingestion; the selected provider endpoint for models; the configured database and object store for storage. Parse URLs canonically, block unsupported schemes, and revalidate redirects. Reject user-controlled local/private network destinations. Explicitly configured local database endpoints are a separate trusted infrastructure path.

Download with finite size, connection/read deadlines, verified TLS, and bounded retries. Parse HTML/XML without executing scripts, loading external entities, or following remote resources. Preserve raw bytes privately for audit; render safe extracted text in the UI. Cap document complexity, upload/request sizes, retrieved context, output size, tokens, and concurrent jobs.

## Secrets and privacy

Use environment configuration during local development and a managed secret store in deployment. Commit names and non-secret examples only. Do not print environment values, credentials, authentication headers, or credential files. Use existing platform bindings and secure settings; never request secret values in chat.

Only credentials intended for HTTPS proxy injection should use proxy-backed placeholders. A local database password or encryption key may require a different secure runtime mechanism. Provider adapters must accept configured credentials explicitly so reserved environment variable names are not a hidden dependency.

Research questions can reveal investment intent even though filings are public. Minimize provider payloads, review provider retention/training policies, redact telemetry, and define deletion/retention for runs, checkpoints, caches, and backups before shared use. Apply actor scope to cached user results; only verified public-source representations may be globally shared.

## Security acceptance gates

- Unit/contract: rejected extra tool fields, unsupported metrics, arbitrary expressions, disallowed URLs, malformed inputs, and unsafe error details.
- Integration: authorization enforced across report/evidence/job/cancel/checkpoint paths, cross-user idempotency isolation, redirect policy, parser resource limits, secret redaction.
- End-to-end: stored-XSS fixtures, prompt-injection cases, access denial, cancellation, budget exhaustion, and provider outage.
- Deployment: dependency/image scan review, least-privilege identities, secret rotation exercise, backup access restrictions, TLS and network policies, abuse-rate limits.

Security failures involving authorization, arbitrary execution, or secret exposure are release blockers. No prompt, judge score, or overall benchmark average can waive them. Track residual risks, incident response steps, owners, and remediation dates during Phase 7 review.
