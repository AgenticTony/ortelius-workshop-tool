# Architecture

How the Workshop Tool fits together: the components, the data flow, and the key decisions behind them.

## System overview

```
┌─────────────────┐      REST (JSON)        ┌──────────────────────────┐
│  Flutter app    │ ───────────────────────▶│  FastAPI backend         │
│  (web + mobile) │  sessions, ideas,       │  (Python 3.13)           │
│                 │  votes, analysis, PDF   │                          │
│  • Facilitator  │ ◀───────────────────────│  ┌────────────────────┐  │
│  • Participant  │   SSE (text/event-      │  │  Anthropic Claude  │  │
└─────────────────┘   stream) live events   │  │  (clustering +     │  │
                       │  │  │  summarisation)│  │
                       │  └─────────┬──────────┘  │
                       │            │             │
                       │  ┌─────────▼─────────┐   │
                       │  │  ReportLab (PDF)  │   │
                       │  └─────────┬─────────┘   │
                       └────────────┼─────────────┘
                                    │
                          ┌─────────▼─────────┐
                          │  PostgreSQL       │
                          │  (Supabase /      │
                          │   local compose)  │
                          └───────────────────┘
```

**One backend, one database, one real-time channel.** The Flutter app talks to the FastAPI backend over REST for everything that mutates state, and over Server-Sent Events (SSE) for live updates.

## Components

### Frontend — Flutter (web + mobile)
- **Riverpod** for state management; **dio** for HTTP (with a bearer-token interceptor for facilitator auth); **go_router** for routing.
- Two roles from one app: **facilitator** (create session, run analysis, download PDF) and **participant** (join, submit ideas, vote).
- Real-time via an SSE client (`lib/services/sse_client.dart`) that reads `text/event-stream` and emits typed events.

### Backend — FastAPI
- **Routes:** sessions, ideas (incl. voting), analysis, SSE stream. See [`api_reference.md`](api_reference.md).
- **Services:** `claude_service` (AI clustering + summarisation), `pdf_service` (ReportLab report generation), `event_bus` (in-memory pub/sub for SSE).
- **Pluggable framework system** (`frameworks.py`): SWOT, PESTEL, and custom frameworks all flow through one code path. See [`frameworks.md`](frameworks.md).
- **Typed errors + global handler:** Claude outages → 503, parse failures → 502, never a stack trace leak. See [`api_reference.md`](api_reference.md#error-responses).

### Database — PostgreSQL (Supabase in prod, local in compose)
- Four tables: `sessions`, `participants`, `ideas`, `analyses`. Schema managed by **Alembic migrations** (`backend/alembic/`); the container entrypoint runs `alembic upgrade head` on boot.
- Single source of truth — both REST reads/writes and the SSE event bus key off `session_id`.

### AI — Anthropic Claude
- `claude-sonnet-4-5-20250929`, called via the Anthropic SDK. The prompt is **framework-aware** and **versioned** (`backend/prompts/clustering_v1.md`). See [`prompt_design.md`](prompt_design.md).
- Output is structured JSON matching a Pydantic schema, with a one-shot retry on parse failure.

## Data flow — a full workshop

1. **Facilitator creates a session** → `POST /sessions` (topic + framework). Backend issues a one-time facilitator token + a 6-char access code.
2. **Participants join** → scan QR / enter code → `POST /sessions/join/{code}`. They get a `participant_id`.
3. **Ideas flow live** → participant submits via `POST /ideas`; backend publishes an `idea_added` SSE event; every connected client (facilitator dashboard + other participants) sees it appear in real time.
4. **Voting** → `POST /ideas/{id}/vote` → `idea_voted` SSE event → vote counts update everywhere.
5. **Facilitator triggers analysis** → `POST /analyse` (with bearer token) → backend sends all ideas to Claude → Claude clusters them into the framework's categories + extracts themes/decisions/questions/next-steps → stored in `analyses`.
6. **PDF report** → `GET /report` (with bearer token) → ReportLab renders the clustered result → browser downloads a consultant-ready PDF.

## Key decisions & trade-offs

### Real-time via SSE, not Firebase Firestore
The original plan (Anthony + Mohand) used Firebase Firestore for real-time idea sync — Flutter writes to Firestore, backend reads from it. **Firestore was dropped** because it was never built, the backend already reads ideas from PostgreSQL, and maintaining a second database for real-time added cost and complexity for no gain. SSE over the existing backend delivers the same "live" feel with one less cloud dependency.

**Trade-off:** the in-memory SSE event bus is **single-worker only**. Scaling to multiple uvicorn workers needs Postgres `LISTEN/NOTIFY` or an external broker (Redis). Flagged as future work.

### Hybrid → single database
Similarly, the "hybrid" architecture (Firestore for real-time, Postgres for persistence) collapsed into a single Postgres once Firestore was removed. Simpler, fewer moving parts, fixed cost.

### Facilitator auth: bearer token, not accounts
A facilitator gets an opaque token at session creation (stored hashed). It gates cost-incurring routes (`/analyse`, `/report`). No accounts, no SSO — fine for workshops. See [`api_reference.md`](api_reference.md#authentication-facilitator-token).

### Frameworks as config, not code
Christian's feedback ("accept any matrix-form template") drove the `FrameworkConfig` registry. Adding a framework is a JSON/dict entry, not a code change. See [`frameworks.md`](frameworks.md).

## Operational

- **Local dev:** `docker compose up` brings up Postgres + API in one command. The Flutter app runs separately (`flutter run`). See [`README.md`](../README.md).
- **Migrations:** Alembic. `alembic upgrade head` runs automatically in the container entrypoint; locally `alembic upgrade head` from `backend/`.
- **Observability:** every Claude call logs prompt version, framework, token counts, and latency. Request IDs propagate via `X-Request-ID`. See [`prompt_design.md`](prompt_design.md#per-call-logging).
- **CI:** GitHub Actions runs `pytest` + `ruff` (backend) and `flutter analyze` (frontend) on every push/PR.
