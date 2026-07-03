# Backend Roadmap — Workshop Support Tool

**Project 5 — Ortelius Internship | May–August 2026**

- **Workstream:** AI & Backend
- **Stack:** Python + FastAPI, Anthropic Claude API, ReportLab, PostgreSQL (Supabase), Firebase Firestore (for real-time sync)
- **Integrates with:** Mohand's Flutter frontend (mobile + web)

> **Companion doc:** Production-readiness work and the "demo-grade vs prod-grade" tagging is tracked separately in `production-readiness.md`. This doc focuses on phase-by-phase tasks aligned to the Ortelius schedule.

---

## How to use this document

- Each phase maps to the schedule in the project planning doc
- Tick items as you complete them; keep this file updated in the repo
- Reference current week's items in your Friday weekly status reports
- **"Why it matters"** notes flag the portfolio-relevant work for interviews

---

## Christian's feedback (21 May 2026) — what shifted

Christian's reply to the workshop-examples email pushed two things:

1. **Template-driven, not framework-hardcoded.** The tool should "accept any matrix-form template containing a description of what each category means." So SWOT and PESTEL become *configurations*, not hardcoded labels.
2. **Per-category descriptions matter.** Categories need a `description` field, not just a `name`. His phrase: *"beskrivning av innehållet."*

He'll send real workshop example material next week. Don't lock framework descriptions in until that lands — refactor the *structure* now, refine the *content* when examples arrive.

This adds **Step 9b** in Phase 2 (the framework refactor) and ripples small changes through Steps 7, 8, 11, 18.

---

## Agreed API contract (decisions with Mohand)

These 10 decisions were agreed between Anthony and Mohand. The final spec is in `docs/project-final.md`.

| # | Decision | Agreed | Implemented |
|---|----------|--------|-------------|
| 1 | Join session format | Query param `?name=Anna` | [x] |
| 2 | Join session response | Participant ID only | [x] |
| 3 | Access codes | Generated on session creation | [x] |
| 4 | GET analysis endpoint | Fetch stored results without re-running | [x] |
| 5 | POST /analyse response | Synchronous — returns result directly | [x] |
| 6 | Idea category field | Keep it — participants can pre-tag | [x] |
| 7 | Analysis storage | Hybrid — Firestore (real-time) + PostgreSQL (persistence) | [ ] |
| 8 | QR codes | Frontend generates | N/A |
| 9 | Service layer | Add `firestore_service.py` for cleaner separation | [ ] |
| 10 | Backend folder | `backend/` | [x] |
| 11 | Framework system | Pluggable via `FrameworkConfig` (Christian's feedback) | [x] |

---

## Phase 1: Foundation (Weeks 3–4)

**Goal:** A working FastAPI skeleton with all the architectural decisions locked in, including the evaluation dataset that will measure AI quality from day one.

### Step 1 — FastAPI skeleton
- [x] Project structure (`app/`, `tests/`, `eval/`, `docs/`, `prompts/`)
- [x] FastAPI app with `/health` endpoint
- [x] CORS middleware configured for Flutter web origin
- [x] Auto-generated OpenAPI docs available at `/docs`
- [x] `.gitignore`, `requirements.txt`, `.env.example`
- [x] Shared `get_db()` in `app/dependencies.py` (DRY — used by all routes)

### Step 2 — Pydantic models
- [x] `Session` model (id, topic, framework, **access_code**, status, created_at)
- [x] `Idea` model (id, session_id, participant_id, **participant_name**, **category**, content, votes, created_at)
- [x] `Participant` model with `joined_at` field (per agreed spec)
- [x] `AnalysisResult` model with SWOT categories, key themes, decisions, questions, next steps
- [x] Each clustered idea references the original `idea_id` (provenance traceability — Ortelius governance requirement)
- [x] `JoinResponse` model — returns just `participant_id` (decision 2B)
- [x] `JoinByCodeRequest` model — validates name with min/max length
- [x] Input validation on ideas: content min_length=1, max_length=2000

### Step 3 — Routes (scaffold)
- [x] `POST /sessions` — create a session (**with access_code**, decision 3A)
- [x] `GET /sessions/{id}` — fetch session details
- [x] `POST /sessions/{id}/join?name=...` — participant joins (**returns participant_id only**, decision 1A + 2B)
- [x] `POST /sessions/join/{access_code}` — join via short code (**decision 3A**)
- [x] `POST /sessions/{id}/ideas` — submit an idea (**includes category + participant_name**, decisions 6B + spec)
- [x] `GET /sessions/{id}/ideas` — list ideas for a session
- [x] `POST /sessions/{id}/analyse` — runs Claude AI analysis (synchronous, decision 5A)
- [x] `GET /sessions/{id}/analysis` — fetch stored results (**decision 4A**)
- [x] `GET /sessions/{id}/report` — returns PDF download

### Step 4 — Config and env vars
- [x] `pydantic-settings` for typed config
- [x] Env vars: `CLAUDE_API_KEY`, `DATABASE_URL`, `FIREBASE_CREDENTIALS_PATH`
- [x] Auth model decided: participant joins by name only (no accounts), facilitator session via access code

### Step 5 — Architecture decision (LOCKED)
- [x] **Decision: Hybrid** — PostgreSQL (Supabase) for structured session/analysis data, Firebase Firestore for real-time idea sync
- [x] Why hybrid (agreed with Mohand after discussion):
  - Firestore is great for real-time (ideas, votes, live updates)
  - PostgreSQL is better for complex queries, analysis results, PDF generation
  - Firestore charges per read/write — gets expensive for dashboard reloads
  - PostgreSQL is fixed cost
- [x] Documented in `docs/project-final.md` (final agreed spec)
- [x] Confirmed with Mohand

### Step 6 — Evaluation dataset v1 (CRITICAL — DO NOT DEFER)
- [x] Create `eval/test_inputs.json` with 12 example workshop inputs (90 ideas total)
- [x] Each input has: workshop topic, list of participant ideas, expected SWOT cluster for each idea
- [x] Mix clear inputs with intentionally vague/short ones (eval-012: single-word inputs, the failure mode)
- [x] Write `eval/run_eval.py` — loads the dataset, runs clustering, prints per-case and overall accuracy
- [x] Pipeline runs end-to-end in mock mode (29% baseline — the floor). Live mode with `--live` flag.
- [x] **BART-large-MNLI runner** (`--bart` flag) — zero-shot comparison model, free and local
- [x] **Baseline accuracy comparison:**
  - Mock (everything → strengths): 28.9%
  - BART-large-MNLI (zero-shot, no context): 68.9%
  - Claude Sonnet (reasoning with context): 97.8%

> **Why it matters:** This is the single biggest difference between "I used an LLM in a project" and "I evaluated an LLM in a project." Recruiters care about the latter. You'll also catch prompt regressions in seconds instead of finding them post-demo.

### Phase 1 success criteria
- [x] API responds to `POST /sessions` and `POST /sessions/{id}/ideas`
- [ ] Mohand can hit your dev API from his Flutter app (smoke test — not full integration yet)
- [x] Eval script runs end-to-end against a mocked clustering function
- [x] Architecture decision documented and agreed

---

## Phase 2: Core Features (Weeks 5–6)

**Goal:** End-to-end AI loop working — participant idea in, structured output, PDF generated. Eval dataset is the measuring stick. Framework system is now pluggable, not hardcoded.

### Step 7 — Claude integration
- [x] `services/claude_service.py` — wraps Anthropic SDK
- [x] Structured output: prompt enforces JSON matching Pydantic schema
- [x] **Refactor:** prompt is now built dynamically from `FrameworkConfig` (see Step 9b)
- [x] **Retry-on-parse-failure:** if Claude returns malformed JSON, retry once with a corrective system prompt before giving up
- [ ] Logging: every Claude call logs prompt version, framework ID, token count, latency

### Step 8 — Prompt design (framework-aware)
- [x] System prompt for clustering (SWOT) — in `services/claude_service.py`
- [x] **Refactor:** single prompt template with `{categories}` and `{descriptions}` placeholders, filled at runtime from `FrameworkConfig`
- [ ] System prompt version-controlled in `prompts/clustering_v1.md`
- [x] Prompt enforces the provenance requirement: output must reference original idea IDs
- [x] Prompt includes category descriptions, not just names (Christian's "beskrivning av innehållet")
- [ ] Prompts include 1–2 few-shot examples of good output (one SWOT, one PESTEL)

### Step 9 — Wire up analysis route
- [x] `POST /sessions/{id}/analyse` reads ideas, calls Claude, returns structured analysis
- [x] Save the analysis result against the session
- [x] Pass `session.framework` and `session.custom_categories` through to `analyse_ideas()`
- [ ] Run `eval/run_eval.py` after every prompt change — track accuracy in `eval/results_log.md`

### Step 9b — Pluggable framework system (Christian's feedback)

**What:** Replace SWOT-hardcoding with a `FrameworkConfig` registry. SWOT, PESTEL, and custom frameworks all flow through the same code path.

**Files to change:**

| File | Action | What |
|------|--------|------|
| `app/frameworks.py` | NEW | `Category`, `Axis`, `FrameworkConfig` models, registry, prompt builder, `get_framework()` |
| `app/models/analysis.py` | MODIFY | `categories: dict[str, list[ClusteredIdea]]` instead of hardcoded SWOT fields |
| `app/models/session.py` | MODIFY | Validator for `framework` + `custom_categories`. Accept `list[str]` (backward compat) or `list[Category]` (richer) |
| `app/services/claude_service.py` | MODIFY | Delete hardcoded SWOT prompt, use `frameworks.build_system_prompt()` |
| `app/services/pdf_service.py` | MODIFY | Replace `_build_swot_grid` with `_build_category_grid`. Cycle through 8-colour palette. Use `Axis` metadata if present (else dynamic grid: 2 cols for ≤4, 3 cols for 5+) |
| `app/routes/analysis.py` | MODIFY | Pass `session.custom_categories` through to the analysis call |
| `eval/run_eval.py` | MODIFY | Dynamic category flattening |
| `eval/test_inputs.json` | MODIFY | Add PESTEL test cases (Step 18 covers expansion) |

**Models (new in `frameworks.py`):**

```python
class Category(BaseModel):
    id: str           # "S", "P_political", etc. Short stable ID.
    name: str         # "Strengths"
    description: str  # "Internal positive factors the organisation can leverage"

class Axis(BaseModel):  # Optional, for matrix-form PDF rendering later
    label: str         # "Source"
    values: list[str]  # ["Internal", "External"]

class FrameworkConfig(BaseModel):
    id: str                                # "swot"
    name: str                              # "SWOT Analysis"
    description: str                       # Short description for the prompt context
    categories: list[Category]
    axes: dict[str, Axis] | None = None    # Optional. PDF falls back to grid if None.
```

**Built-in registry (initial):**
- `swot` — 4 categories, placeholder descriptions (refine when Christian's examples arrive)
- `pestel` — 6 categories, placeholder descriptions (same)
- `custom` — built at runtime from `custom_categories` passed at session creation

**Implementation order:**
- [x] Create `frameworks.py` with models and registry. No dependencies, new file.
- [x] Update `models/analysis.py` to use generic dict. Existing tests pass because they already use plain dicts.
- [x] Add validator to `models/session.py` supporting both `list[str]` and `list[Category]`
- [x] Refactor `claude_service.py`: delete hardcoded SWOT prompt, inject category descriptions
- [x] One-line change in `routes/analysis.py` to pass through `custom_categories`
- [x] Refactor `pdf_service.py`: generic `_build_category_grid`
- [x] Update eval: dynamic category flattening
- [x] Run all 30 existing tests — they must pass unchanged

**Verification:**
- [x] `pytest tests/ -v` — all 30 existing tests pass
- [x] `python eval/run_eval.py` — mock mode works
- [x] `python eval/run_eval.py --live` — SWOT cases still score ~97%
- [x] Create session with `framework: "pestel"`, run analysis, download PDF
- [x] Create session with `framework: "custom"` and 5 user categories, run analysis, download PDF

> **Why it matters:** This is the schema-driven LLM output pattern that production systems (Instructor, LangChain, OpenAI structured outputs) all use. Worth namechecking in interviews — "the framework registry is data-driven; adding a new clustering framework requires adding a JSON config, not writing code."

### Step 10 — Firestore service (decision 9B)
- [ ] `services/firestore_service.py` — reads ideas from Firebase Firestore
- [ ] Uses `firebase-admin` SDK with service account credentials from `FIREBASE_CREDENTIALS_PATH`
- [ ] Method: `get_ideas_from_firestore(session_id)` — returns list of idea dicts
- [ ] Update `POST /sessions/{id}/analyse` to read from Firestore instead of PostgreSQL for idea data
- [ ] Keep `GET /sessions/{id}/ideas` reading from PostgreSQL (backend testing endpoint)
- [ ] Add `firebase-admin` to `requirements.txt`
- [ ] Test with real Firestore credentials
- [ ] Firestore structure the service reads from (per agreed spec):
  ```
  sessions/{session_id}/ideas/{idea_id}
    ├── participant_id: string
    ├── participant_name: string
    ├── category: string (optional)
    ├── content: string
    ├── votes: number
    └── created_at: timestamp
  ```

> **Why it matters:** This is the core of the hybrid architecture. Flutter writes ideas to Firestore in real-time during the workshop. The backend reads them from Firestore when analysis is triggered. PostgreSQL stores sessions, analysis results, and reports. Both databases do what they're best at.

### Step 10b — Analysis service (from repo structure in spec)
- [ ] `services/analysis_service.py` — orchestration layer for the analysis pipeline
- [ ] Coordinates: read ideas (Firestore) → resolve framework (frameworks.py) → call Claude → parse result → store (PostgreSQL)
- [ ] Keeps the analysis route thin — route calls the service, service does the work
- [ ] Matches the repo structure agreed in `docs/project-final.md`

### Step 11 — PDF generation (framework-aware)
- [x] `services/pdf_service.py` — takes analysis result, produces consultant-ready PDF
- [x] Template: cover page, SWOT 2x2 grid, key themes, decisions, questions, next steps, header/footer
- [x] **Refactor:** `_build_category_grid` replaces `_build_swot_grid`. Reads category list from analysis result dynamically, 8-colour palette, 2/3 column grid. (See Step 9b.)
- [ ] Provenance visible in PDF: every clustered idea shows the participant's name in brackets
- [ ] Performance target: generation completes in <10s for a typical session
- [ ] **Deferred to future dev:** matrix-form PDF layout using `Axis` metadata

### Step 12 — Report route
- [x] `GET /sessions/{id}/report` — returns PDF stream
- [ ] PDF cached so repeated calls don't re-generate (cache invalidates if analysis updates)

### Step 13 — Smoke integration with Mohand
- [ ] Mohand's Flutter app can: create a session, submit ideas, trigger analysis, download PDF
- [x] **API contract locked** in `docs/project-final.md` (final agreed version)
- [ ] Any breaking changes after this point require explicit agreement — no silent renames
- [ ] Verify Flutter sends `framework` field when creating a session (decision 11)

### Step 14 — Basic Dockerfile
- [ ] `Dockerfile` builds and runs the API locally in a container
- [ ] `docker-compose.yml` if using PostgreSQL (Postgres + API in one command)
- [ ] Document the local Docker workflow in README

> **Why it matters:** Doing Docker now (when dependencies are minimal) is 10x easier than doing it in Week 11. You'll thank yourself.

### Phase 2 success criteria
- [x] Full happy-path loop works: create session → submit ideas → trigger AI → download PDF
- [x] Pluggable framework system shipped — SWOT and PESTEL both run through the same code path
- [x] Eval accuracy ≥50% on the test dataset including PESTEL cases (SWOT 97.8%, PESTEL 80.0%, overall 94.3%)
- [ ] Mohand's Flutter app successfully calls the live AI route end-to-end at least once
- [ ] Container builds and runs locally

---

## Phase 3: Production Readiness (Weeks 7–8)

**Goal:** Move from "works on my machine for the happy path" to "handles real-world inputs and failures gracefully."

> See `production-readiness.md` for the full demo-grade vs prod-grade tagging. The items below are the ones that block Phase 3 specifically.

### Step 15 — Persistent storage
- [x] Implement chosen architecture from Phase 1 Step 5
- [x] Migration from in-memory dicts to actual DB (Supabase PostgreSQL)
- [x] SQLAlchemy ORM models for sessions, participants, ideas, analyses
- [x] UTC datetimes across all DB models (`datetime.now(timezone.utc)`)
- [x] Access code with unique constraint and collision guard
- [ ] Connection pooling, proper async handling
- [ ] Alembic migrations from now on (no manual schema changes)
- [ ] Backup/restore strategy documented (Supabase handles backups, note retention)

### Step 16 — Error handling and input validation
- [x] Input validation: name required, content min/max length, access code format
- [x] Consistent JSON error responses (`{"detail": "message"}` with HTTP status codes)
- [ ] Custom exception classes (`SessionNotFoundError`, `ClaudeAPIError`, `RateLimitError`, `FrameworkNotFoundError`)
- [ ] Global exception handler
- [ ] Input sanitisation: max ideas per session, max sessions per facilitator
- [ ] Edge cases tested: empty session, single idea, ideas in mixed languages, very long ideas
- [ ] Framework validation: unknown framework ID returns 422, custom needs at least 2 categories

### Step 17 — Rate limiting and cost protection
- [ ] Rate limit `POST /sessions/{id}/analyse` (max 3 calls per session, max 100 calls per IP per hour)
- [ ] Daily token budget cap with logged warnings before hitting it
- [ ] Document estimated cost per session in README
- [ ] Idempotency on `/analyse` — same idea-set hash returns cached result, don't re-bill

### Step 18 — Evaluation dataset v2
- [ ] Expand to 30+ examples
- [x] **Add 3 PESTEL test cases** (done in Step 9b — 32 ideas across healthcare, EV, fintech)
- [ ] **Add 2+ custom-framework test cases** using Christian's example material (once it arrives)
- [ ] Add edge cases discovered during integration testing
- [ ] Categorise by difficulty (clear / ambiguous / adversarial)
- [ ] Per-framework, per-category accuracy tracked separately in `eval/results_log.md`

### Step 19 — Prompt tuning
- [ ] Iterate on prompts using eval dataset as ground truth
- [ ] **Target: ≥80% accuracy on each framework (SWOT, PESTEL, custom)**
- [ ] Each prompt iteration: what changed, why, accuracy delta — logged in `prompts/CHANGELOG.md`
- [ ] Tune category descriptions against real Ortelius workshop examples (when Christian sends them)

> **Why it matters:** This is the substantive AI engineering work. The accuracy graph from prompt v1 to vN, with a written rationale for each change, is portfolio gold. Most candidates can't show this. With multiple frameworks tracked separately, you can also show how the same prompt architecture generalises across different category structures.

### Phase 3 success criteria
- [ ] AI clustering accuracy ≥80% on SWOT and PESTEL eval datasets
- [ ] API handles malformed requests, empty sessions, and Claude API failures without crashing
- [ ] One full session round-trip stays under the planning-doc target (<30s from analysis trigger to PDF available)

---

## Phase 4: Testing & Polish (Weeks 9–10)

**Goal:** Catch the bugs you don't know about yet. Real users finding real issues beats synthetic tests every time.

### Step 20 — Backend tests
- [ ] Unit tests: routes (using FastAPI `TestClient`), services, models
- [ ] **New:** unit tests for `frameworks.py` — registry lookups, custom framework construction, prompt builder
- [ ] Mock Claude API for fast, deterministic tests (don't burn tokens on every test run)
- [ ] Coverage target: ≥70% on `app/` (not chasing 100% — chasing meaningful coverage)
- [ ] CI: GitHub Actions running tests on every push

### Step 21 — Full integration testing
- [ ] End-to-end tests with Mohand's Flutter app
- [ ] Multi-participant scenarios (5+ concurrent ideas, real-time sync stress)
- [ ] Real-time sync edge cases (participant joins mid-analysis)
- [ ] PDF rendering across different session sizes (3 ideas vs 50 ideas)
- [ ] PDF rendering across all supported frameworks (SWOT, PESTEL, custom with 3/5/7 categories)

### Step 22 — User testing with Ortelius consultants
- [ ] At least one consultant runs a real workshop session through the tool
- [ ] Consultant tries at least one custom framework (their own categories, their own descriptions)
- [ ] Capture feedback structured by: what worked, what broke, what was confusing
- [ ] Triage feedback: **must-fix** (this week), **nice-to-have** (future-development list)

### Step 23 — Bug fixes and polish
- [ ] Address must-fix items from user testing
- [ ] Performance check: full session under planning-doc success criteria
- [ ] Final pass on error messages — humans should understand them

### Phase 4 success criteria
- [ ] At least one Ortelius consultant confirms the prototype reflects a real workflow
- [ ] Consultant validates the custom framework flow works for at least one real Ortelius use case
- [ ] All planning-doc success criteria met
- [ ] Test suite passes in CI

---

## Phase 5: Final Delivery (Weeks 11–12)

**Goal:** Demo-ready, documented, deployable. Future-proofed for whoever picks this up.

### Step 24 — Cloud deployment
- [ ] Deploy existing Docker image to Render / Railway / Azure
- [ ] Environment variables configured in cloud
- [ ] HTTPS, custom domain if applicable
- [ ] Smoke test the production URL with Mohand's app

### Step 25 — Documentation
- [ ] `README.md` — what it is, how to run it locally, how to deploy
- [ ] `docs/architecture.md` — system diagram, key decisions, trade-offs
- [ ] `docs/api_reference.md` — endpoints, request/response examples
- [ ] `docs/prompt_design.md` — how the AI layer works, why these prompts
- [ ] **`docs/frameworks.md`** — how to add a new framework (config-only, no code)
- [ ] `docs/evaluation.md` — how the eval dataset works, accuracy results, methodology, per-framework breakdown
- [ ] `docs/future_development.md` — what wasn't built, what would be next, what's brittle (incl. matrix-form PDF layout)

### Step 26 — Demo prep
- [ ] Demo script (3–5 min walkthrough)
- [ ] Show at least two frameworks in the demo (SWOT + custom, or SWOT + PESTEL)
- [ ] Recorded demo video for portfolio use
- [ ] Slide deck for final presentation

### Step 27 — Recommendations for further development
- [ ] Honest assessment: what works, what's brittle, what's missing
- [ ] Concrete next steps Ortelius could take
- [ ] Cost analysis: estimated monthly run cost at projected usage
- [ ] Specifically: a UI for consultants to manage framework templates (currently they pass JSON)

### Phase 5 success criteria
- [ ] Live URL works
- [ ] Repository is documented well enough that another developer could pick it up cold
- [ ] Final presentation delivered

---

## Cross-cutting checklist

These aren't tied to a single phase — they should be true throughout:

- [ ] Git commits are atomic, meaningful, and tagged to issues/tasks
- [ ] Every PR has a description of what changed and why
- [x] Secrets never committed (use `.env.example` for templates)
- [ ] Weekly status report references the current phase and step
- [ ] **Friday end-of-week ritual:** tick completed items here, log eval accuracy, push to repo

---

## Key portfolio artifacts produced

By the end of the project, this repo should contain:

1. **Eval framework** — measurable AI quality work (rare among junior candidates)
2. **Prompt CHANGELOG** — iteration history with accuracy data
3. **Pluggable framework registry** — schema-driven LLM output, production pattern
4. **API documentation** — proves you can design a clean contract
5. **Architecture doc** — proves you can make and justify decisions
6. **Demo video** — for portfolio
7. **Passing CI** — proves you ship tested code

These are the concrete things to point at in interviews when asked "tell me about an AI project you've built."

---

## Changes from the original plan

| Original | Updated | Why |
|---|---|---|
| Eval dataset in Week 7–8 | **Week 3–4** | Can't tune what you can't measure. Build the ruler first. |
| Integration testing in Week 9–10 | **Smoke integration in Week 5–6** + full in Week 9–10 | Locks API contract early; avoids 4 weeks of accumulated mismatches. |
| Docker in Week 11 | **Basic Dockerfile in Week 5–6** | Easier when deps are minimal; deployment in Week 11 becomes trivial. |
| Error handling in Week 7–8 only | **Baked in from Week 3** | Cheaper to do incrementally than retrofit. |
| Provenance + JSON validation not listed | **Added to Step 2 and Step 7** | Both are Ortelius governance + reliability requirements. |
| CORS, `/health`, auth model not listed | **Added to Phase 1** | Cheap upfront, expensive if forgotten. |
| Join returns full session | **Returns participant_id only (decision 2B)** | Lighter response, Mohand agreed. |
| No access codes | **Added access codes + join by code (decision 3A)** | Polished for demo — facilitator shares a short code. |
| No GET analysis endpoint | **Added GET /sessions/{id}/analysis (decision 4A)** | Facilitator can refresh without re-running Claude. |
| No category field on ideas | **Added optional category (decision 6B)** | Participants can pre-tag, AI categorises everything regardless. |
| No participant_name on ideas | **Added participant_name** | Provenance — PDF shows who said what. |
| Shared get_db() duplicated | **Moved to app/dependencies.py** | DRY — one copy, all routes use it. |
| No firestore_service.py | **Added Step 10 (decision 9B)** | Service layer for reading ideas from Firestore during analysis. |
| datetime.now (naive) | **UTC datetimes across all DB models** | Consistent timezone handling for multi-region workshops. |
| SWOT hardcoded everywhere | **Pluggable `FrameworkConfig` registry (Step 9b)** | Christian's feedback (21 May) — any matrix-form template should work, not just SWOT. |
| Categories were string labels | **Categories now have `id`, `name`, `description`** | Christian's "beskrivning av innehållet" — descriptions give Claude clearer context, also enables custom frameworks the facilitator can fully define. |
| PESTEL not supported | **Built-in PESTEL config + eval test cases** | Same code path as SWOT once framework system lands. |
| Custom frameworks not supported | **`framework: "custom"` + `custom_categories` flow** | Any Ortelius client framework can be plugged in without code changes. |
| Matrix-form PDF layout | **Optional `Axis` metadata in `FrameworkConfig`, rendering deferred to future dev** | Christian flagged "matrisform" but the structure is enough for prototype. |
