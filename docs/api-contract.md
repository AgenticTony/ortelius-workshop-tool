# API Contract

## Vad detta dokument är

Detta är avtalet mellan backend (Python/FastAPI) och frontend (Flutter) om hur de två delarna kommunicerar med varandra. Det definierar vilka slutpunkter som finns, vilken data som ska in och vilken data som ska ut.

Vi båda bygger mot detta dokument. Om vi ​​båda följer det kommer vår kod att fungera tillsammans utan att vi behöver testa integrationen förrän senare.

## Vad vi behöver komma överens om

Innan vi börjar bygga, läs igenom detta och bekräfta att du är nöjd med:

1. **Slutpunkterna** — är dessa rätt? Saknas något? Behöver du något inte?

2. **Dataformerna** — JSON-strukturerna för Session, Idea och AnalysisResult. Kan du arbeta med dessa i Flutter?

3. **Firebase-strukturen** — hur idéer lagras i Firestore. Det här är vad du kommer att skriva till och vad jag kommer att läsa från.

4. **Ansvarsfördelning:**
- Frontend hanterar idéinmatning, omröstning och realtidsvy
- Backend hanterar sessionsskapande, AI-analys och PDF-generering via API:et
- Frontend anropar backend för att: skapa sessioner, gå med i sessioner, skicka idéer, rösta, prenumerera på realtidsuppdateringar, utlösa analyser och ladda ner PDF:en

Om något inte fungerar för din sida kan vi ändra det innan någon av oss skriver kod mot det.

## Architecture Overview

```
Flutter frontend ──REST──────> FastAPI backend (sessions, ideas, votes, analysis, PDF)
Flutter frontend ──SSE───────> FastAPI backend (live idea/vote/participant stream)
FastAPI backend  ──stores───> PostgreSQL / Supabase (everything)
FastAPI backend  ──calls─────> Claude API (clustering + summarisation)
```

Real-time updates are delivered via a Server-Sent Events (SSE) stream from the backend. AI analysis and PDF generation also go through the FastAPI backend.

> **Note (July 2026):** The original design used Firebase Firestore for real-time idea sync. Firestore was never built, and the backend already reads ideas from PostgreSQL. We have dropped Firestore entirely and replaced its real-time role with SSE. The architecture is now a single database (PostgreSQL) and a single backend.

## Authentication: facilitator token

`POST /sessions` issues a one-time **facilitator token** in the response body (`facilitator_token`). The frontend must store it securely and send it as `Authorization: Bearer <token>` on the protected routes below. It is never re-served by any other endpoint.

| Route | Auth required |
|-------|---------------|
| `POST /sessions/{id}/analyse` | Yes — facilitator token |
| `GET /sessions/{id}/report` | Yes — facilitator token |
| All other routes | No |

## Endpoints

### Sessions

| Method | Path | Description |
|--------|------|-------------|
| POST | `/sessions` | Create a new workshop session (response includes one-time `facilitator_token`) |
| GET | `/sessions/{session_id}` | Get session details |
| POST | `/sessions/{session_id}/join?name=...` | Participant joins session |
| POST | `/sessions/join/{access_code}` | Join via short access code |

### Ideas

| Method | Path | Description |
|--------|------|-------------|
| POST | `/sessions/{session_id}/ideas` | Submit an idea |
| GET | `/sessions/{session_id}/ideas` | List all ideas in session |
| POST | `/sessions/{session_id}/ideas/{idea_id}/vote` | Upvote an idea (returns updated idea) |
| GET | `/sessions/{session_id}/ideas/stream` | **SSE** — live stream of `idea_added`, `idea_voted`, `participant_joined` events |

**Note:** Ideas are submitted and read via these REST endpoints; PostgreSQL is the single source of truth. (The earlier "testing only" note for POST is obsolete.)

### Analysis

| Method | Path | Description | Request Body | Response |
|--------|------|-------------|--------------|----------|
| POST | `/sessions/{session_id}/analyse` | Run AI clustering + summarisation | None — backend reads ideas from DB. **Facilitator token required.** | `AnalysisResult` JSON |
| GET | `/sessions/{session_id}/analysis` | Fetch stored analysis results (no re-run) | None | `AnalysisResult` JSON |
| GET | `/sessions/{session_id}/report` | Download generated PDF | None. **Facilitator token required.** | PDF file (binary) |

## Core Data Models

### Session

```json
{
  "id": "uuid",
  "topic": "string",
  "framework": "swot | pestel | custom",
  "custom_categories": ["string"],
  "access_code": "string (6-char, generated on creation)",
  "status": "active | closed | analysed",
  "created_at": "ISO 8601",
  "participants": [
    {
      "id": "uuid",
      "name": "string",
      "joined_at": "ISO 8601"
    }
  ],
  "facilitator_token": "string | null (only present on the POST /sessions response)"
}
```

> `facilitator_token` is returned **once**, on session creation, so the facilitator's client can store it. It is `null` on every other endpoint. Required as `Authorization: Bearer <token>` for `/analyse` and `/report`.

### Idea

```json
{
  "id": "uuid",
  "session_id": "uuid",
  "participant_id": "uuid",
  "participant_name": "string",
  "category": "string | null",
  "content": "string",
  "votes": 0,
  "created_at": "ISO 8601"
}
```

### Analysis Result

Categories are dynamic — keys match the framework's category names. Examples for SWOT and PESTEL:

```json
{
  "session_id": "uuid",
  "framework": "swot",
  "categories": {
    "strengths": [{"idea_id": "uuid", "summary": "string"}],
    "weaknesses": [{"idea_id": "uuid", "summary": "string"}],
    "opportunities": [{"idea_id": "uuid", "summary": "string"}],
    "threats": [{"idea_id": "uuid", "summary": "string"}]
  },
  "key_themes": ["string"],
  "decisions_made": ["string"],
  "open_questions": ["string"],
  "recommended_next_steps": ["string"]
}
```

For a PESTEL session, `categories` would contain keys: `political`, `economic`, `social`, `technological`, `environmental`, `legal`. For a custom framework, keys match whatever categories the facilitator defined.

## SSE Event Stream (`GET /sessions/{session_id}/ideas/stream`)

A Server-Sent Events stream. The client opens it once and receives events as they happen. Each event is sent as:

```
event: <type>
data: <json>

```

Line comments starting with `:` are heartbeats / connection confirmations — the client should ignore them. Event types:

| Event type | When | `data` payload |
|------------|------|----------------|
| `idea_added` | A participant submits an idea | the full `Idea` object |
| `idea_voted` | An idea is upvoted | `{"idea_id": str, "votes": int}` |
| `participant_joined` | A participant joins the session | `{"participant_id": str, "name": str, "participant_count": int}` |

**Limitation:** the in-memory event bus requires a single uvicorn worker. Multi-worker deployment needs Postgres `LISTEN/NOTIFY` or an external broker (deferred — see `docs/frontend-roadmap.md`).

## Rate limiting

| Route | Limit | Notes |
|-------|-------|-------|
| `POST /sessions/{id}/analyse` | 5 / minute / IP | Protects Claude cost |
| `POST /sessions/{id}/ideas` | 30 / minute / IP | Guards against idea spam |

Exceeding a limit returns `429 Too Many Requests`.

## Response Format

All JSON responses follow this structure:

- **Success:** Returns the model directly (Session, Idea, AnalysisResult)
- **Error:** Returns `{"detail": "error message"}` with appropriate HTTP status code

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 401 | Facilitator token missing or invalid (protected routes) |
| 404 | Session or resource not found |
| 422 | Validation error (missing or invalid fields) |
| 429 | Rate limit exceeded |
| 500 | Server error |

## Notes

- Real-time updates use SSE; everything is stored in PostgreSQL — there is no Firebase dependency
- All AI responses return structured JSON for auditability
- Every clustered idea references the original participant (provenance)
- PDF report endpoint returns `application/pdf` content type, not JSON
