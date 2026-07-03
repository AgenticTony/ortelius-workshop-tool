# Frontend Roadmap — Workshop Support Tool

**Project 5 — Ortelius Internship | May–August 2026**

- **Workstream:** Frontend (Flutter, web + mobile)
- **Stack:** Flutter, Riverpod (state), dio (HTTP), qr_flutter (QR codes), flutter_secure_storage (facilitator token), flutter_dotenv (env)
- **Consumes:** The FastAPI backend (see `backend-roadmap.md` and `api-contract.md`)
- **Owner:** Anthony (originally Mohand — transferred after he left the project)

> **Companion doc:** `backend-roadmap.md` tracks the API this frontend talks to. This doc tracks the Flutter app itself. Each milestone ships as its own branch + PR so there's a demoable result at every step.

---

## What changed and why (re-plan, July 2026)

Mohand left the project. Anthony now owns the frontend in addition to the backend. The re-plan:

1. **Flutter stays** — original decision holds. Web + mobile from one codebase.
2. **Firestore is dropped.** It was in the original spec but never built, and the backend already reads ideas from PostgreSQL. "Real-time" is now delivered via an SSE stream (`GET /sessions/{id}/ideas/stream`) instead of Firebase. One less cloud dependency, one less SDK.
3. **Three API gaps closed first (Milestone 1, backend).** Voting, facilitator token auth, and rate limiting were originally going to live in the Firebase layer. With Firebase gone, they become backend endpoints. These must exist before the Flutter screens that need them.
4. **Full prototype scope.** Both facilitator and participant UIs, all three frameworks (SWOT, PESTEL, custom), custom-framework authoring, voting, live feed.

### Architecture defaults (locked)

| Concern | Choice | Why |
|---|---|---|
| State management | Riverpod | Original plan; handles async/SSE well |
| HTTP client | dio | Interceptors to attach the facilitator token |
| Facilitator token storage | flutter_secure_storage | Not in plaintext / not in shared prefs |
| QR codes | qr_flutter | Encode the join URL / access code |
| Real-time transport | SSE (text/event-stream) | Simple, one-directional, no WebSocket lifecycle. **Single-worker uvicorn only** for the prototype — multi-worker needs Postgres LISTEN/NOTIFY (future) |
| Facilitator auth scheme | `secrets.token_urlsafe(32)` at create; SHA-256 hash in DB; `Authorization: Bearer` on protected routes | Stateless, demo-grade |

### Known limitations (flagged, not forgotten)

- SSE is single-worker only (in-memory event bus). Multi-worker → Postgres LISTEN/NOTIFY later.
- Voting is a simple increment for v1; per-participant vote dedup is deferred (no new table now).
- Facilitator auth is a bearer token, not full accounts. Fine for workshops; SSO is future/prod.
- The token-hash column is created via `init_db.create_all` (no Alembic yet — Step 15).

---

## Milestone 1 — Backend API gaps + SSE real-time

**Branch:** `feat/backend-realtime-and-gaps`

This is backend work that unblocks the Flutter build. The frontend can't be built against endpoints that don't exist.

- [ ] **Facilitator token auth**
  - `SessionDB.facilitator_token_hash` (nullable for back-compat; populated on create)
  - `POST /sessions` issues a `secrets.token_urlsafe(32)` token, stores its SHA-256 hash, returns plaintext once in the create response (`facilitator_token` field)
  - New dependency `get_facilitator(session_id, authorization, db)` validates `Authorization: Bearer` against the stored hash
  - Protect `POST /sessions/{id}/analyse` and `GET /sessions/{id}/report`
- [ ] **Voting endpoint** — `POST /sessions/{session_id}/ideas/{idea_id}/vote` → 200, returns updated `Idea`
- [ ] **Rate limiting** (`slowapi`) — `/analyse` 5/min/IP, `/ideas` 30/min/IP; in-memory store
- [ ] **SSE real-time**
  - `app/services/event_bus.py` — in-memory `dict[session_id, set[asyncio.Queue]]`, thread-safe publish
  - `GET /sessions/{session_id}/ideas/stream` → `StreamingResponse(text/event-stream)`
  - Events: `idea_added`, `idea_voted`, `participant_joined`
  - Wire publishes into the relevant POST routes
- [ ] **Tests** — token auth (401/200 cases), voting, SSE stream via AsyncClient
- [ ] **Docs sync** — drop Firestore from `api-contract.md` + `project-final.md`; document vote/stream/token endpoints

**Success criteria:** all backend tests green; `docker compose up` healthy; two curl clients see each other's ideas via the stream in real time.

---

## Milestone 2 — Flutter scaffold + API client + models

**Branch:** `feat/frontend-scaffold`

- [ ] `flutter create frontend --org com.ortelius` (web + mobile), strip placeholder
- [ ] Folder structure: `lib/{core,models,services,features,widgets}`
- [ ] Riverpod setup; dio client in `core/api/` with base URL from `--dart-define`/`.env`
- [ ] Models mirroring backend: `Session`, `Idea`, `Participant`, `AnalysisResult`, `ClusteredIdea`, `Category`, `JoinResponse`
- [ ] Routing skeleton (`go_router`), app theme, environment switcher (local/dev)
- [ ] **Demoable:** app launches, hits `/health`, shows "connected"

> **Why it matters:** A clean scaffold with typed models is the foundation. Getting the API client + auth-interceptor pattern right here means every later screen is just wiring.

---

## Milestone 3 — Participant flow

**Branch:** `feat/frontend-participant`

- [ ] Join screen — access code + name → `POST /sessions/join/{code}`; store `participant_id`
- [ ] Idea submission — content + optional category pre-tag → `POST /ideas`
- [ ] **Live idea feed via SSE** — subscribe to `/ideas/stream`, render incoming ideas
- [ ] Voting UI — tap to upvote → `POST /ideas/{id}/vote`, optimistic update
- [ ] **Demoable:** two devices join, submit ideas, see each other live, vote

> **Why it matters:** This is the real-time UX that makes a workshop tool feel live. SSE from Flutter (via `dio`'s response stream or `http` package) is the interesting bit.

---

## Milestone 4 — Facilitator flow

**Branch:** `feat/frontend-facilitator`

- [ ] Create-session screen — topic + framework picker (SWOT/PESTEL/custom)
- [ ] **Custom-category authoring UI** — ≥2 names when `framework=custom` (Christian's request)
- [ ] Capture + securely store `facilitator_token` from the create response
- [ ] Session dashboard — access code + QR (`qr_flutter`), live participant/idea counts, live feed (reuse SSE)
- [ ] Trigger analysis (`POST /analyse` with bearer token), loading state, render `AnalysisResult` (category grid, key themes, decisions, questions, next steps)
- [ ] Download PDF (`GET /report`)
- [ ] **Demoable:** facilitator creates a custom session, participants join via QR, live ideas, one-click analysis, PDF download

> **Why it matters:** This is the consultant-facing surface — the demo Ortelius sees. The custom-framework authoring is Christian's explicit feedback, so it must work end-to-end.

---

## Milestone 5 — Polish + integration

**Branch:** `feat/frontend-polish`

- [ ] All three frameworks validated end-to-end (SWOT, PESTEL, custom with 3/5/7 categories)
- [ ] Empty / loading / error states across all screens
- [ ] Consistent theming; accessibility pass (contrast, tap targets, semantics)
- [ ] CORS origins updated for the Flutter web origin in `.env`/compose
- [ ] End-to-end smoke against the Dockerized backend
- [ ] `README` updated with frontend run instructions

---

## Cross-cutting checklist

- [ ] Each milestone is its own branch + PR
- [ ] Flutter code passes `flutter analyze` with no warnings
- [ ] API client never hardcodes URLs — always from env
- [ ] Facilitator token never logged or rendered in the UI

---

## Changes from the original plan

| Original | Updated | Why |
|---|---|---|
| Mohand owns frontend | Anthony owns both | Mohand left the project |
| Firestore for real-time | SSE stream endpoint | Firestore was never built; backend already reads from Postgres. One less cloud dependency |
| Voting via Firestore | `POST /ideas/{id}/vote` REST endpoint | Firestore gone; voting needs a home |
| No facilitator auth (Firestore rules covered it) | Bearer-token facilitator auth | Firestore security rules are gone too; protected routes need a gate |
| No rate limiting | `slowapi` on /analyse and /ideas | Cost protection (Claude) + spam protection |
| `frontend_flutter/` directory | `frontend/` (existing empty dir) | Match what's already in the repo |
