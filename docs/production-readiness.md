# Backend Plan — Workshop Support Tool

Working notes for the FastAPI backend. Update as work progresses.

**Last updated:** 21 May 2026
**Owner:** Anthony (backend)
**Counterpart:** Mohand (Flutter)

---

## Where we are

- FastAPI backend running, basic structure in place
- SWOT clustering working at ~97% accuracy on eval dataset
- 30 tests passing
- PDF generation working (ReportLab)
- DB layer is already generic (`categories: JSON`, `custom_categories: JSON`)
- Architecture decided: Firestore for real-time, PostgreSQL (Supabase) for persistence
- Repo set up, backend skeleton in place

---

## What changed after Christian's email (21 May 2026)

Christian's reply shifts the framework design from "support specific frameworks (SWOT, PESTEL)" to "accept any matrix-form template that includes a description of what each box means." His exact words:

> "Något som hade varit bra är om ni kan ta in en befintlig godtycklig mall innehållande beskrivning av innehållet och generera utifrån detta. På så sätt kan man tex. Hantera vilken typ av workshop som helst där materialet strukturerats in någon matrisform, vilket ofta är fallet."

Two practical implications:

1. **Categories need descriptions, not just names.** SWOT becomes a config that says "Strengths = internal positive factors", not a hardcoded label.
2. **Most consulting frameworks are matrices** (SWOT 2x2, stakeholder map 2x2, RACI grid). The data model should support this, even if the first PDF version doesn't render true matrix layout.

Christian is sending example material next week. Don't lock framework descriptions in until that arrives. We can refactor the *structure* now and refine the *content* when the examples land.

He also confirmed: individual weekly reports plus a shared project status. Process thing, not code.

---

## Production-grade vs prototype

The goal is to build a prototype with production-grade hooks already in place, so flipping to production is configuration not rewrite. If Ortelius decides to run this for real clients (IKEA, Volvo, etc.) we should not need to rearchitect.

What "production-grade hooks" means in practice:

- All secrets in env vars from day one, ready to swap to a secret manager
- Structured logging from day one, ready to plug into Sentry / Datadog
- Database migrations via Alembic from day one (no manual schema changes)
- API versioning (`/v1/`) so we can break things later without breaking clients
- Rate limiting and cost caps from day one
- Audit logging from day one (Ortelius governance requirement, not optional for them)

What stays prototype-level until/unless Ortelius decides to productionise:

- Single instance, no HA
- No sophisticated caching layer
- No multi-tenancy
- Firebase Anonymous Auth for participants (fine for workshops, not for enterprise SSO)

These can all flip later without rearchitecting if we do the hooks right now.

---

## Refactor: Template-driven framework system

Updated from the earlier plan. Adds per-category descriptions and optional matrix metadata.

### Files to change

| File | Action | What |
|------|--------|------|
| `backend/app/frameworks.py` | NEW | `Category`, `Axis`, `FrameworkConfig` models, built-in registry, prompt builder, `get_framework()` |
| `backend/app/models/analysis.py` | MODIFY | `categories: dict[str, list[ClusteredIdea]]` |
| `backend/app/models/session.py` | MODIFY | Validator for framework + `custom_categories`. Accept either `list[str]` (backward compat) or `list[Category]` (richer) |
| `backend/app/services/claude_service.py` | MODIFY | Use `frameworks.py` to build prompt dynamically. Inject category descriptions into prompt |
| `backend/app/services/pdf_service.py` | MODIFY | Generic category grid using `Axis` metadata if available, fall back to cycling colour palette |
| `backend/app/routes/analysis.py` | MODIFY | Pass `session.custom_categories` to `analyse_ideas()` |
| `backend/eval/run_eval.py` | MODIFY | Dynamic category flattening in `run_live` and `run_bart` |
| `backend/eval/test_inputs.json` | MODIFY | Add 2-3 PESTEL test cases, custom-framework test case when Christian's examples arrive |
| `backend/docs/backend-roadmap.md` | MODIFY | Tick items as we go |

No changes needed: `tests/`, `conftest.py`, `__init__.py`, DB models (already generic).

### Models

```python
class Category(BaseModel):
    id: str           # "S", "P_political", etc. Short stable ID.
    name: str         # "Strengths"
    description: str  # "Internal positive factors the organisation can leverage"

class Axis(BaseModel):  # Optional, for matrix-form rendering later
    label: str        # "Source"
    values: list[str] # ["Internal", "External"]

class FrameworkConfig(BaseModel):
    id: str                                # "swot"
    name: str                              # "SWOT Analysis"
    description: str                       # "Internal vs external, positive vs negative"
    categories: list[Category]
    axes: dict[str, Axis] | None = None    # Optional. PDF service falls back to grid if None.
```

### Built-in registry (initial)

- `swot`: 4 categories with placeholder descriptions (refine when Christian's examples arrive)
- `pestel`: 6 categories with placeholder descriptions (same)
- `custom`: built at runtime from `custom_categories` passed at session creation

### Implementation order

1. Create `frameworks.py` with models and registry. No dependencies, new file.
2. Update `models/analysis.py` to use generic dict. Existing tests pass because they already use plain dicts.
3. Add validator to `models/session.py` supporting both `list[str]` and `list[Category]` in `custom_categories`.
4. Refactor `claude_service.py`: delete hardcoded SWOT prompt, import from `frameworks.py`, inject category descriptions into prompt.
5. One-line change in `routes/analysis.py` to pass through `session.custom_categories`.
6. Refactor `pdf_service.py`: replace `_build_swot_grid` with `_build_category_grid`. Use `Axis` if present, otherwise dynamic columns (2 for ≤4 categories, 3 for 5+). Cycle through an 8-colour palette.
7. Update eval: dynamic category flattening, add PESTEL test cases.
8. Run all tests. The 30 existing tests must pass unchanged.

### Verification

- `pytest tests/ -v` — all 30 existing tests pass
- `python eval/run_eval.py` — mock mode works
- `python eval/run_eval.py --live` — SWOT cases still score ~97%
- Create session with `framework: "pestel"`, run analysis, download PDF. Verify PESTEL grid renders.
- Create session with `framework: "custom"` and 5 user categories, run analysis, download PDF.
- Add 2+ PESTEL test cases to eval. Target 80%+ accuracy on PESTEL.

---

## Production-grade work

Organised by concern. Each item flagged: **(demo)** required for the 12-week prototype, or **(prod)** required to flip to real production usage.

### Security and authentication

- [ ] **(demo)** Firebase Anonymous Auth for participants (already in spec)
- [ ] **(demo)** Facilitator auth via short-lived token. Token issued by `POST /sessions`, required on `/analyse`, `/report`. Store hash in DB.
- [ ] **(demo)** Firestore security rules: users can only edit their own ideas, anonymous auth only, analysis writable only by backend
- [ ] **(demo)** CORS locked down to known origins, not `*`
- [ ] **(demo)** HTTPS only in production
- [ ] **(prod)** Migrate secrets from env vars to Azure Key Vault or Supabase secret manager
- [ ] **(prod)** Proper facilitator accounts (anonymous-only is fine for prototype)
- [ ] **(prod)** SSO if Ortelius requires it
- [ ] **(prod)** Penetration test before going live with real client data

### Rate limiting and cost protection

- [ ] **(demo)** Rate limit on `POST /sessions/{id}/analyse`: max 3 calls per session, max 100 calls per IP per hour
- [ ] **(demo)** Daily token budget cap with logged warning before it hits
- [ ] **(demo)** Per-Claude-call logging: prompt version, input tokens, output tokens, latency, cost estimate
- [ ] **(demo)** Document estimated cost per session in README
- [ ] **(prod)** Per-tenant token quotas if Ortelius runs multi-tenant
- [ ] **(prod)** Alerting on cost anomalies (e.g., 10x daily average)

### Input validation and error handling

- [ ] **(demo)** Custom exception classes (`SessionNotFoundError`, `ClaudeAPIError`, `RateLimitError`, etc.)
- [ ] **(demo)** Global exception handler returning `{detail: "..."}` with the right status code
- [ ] **(demo)** Input limits: max idea length 1000 chars, max ideas per session 200, max sessions per facilitator 50
- [ ] **(demo)** Sanitise text inputs (strip control chars, length limits)
- [ ] **(demo)** Validate `framework` and `custom_categories` on session creation
- [ ] **(demo)** Retry on Claude JSON parse failure with corrective prompt
- [ ] **(demo)** Graceful degradation if Firebase is down (degraded mode, log alerts)

### Observability

- [ ] **(demo)** Structured JSON logging from day one (loguru or structlog)
- [ ] **(demo)** Request IDs propagated through all log lines
- [ ] **(demo)** `/health` endpoint returns DB + Firebase connectivity status, not just "OK"
- [ ] **(demo)** Eval accuracy tracked over time in `eval/results_log.md`, committed to repo
- [ ] **(prod)** Sentry integration for error tracking
- [ ] **(prod)** Prometheus-style `/metrics` endpoint
- [ ] **(prod)** Datadog or similar for dashboards
- [ ] **(prod)** Per-route latency histograms
- [ ] **(prod)** Uptime monitoring (UptimeRobot or similar)

### Data and migrations

- [ ] **(demo)** Alembic migrations from day one (no manual schema changes ever)
- [ ] **(demo)** Idempotency on `POST /sessions/{id}/analyse` — return cached result if same idea-set hash, don't re-bill
- [ ] **(demo)** Soft deletes for sessions (set `deleted_at`, don't hard-delete)
- [ ] **(demo)** Database connection pooling configured
- [ ] **(prod)** Backup strategy documented (Supabase has automated backups, just note retention policy)
- [ ] **(prod)** Data retention policy: how long do we keep session data, ideas, participants
- [ ] **(prod)** GDPR delete flow: participant requests their name removed

### Governance and audit (Ortelius-specific)

Ortelius's whole methodology is around traceable, governed information. This isn't optional for them, even at prototype stage. If we ship without this, the prototype isn't credible.

- [ ] **(demo)** Audit log table: every analysis call recorded with who triggered, when, what session, what input ideas, what output
- [ ] **(demo)** Provenance in PDF output: every clustered idea shows the participant's name
- [ ] **(demo)** Prompt versions tracked in `prompts/` directory with CHANGELOG.md
- [ ] **(demo)** Eval results logged with date, prompt version, accuracy
- [ ] **(prod)** Per-session audit export endpoint: Ortelius asks "show me everything that happened in this workshop", we return a JSON dump
- [ ] **(prod)** Workshop data ownership documented (who owns the data — Ortelius, or the end client?)

### API design

- [ ] **(demo)** API versioning prefix `/v1/` from day one
- [ ] **(demo)** Pagination on `GET /sessions/{id}/ideas` (cursor-based, default limit 100)
- [ ] **(demo)** Consistent error format: `{detail: str, code: str, request_id: str}`
- [ ] **(demo)** OpenAPI spec auto-generated (FastAPI does this free at `/docs`)
- [ ] **(demo)** Strong response models, no `dict[str, Any]` return types
- [ ] **(prod)** Deprecation headers when we move things between versions

### Testing

- [ ] **(demo)** Unit tests for routes, services, models. Currently 30 passing, keep building.
- [ ] **(demo)** Integration tests with mocked Claude (fast deterministic)
- [ ] **(demo)** Eval tests with real Claude (slower, run before AI changes are merged)
- [ ] **(demo)** CI: GitHub Actions runs tests + linting (ruff) on every push
- [ ] **(demo)** Coverage tracking, target 70%+ on `app/`
- [ ] **(prod)** Load testing for concurrent workshop sessions (locust)
- [ ] **(prod)** Chaos testing for Firebase / Claude failures

### Operational

- [ ] **(demo)** Dockerfile builds and runs locally
- [ ] **(demo)** docker-compose for local dev (API + Postgres)
- [ ] **(demo)** Configuration validation on startup. App must refuse to start if critical env vars missing.
- [ ] **(demo)** README explains how to run locally (clone, env vars, docker compose up)
- [ ] **(prod)** Deployment to Render / Railway / Azure App Service
- [ ] **(prod)** Rollback procedure documented
- [ ] **(prod)** Runbook for common issues: Claude down, Firebase down, eval accuracy drop, hot route slow

---

## Out of scope for prototype (future dev)

Listing these so they're deliberately deferred, not forgotten.

- Multi-tenant isolation (one instance per Ortelius client)
- SSO for facilitators
- Real-time collaboration on analysis editing
- Webhooks (e.g., notify Slack when a workshop ends)
- Framework editor UI (facilitator currently passes JSON, no UI to build templates)
- Matrix-form PDF rendering using the `axes` metadata (structure in place, rendering deferred)
- Internationalisation (English-only for now)
- Mobile-native facilitator app (Flutter web works for facilitator)
- Workshop replay / history view
- Export to Word or PowerPoint (PDF only for now)
- Real-time AI suggestions during the workshop (batch analysis at the end only)
- Vector search across past workshops for "have we seen this idea before"

---

## Open questions for Christian (Monday check-in)

1. Confirm what "gemensam projektstatus" means. Separate doc, or the Monday meeting itself?
2. Are there any in-house Ortelius frameworks they'd want as built-in defaults beyond SWOT and PESTEL?
3. Data retention: how long should we keep workshop data after the session ends?
4. Workshop data ownership: Ortelius, or the end client (IKEA, Volvo, etc.)?
5. Workshop materials he'll send next week: any specific examples we should prioritise testing against?

---

## Weekly checklist (Friday end-of-week ritual)

- [ ] Tick completed items above
- [ ] Push backend-roadmap.md update to repo
- [ ] Update eval results log if AI work happened this week
- [ ] Update individual weekly status report
