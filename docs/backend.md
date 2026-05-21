# Backend Roadmap — Workshop Support Tool

**Project 5 — Ortelius Internship | May–August 2026**

- **Workstream:** AI & Backend
- **Stack:** Python + FastAPI, Anthropic Claude API, ReportLab, PostgreSQL (Supabase), Firebase Firestore (for real-time sync)
- **Integrates with:** Mohand's Flutter frontend (mobile + web)

---

## How to use this document

- Each phase maps to the schedule in the project planning doc
- Tick items as you complete them; keep this file updated in the repo
- Reference current week's items in your Friday weekly status reports
- **"Why it matters"** notes flag the portfolio-relevant work for interviews

---

## Phase 1: Foundation (Weeks 3–4)

**Goal:** A working FastAPI skeleton with all the architectural decisions locked in, including the evaluation dataset that will measure AI quality from day one.

### Step 1 — FastAPI skeleton
- [x] Project structure (`app/`, `tests/`, `eval/`, `docs/`, `prompts/`)
- [x] FastAPI app with `/health` endpoint
- [x] CORS middleware configured for Flutter web origin
- [x] Auto-generated OpenAPI docs available at `/docs`
- [x] `.gitignore`, `requirements.txt`, `.env.example`

### Step 2 — Pydantic models
- [x] `Session` model (id, topic, framework, status, created_at)
- [x] `Idea` model (id, session_id, participant_id, content, votes, created_at)
- [x] `AnalysisResult` model with SWOT categories, key themes, decisions, questions, next steps
- [x] Each clustered idea references the original `idea_id` (provenance traceability — Ortelius governance requirement)

### Step 3 — Routes (scaffold)
- [x] `POST /sessions` — create a session
- [x] `GET /sessions/{id}` — fetch session details
- [x] `POST /sessions/{id}/ideas` — submit an idea
- [x] `GET /sessions/{id}/ideas` — list ideas for a session
- [x] `POST /sessions/{id}/analyse` — runs Claude AI analysis
- [x] `GET /sessions/{id}/report` — returns PDF download

### Step 4 — Config and env vars
- [x] `pydantic-settings` for typed config
- [x] Env vars: `CLAUDE_API_KEY`, `DATABASE_URL`, `FIREBASE_CREDENTIALS_PATH`
- [ ] Auth model decided and documented: facilitator session token, participant joins by name only

### Step 5 — Architecture decision (LOCK BEFORE WEEK 5)
- [x] Decide: Firebase only, PostgreSQL only, or hybrid?
  - **Decision: Hybrid** — PostgreSQL (Supabase) for structured session/analysis data, Firebase for real-time idea sync
- [x] Document the decision in `docs/api-contract.md`
- [x] Confirm with Mohand — affects his Flutter integration directly

### Step 6 — Evaluation dataset v1 (CRITICAL — DO NOT DEFER)
- [ ] Create `eval/test_inputs.json` with 10–15 example workshop inputs
- [ ] Each input has: workshop topic, list of participant ideas, expected SWOT cluster for each idea
- [ ] Mix clear inputs with intentionally vague/short ones (the failure modes you need to test)
- [ ] Write `eval/run_eval.py` — loads the dataset, runs your clustering function, prints per-input and overall accuracy
- [ ] The script must run end-to-end even if accuracy is 0% on day one. Pipeline first, score later.

> **Why it matters:** This is the single biggest difference between "I used an LLM in a project" and "I evaluated an LLM in a project." Recruiters care about the latter. You'll also catch prompt regressions in seconds instead of finding them post-demo.

### Phase 1 success criteria
- [x] API responds to `POST /sessions` and `POST /sessions/{id}/ideas`
- [ ] Mohand can hit your dev API from his Flutter app (smoke test — not full integration yet)
- [ ] Eval script runs end-to-end against a mocked clustering function
- [x] Architecture decision documented and agreed

---

## Phase 2: Core Features (Weeks 5–6)

**Goal:** End-to-end AI loop working — participant idea in, structured SWOT out, PDF generated. Eval dataset is the measuring stick.

### Step 7 — Claude integration
- [x] `services/claude_service.py` — wraps Anthropic SDK
- [x] Structured output: prompt enforces JSON matching Pydantic schema
- [ ] **Retry-on-parse-failure:** if Claude returns malformed JSON, retry once with a corrective system prompt before giving up
- [ ] Logging: every Claude call logs prompt version, token count, latency

### Step 8 — Prompt design (v1)
- [x] System prompt for clustering (SWOT) — in `services/claude_service.py`
- [ ] System prompt version-controlled in `prompts/clustering_v1.md`
- [x] Prompt enforces the provenance requirement: output must reference original idea IDs
- [ ] Prompts include 1–2 few-shot examples of good output

### Step 9 — Wire up analysis route
- [x] `POST /sessions/{id}/analyse` reads ideas, calls Claude, returns structured analysis
- [x] Save the analysis result against the session
- [ ] Run `eval/run_eval.py` after every prompt change — track accuracy in `eval/results_log.md`

### Step 10 — PDF generation (ReportLab)
- [x] `services/pdf_service.py` — takes analysis result, produces consultant-ready PDF
- [x] Template: cover page, SWOT 2x2 grid, key themes, decisions, questions, next steps, header/footer
- [ ] Provenance visible in PDF: every clustered idea shows the participant's name in brackets
- [ ] Performance target: generation completes in <10s for a typical session

### Step 11 — Report route
- [x] `GET /sessions/{id}/report` — returns PDF stream
- [ ] PDF cached so repeated calls don't re-generate (cache invalidates if analysis updates)

### Step 12 — Smoke integration with Mohand
- [ ] Mohand's Flutter app can: create a session, submit ideas, trigger analysis, download PDF
- [x] **API contract locked** in `docs/api-contract.md`
- [ ] Any breaking changes after this point require explicit agreement — no silent renames

### Step 13 — Basic Dockerfile
- [ ] `Dockerfile` builds and runs the API locally in a container
- [ ] `docker-compose.yml` if using PostgreSQL (Postgres + API in one command)
- [ ] Document the local Docker workflow in README

> **Why it matters:** Doing Docker now (when dependencies are minimal) is 10× easier than doing it in Week 11. You'll thank yourself.

### Phase 2 success criteria
- [x] Full happy-path loop works: create session → submit ideas → trigger AI → download PDF
- [ ] Eval accuracy ≥50% on the test dataset (rough baseline to improve from)
- [ ] Mohand's Flutter app successfully calls the live AI route end-to-end at least once
- [ ] Container builds and runs locally

---

## Phase 3: Production Readiness (Weeks 7–8)

**Goal:** Move from "works on my machine for the happy path" to "handles real-world inputs and failures gracefully."

### Step 14 — Persistent storage
- [x] Implement chosen architecture from Phase 1 Step 5
- [x] Migration from in-memory dicts to actual DB (Supabase PostgreSQL)
- [x] SQLAlchemy ORM models for sessions, participants, ideas, analyses
- [ ] Connection pooling, proper async handling
- [ ] Backup/restore strategy documented (even if just "Firebase handles it")

### Step 15 — Error handling and input validation
- [ ] Custom exception classes (`SessionNotFoundError`, `ClaudeAPIError`, `RateLimitError`, etc.)
- [ ] Global exception handler returning consistent JSON error format
- [ ] Input sanitisation: max idea length, max ideas per session, max sessions per facilitator
- [ ] Edge cases tested: empty session, single idea, ideas in mixed languages, very long ideas

### Step 16 — Rate limiting and cost protection
- [ ] Rate limit `POST /sessions/{id}/analyse` (it's the expensive endpoint)
- [ ] Daily token budget cap with logged warnings before hitting it
- [ ] Document estimated cost per session in README

### Step 17 — Evaluation dataset v2
- [ ] Expand to 30+ examples
- [ ] Add edge cases discovered during integration testing
- [ ] Categorise by difficulty (clear / ambiguous / adversarial)
- [ ] Per-category accuracy tracked separately in `eval/results_log.md`

### Step 18 — Prompt tuning
- [ ] Iterate on prompts using eval dataset as ground truth
- [ ] **Target: ≥80% accuracy on SWOT clustering** (per planning doc success criteria)
- [ ] Each prompt iteration: what changed, why, accuracy delta — logged in `prompts/CHANGELOG.md`

> **Why it matters:** This is the substantive AI engineering work. The accuracy graph from prompt v1 → vN, with a written rationale for each change, is portfolio gold. Most candidates can't show this.

### Phase 3 success criteria
- [ ] AI clustering accuracy ≥80% on the eval dataset
- [ ] API handles malformed requests, empty sessions, and Claude API failures without crashing
- [ ] One full session round-trip stays under the planning-doc target (<30s from analysis trigger to PDF available)

---

## Phase 4: Testing & Polish (Weeks 9–10)

**Goal:** Catch the bugs you don't know about yet. Real users finding real issues beats synthetic tests every time.

### Step 19 — Backend tests
- [ ] Unit tests: routes (using FastAPI `TestClient`), services, models
- [ ] Mock Claude API for fast, deterministic tests (don't burn tokens on every test run)
- [ ] Coverage target: ≥70% on `app/` (not chasing 100% — chasing meaningful coverage)
- [ ] CI: GitHub Actions running tests on every push

### Step 20 — Full integration testing
- [ ] End-to-end tests with Mohand's Flutter app
- [ ] Multi-participant scenarios (5+ concurrent ideas, real-time sync stress)
- [ ] Real-time sync edge cases (participant joins mid-analysis)
- [ ] PDF rendering across different session sizes (3 ideas vs 50 ideas)

### Step 21 — User testing with Ortelius consultants
- [ ] At least one consultant runs a real workshop session through the tool
- [ ] Capture feedback structured by: what worked, what broke, what was confusing
- [ ] Triage feedback: **must-fix** (this week), **nice-to-have** (future-development list)

### Step 22 — Bug fixes and polish
- [ ] Address must-fix items from user testing
- [ ] Performance check: full session under planning-doc success criteria
- [ ] Final pass on error messages — humans should understand them

### Phase 4 success criteria
- [ ] At least one Ortelius consultant confirms the prototype reflects a real workflow
- [ ] All planning-doc success criteria met
- [ ] Test suite passes in CI

---

## Phase 5: Final Delivery (Weeks 11–12)

**Goal:** Demo-ready, documented, deployable. Future-proofed for whoever picks this up.

### Step 23 — Cloud deployment
- [ ] Deploy existing Docker image to Azure (or chosen cloud)
- [ ] Environment variables configured in cloud
- [ ] HTTPS, custom domain if applicable
- [ ] Smoke test the production URL with Mohand's app

### Step 24 — Documentation
- [ ] `README.md` — what it is, how to run it locally, how to deploy
- [ ] `docs/architecture.md` — system diagram, key decisions, trade-offs
- [ ] `docs/api_reference.md` — endpoints, request/response examples
- [ ] `docs/prompt_design.md` — how the AI layer works, why these prompts
- [ ] `docs/evaluation.md` — how the eval dataset works, accuracy results, methodology
- [ ] `docs/future_development.md` — what wasn't built, what would be next, what's brittle

### Step 25 — Demo prep
- [ ] Demo script (3–5 min walkthrough)
- [ ] Recorded demo video for portfolio use
- [ ] Slide deck for final presentation

### Step 26 — Recommendations for further development
- [ ] Honest assessment: what works, what's brittle, what's missing
- [ ] Concrete next steps Ortelius could take
- [ ] Cost analysis: estimated monthly run cost at projected usage

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
3. **API documentation** — proves you can design a clean contract
4. **Architecture doc** — proves you can make and justify decisions
5. **Demo video** — for portfolio
6. **Passing CI** — proves you ship tested code

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
