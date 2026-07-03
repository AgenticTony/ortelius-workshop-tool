# Ortelius Workshop Tool — Project Spec

**Final agreed version — Anthony (Backend) + Mohand (Frontend)**

> ⚠️ **PARTIALLY SUPERSEDED (July 2026) — read this note first.**
>
> The sections below that mention **Firebase Firestore, Firebase Auth, Firebase Hosting, `firestore_service.py`, and a "hybrid" Firestore+PostgreSQL architecture are obsolete.** Firestore was never built; the backend reads ideas from PostgreSQL. The original frontend owner (Mohand) has left; Anthony now owns both layers.
>
> The **current, authoritative** reality is:
> - **Single database (PostgreSQL/Supabase).** No Firebase.
> - **Real-time via SSE** (`GET /sessions/{id}/ideas/stream`), not Firestore.
> - **Ideas + voting** are REST endpoints (`POST /ideas`, `POST /ideas/{id}/vote`), not Firestore writes.
> - **Facilitator auth** is a bearer token issued at session creation.
>
> For the live contract, see **`docs/api-contract.md`** (updated). For frontend progress, see **`docs/frontend-roadmap.md`**. For backend progress, see **`docs/backend-roadmap.md`**. The remainder of this document is preserved as the original agreed scope; treat the Firebase-specific parts as historical context only.

---

## What we're building

A workshop facilitation tool where a consultant runs a session, participants submit ideas live, AI clusters and summarises them, and a PDF report is generated. Built for Ortelius consultants to use in real workshops.

## The flow

1. Facilitator creates a session (picks topic + framework)
2. Participants join with just a name (no accounts)
3. Participants submit ideas in real-time
4. Facilitator triggers AI analysis
5. Claude groups ideas into SWOT/PESTEL categories
6. PDF report is generated for download

---

## Architecture

```
Flutter app ──realtime──> Firebase Firestore (ideas, votes)
Flutter app ──REST──────> FastAPI backend (sessions, analysis, PDF)
FastAPI backend ──reads─────> Firebase Firestore (ideas for analysis)
FastAPI backend ──calls─────> Claude API (clustering + summarisation)
FastAPI backend ──stores────> PostgreSQL / Supabase (sessions, analysis, reports)
```

**Why hybrid (Firestore + PostgreSQL):**
- Firestore handles real-time — ideas, votes, live updates during the workshop
- PostgreSQL handles persistence — sessions, analysis results, PDF reports, structured queries
- Firestore charges per read/write, PostgreSQL is fixed cost. Running analysis queries through Firestore gets expensive fast.

---

## Responsibilities

| Layer | What it does |
|-------|-------------|
| Flutter | UI, real-time idea sync, voting, QR code generation |
| Firebase Firestore | Live workshop data (ideas, votes, participants) |
| Firebase Auth | Anonymous auth — participants don't create accounts |
| FastAPI | Session management, AI analysis, PDF generation |
| Claude API | Idea clustering + summarisation |
| PostgreSQL (Supabase) | Sessions, analysis results, reports |
| ReportLab | PDF generation |

---

## Tech stack

| Area | Choice |
|------|--------|
| Frontend | Flutter (web + mobile) |
| State management | Riverpod |
| Real-time database | Firebase Firestore |
| Backend | FastAPI (Python) |
| AI | Anthropic Claude API |
| PDF | ReportLab |
| Auth | Firebase Anonymous Auth |
| Persistence | PostgreSQL (Supabase) |
| Hosting | Firebase Hosting + Render/Railway (or Azure) |

---

## API endpoints

### Sessions

| Method | Path | What it does | Why |
|--------|------|-------------|-----|
| POST | `/sessions` | Creates a workshop session | Facilitator starts a workshop |
| GET | `/sessions/{id}` | Gets session details | Facilitator dashboard |
| POST | `/sessions/{id}/join?name=Anna` | Participant joins with name | No accounts needed |
| POST | `/sessions/join/{access_code}?name=Anna` | Join via access code | No need to share session ID |

### Ideas

| Method | Path | What it does | Why |
|--------|------|-------------|-----|
| POST | `/sessions/{id}/ideas` | Submit an idea (testing only) | Backend testing without Flutter |
| GET | `/sessions/{id}/ideas` | List all ideas | Backend reads before sending to Claude |

**Production:** Flutter writes ideas directly to Firestore. The POST endpoint is for backend testing.

### Analysis

| Method | Path | What it does | Why |
|--------|------|-------------|-----|
| POST | `/sessions/{id}/analyse` | Runs AI analysis (sync) | Reads ideas → Claude → returns result |
| GET | `/sessions/{id}/analysis` | Fetches stored analysis | Facilitator can refresh without re-running |
| GET | `/sessions/{id}/report` | Downloads PDF | Consultant-ready report |

### Utility

| Method | Path | What it does |
|--------|------|-------------|
| GET | `/health` | Confirms backend is running |
| GET | `/docs` | Swagger UI — test everything in browser |

---

## Data models

### Session

```json
{
  "id": "uuid",
  "topic": "Improve onboarding",
  "framework": "swot",
  "access_code": "ABCD12",
  "status": "active",
  "created_at": "ISO 8601"
}
```

### Participant

```json
{
  "id": "uuid",
  "name": "Anna",
  "joined_at": "ISO 8601"
}
```

### Idea

```json
{
  "id": "uuid",
  "session_id": "uuid",
  "participant_id": "uuid",
  "participant_name": "Anna",
  "category": "strength",
  "content": "Better documentation for new hires",
  "votes": 3,
  "created_at": "ISO 8601"
}
```

`category` is optional — participants can pre-tag ideas if they want, but AI will categorise everything during analysis regardless.

### Analysis Result

```json
{
  "session_id": "uuid",
  "framework": "swot",
  "categories": {
    "strengths": [{ "idea_id": "uuid", "summary": "string" }],
    "weaknesses": [{ "idea_id": "uuid", "summary": "string" }],
    "opportunities": [{ "idea_id": "uuid", "summary": "string" }],
    "threats": [{ "idea_id": "uuid", "summary": "string" }]
  },
  "key_themes": ["string"],
  "decisions_made": ["string"],
  "open_questions": ["string"],
  "recommended_next_steps": ["string"]
}
```

Every clustered idea references the original `idea_id` — this is a provenance requirement from Ortelius. The PDF shows who said what.

---

## Firebase Firestore structure

```
sessions/{session_id}/
  ├── topic: string
  ├── framework: string
  ├── status: string
  └── participants: array

sessions/{session_id}/ideas/{idea_id}
  ├── participant_id: string
  ├── participant_name: string
  ├── category: string (optional)
  ├── content: string
  ├── votes: number
  └── created_at: timestamp
```

**Firestore security rules:**
- Users can only edit their own ideas
- Authenticated anonymous users only
- Analysis writable only by backend

---

## What Flutter calls

```
Flutter → POST /sessions              (create workshop)
Flutter → POST /sessions/{id}/join    (participant joins)
Flutter → Firestore                   (real-time idea input + voting)
Flutter → POST /sessions/{id}/analyse (trigger AI)
Flutter → GET /sessions/{id}/analysis (fetch results)
Flutter → GET /sessions/{id}/report   (download PDF)
```

Flutter generates QR codes locally — it's just encoding a URL, no backend needed.

---

## Repo structure

```
workshopstodverktyg/
├── backend/                  ← FastAPI (Anthony)
│   └── app/
│       ├── main.py
│       ├── config/
│       ├── models/
│       ├── routes/
│       ├── services/
│       │   ├── claude_service.py
│       │   ├── firestore_service.py
│       │   ├── pdf_service.py
│       │   └── analysis_service.py
│       └── prompts/
├── frontend_flutter/         ← Flutter (Mohand)
│   └── lib/
│       ├── main.dart
│       ├── core/
│       ├── models/
│       ├── services/
│       ├── features/
│       │   ├── session/
│       │   ├── workshop/
│       │   ├── analysis/
│       │   └── report/
│       └── widgets/
├── firebase/
├── docs/
└── README.md
```

---

## Development phases

### Phase 1 — Workshop Setup (Weeks 1–2)
- Create session
- Join session with name
- Access code generation
- QR code generation (frontend)
- Basic real-time dashboard

### Phase 2 — Realtime Workshop (Weeks 3–4)
- Submit ideas to Firestore
- Real-time dashboard updates
- Upvote ideas
- Facilitator dashboard

### Phase 3 — AI Analysis (Weeks 5–6)
- Claude integration
- SWOT/PESTEL clustering
- Structured JSON output
- Prompt design + evaluation

### Phase 4 — Reports (Weeks 7–8)
- PDF generation (ReportLab)
- Consultant-ready template
- Download flow

### Phase 5 — Testing & Polish (Weeks 9–10)
- Multi-participant testing
- Real-time sync stress tests
- Error handling
- User testing with Ortelius consultants

### Phase 6 — Delivery (Weeks 11–12)
- Cloud deployment
- Documentation
- Demo prep
- Final presentation

---

## Claude prompt strategy

Keep it simple. No agents, no LangChain, no RAG.

Example:
```
You are analysing workshop ideas.
Group the following ideas into SWOT categories.
Return ONLY valid JSON.
Ideas:
{ideas}
```

Prompt versions are tracked in `prompts/` directory. Each version logged with what changed and accuracy results.

---

## Success criteria

- Workshop setup < 2 minutes
- Mobile participation works without install
- Real-time updates feel instant
- AI groups ideas correctly (≥80% accuracy on eval dataset)
- PDF generated < 30 seconds
- Consultants can demo it

---

## Error handling

All errors return `{"detail": "error message"}` with HTTP status code:

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 404 | Session or resource not found |
| 422 | Validation error |
| 500 | Server error |

---

## Philosophy

Optimise for:
- Simplicity
- Maintainability
- Demoability
- Clear documentation

NOT for:
- Enterprise scalability
- Microservices
- Complex infrastructure

The cleanest MVP is the best MVP.
