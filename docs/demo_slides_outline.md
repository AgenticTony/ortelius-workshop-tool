# Demo Slides — Outline

Slide-by-slide outline for the final presentation. Produce the actual deck (Keynote / PowerPoint / Google Slides) from this — the content + order is what matters. Aim for ~10–12 slides for a 10-minute talk (5 min demo + 5 min context/Q&A).

## Slide 1 — Title
- **Workshop Support Tool**
- Ortelius Internship — Project 5
- Your name, date

## Slide 2 — The problem
- Consultants run workshops → capture dozens of ideas → manually sort into SWOT/PESTEL → hours of post-work
- "What if this took seconds, not hours?"

## Slide 3 — What it does (the 30-second pitch)
- Participants submit ideas live from their phone
- AI clusters them into any framework (SWOT, PESTEL, or custom)
- Consultant-ready PDF generated instantly
- *Screenshot: the facilitator dashboard with live ideas*

## Slide 4 — Architecture
- The system diagram from [`architecture.md`](architecture.md)
- Flutter frontend ↔ FastAPI backend ↔ PostgreSQL + Claude
- SSE for real-time (not Firestore — explain the decision)
- *One clean diagram, not a wall of text*

## Slide 5 — The pluggable framework system
- "Adding a framework is config, not code"
- The `FrameworkConfig` registry: SWOT, PESTEL, custom
- Christian's feedback: *"beskrivning av innehållet"* — category descriptions drive accuracy
- *Code snippet: defining a custom framework in ~10 lines*

## Slide 6 — The AI layer
- Framework-aware prompt (category names + descriptions injected)
- Structured JSON output (schema-driven)
- Retry on bad JSON; Claude outage → clean 503
- Versioned prompt + per-call logging (tokens, latency)
- *Link to [`prompt_design.md`](prompt_design.md)*

## Slide 7 — Evaluation (the "I evaluated an LLM" slide)
- The eval framework: mock / BART / live modes
- **The accuracy table:**
  - SWOT: 96.7%
  - PESTEL: 81.2%
  - Custom: **100%**
- The comparison: mock 20% → BART 69% → Claude 93%
- *This is the slide that differentiates from "I just used an LLM"*

## Slide 8 — Live demo
- *Run the demo from [`demo_script.md`](demo_script.md)*
- SWOT session → live ideas → analysis → PDF
- Then custom framework → "100% accuracy, our own categories"

## Slide 9 — Real-time engineering
- SSE over the existing backend (dropped Firestore)
- Auto-reconnect on drop
- Mobile-buffering fix (the `no-transform` discovery)
- *Brief — this shows engineering depth, not a feature list*

## Slide 10 — Production readiness
- Docker + docker-compose (one command up)
- Alembic migrations
- Typed errors + global handler (no stack-trace leaks)
- CI: GitHub Actions (pytest + ruff + flutter analyze) — green on every PR
- Rate limiting + facilitator auth
- Deployed to Render: `workshop-web-1gvl.onrender.com`

## Slide 11 — What's next
- The prioritized list from [`future_development.md`](future_development.md):
  - Multi-worker SSE (Postgres LISTEN/NOTIFY)
  - Vote dedup
  - Framework-editor UI (consultants author descriptions)
  - Few-shot prompt (v2) for PESTEL
- Cost: ~$8/mo at 100 workshops

## Slide 12 — Thank you / Q&A
- Repo link
- Live demo URL
- Contact

## Production tips
- **~1 minute per slide** max — the demo (slide 8) is the longest section.
- **Don't read the slides** — talk to the architecture/eval, let the demo speak for itself.
- **Have the eval numbers memorized** (96.7 / 81.2 / 100) — they're the most-asked-about.
- **Practice the demo twice** — the live-submit-to-analysis flow is the wow moment; don't fumble it.
