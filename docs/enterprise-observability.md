# Enterprise observability / SSO / multi-worker — FUTURE WORK (unvalidated)

This branch preserves scaffolding for production-grade platform features that
were explored during hardening but **deliberately not shipped** in the prototype
(see PR #28 `feat/participant-auth`). They are kept here as a labelled starting
point so the work isn't lost — **they are not wired into the app and have never
been exercised end-to-end.** Treat them as unvalidated scaffolding, not working
features.

## What's here

| Module | Purpose | Why it's future work |
| --- | --- | --- |
| `app/metrics.py` | Prometheus counters/histogram/gauge + `/metrics` body | Not wired: no `/metrics` endpoint or middleware in `main.py`. Nobody scrapapes metrics on a free-tier prototype. |
| `app/observability.py` | Guarded Sentry + OpenTelemetry init | Not wired: `setup_observability()` isn't called. Needs a Sentry DSN + an OTLP collector (procurement decision). |
| `app/security_oidc.py` | Entra ID / OIDC JWKS JWT verification | Not wired: `verify_oidc_token` isn't called from `resolve_principal`/`get_facilitator`. Needs an IdP tenant + app registration, and a product decision on mapping an IdP identity to a workshop participant. |
| `app/services/pg_event_bus.py` | Postgres `LISTEN`/`NOTIFY` event bus (multi-worker SSE) | Not wired: `get_event_bus()` always returns the in-memory bus. Needed only when running >1 uvicorn worker. |
| `app/audit.py` | Structured audit logger | Not wired: no route calls `audit(...)`. The opaque-token + request-id logging covers the prototype's needs. |

Plus their isolation-only tests: `tests/test_metrics.py`, `tests/test_oidc.py`,
`tests/test_pg_event_bus.py`, `tests/test_audit.py`. Each was unit-tested in
isolation; none validate the wiring described below.

## Dependencies (not in `requirements.txt`)

Reviving these requires adding: `prometheus-client`, `sentry-sdk[fastapi]`,
`opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp`,
`PyJWT`, `cryptography`. They were intentionally removed from the prototype's
pinned deps when the modules were quarantined.

## How to revive (each is an independent, infra-gated decision)

- **Metrics**: add the `/metrics` endpoint + the request-labeling middleware to
  `main.py` (see the `HTTP_REQUESTS`/`_route_template` references that were
  stripped). Decide a scraper destination first.
- **Observability**: call `setup_observability()` at the top of `main.py` before
  `app = FastAPI(...)`. Set `SENTRY_DSN` / `OTEL_EXPORTER_OTLP_ENDPOINT`.
- **OIDC/SSO**: import `looks_like_jwt`/`verify_oidc_token` in `dependencies.py`
  and accept a verified JWT as a facilitator `Principal` in `resolve_principal`
  and `get_facilitator`. Configure `OIDC_ISSUER` / `OIDC_JWKS_URL` /
  `OIDC_AUDIENCE` (Entra ID v2 endpoint). Decide how an IdP `sub` maps to a
  workshop participant (a per-session `oidc_sub` column + join claim flow).
- **Postgres bus**: add an `event_bus_backend` setting and have
  `get_event_bus()` return the `PostgresListenNotifyEventBus` when set to
  `"postgres"`. Only worth it once you run >1 uvicorn worker.

## Base

This branch is based on `feat/participant-auth` (PR #28) because the quarantined
modules import `MAX_SUBSCRIBER_QUEUE`, `_safe_put`, and `EventBusProtocol` from
`app/services/event_bus.py`, which #28 introduced. Rebase onto `main` once #28
merges.
