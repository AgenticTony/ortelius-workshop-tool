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
- Du hanterar idéinmatning och omröstning i realtid via Firebase
- Jag hanterar sessionsskapande, AI-analys och PDF-generering via API:et
- Den enda gången Flutter anropar backend är för att: skapa sessioner, gå med i sessioner, utlösa analyser och ladda ner PDF:en

Om något inte fungerar för din sida kan vi ändra det innan någon av oss skriver kod mot det.

## Architecture Overview

```
Flutter frontend ──realtime──> Firebase Firestore (ideas, votes)
Flutter frontend ──REST──────> FastAPI backend (sessions, analysis, PDF)
FastAPI backend  ──reads─────> Firebase Firestore (ideas for analysis)
FastAPI backend  ──calls─────> Claude API (clustering + summarisation)
```

Real-time idea sync goes through Firebase. AI analysis and PDF generation go through the FastAPI backend.

## Endpoints

### Sessions

| Method | Path | Description |
|--------|------|-------------|
| POST | `/sessions` | Create a new workshop session |
| GET | `/sessions/{session_id}` | Get session details |
| POST | `/sessions/{session_id}/join?name=...` | Participant joins session |
| POST | `/sessions/join/{access_code}` | Join via short access code |

### Ideas

| Method | Path | Description |
|--------|------|-------------|
| POST | `/sessions/{session_id}/ideas` | Submit an idea (testing only) |
| GET | `/sessions/{session_id}/ideas` | List all ideas in session |

**Note:** In production, Flutter writes ideas directly to Firebase Firestore (see Firebase structure below). The POST endpoint exists for backend testing without the frontend.

### Analysis

| Method | Path | Description | Request Body | Response |
|--------|------|-------------|--------------|----------|
| POST | `/sessions/{session_id}/analyse` | Run AI clustering + summarisation | None — backend reads ideas from Firebase | `AnalysisResult` JSON |
| GET | `/sessions/{session_id}/analysis` | Fetch stored analysis results (no re-run) | None | `AnalysisResult` JSON |
| GET | `/sessions/{session_id}/report` | Download generated PDF | None | PDF file (binary) |

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
  ]
}
```

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

## Firebase Firestore Structure

Flutter reads and writes ideas here. Backend reads from here for AI analysis.

```
sessions/{session_id}/
  ├── topic: string
  ├── framework: string
  ├── status: string
  └── participants: array

sessions/{session_id}/ideas/{idea_id}
  ├── participant_id: string
  ├── participant_name: string
  ├── content: string
  ├── votes: number
  └── created_at: timestamp
```

**Rules:**
- `participant_name` is stored alongside `participant_id` for provenance — the PDF report needs to show who said what
- `votes` is incremented by Flutter when participants upvote
- Backend reads this collection when `POST /analyse` is called

## Response Format

All JSON responses follow this structure:

- **Success:** Returns the model directly (Session, Idea, AnalysisResult)
- **Error:** Returns `{"detail": "error message"}` with appropriate HTTP status code

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 404 | Session or resource not found |
| 422 | Validation error (missing or invalid fields) |
| 500 | Server error |

## Notes

- Real-time idea sync uses Firebase Firestore — these REST endpoints are for AI analysis and session management only
- All AI responses return structured JSON for auditability
- Every clustered idea references the original participant (provenance)
- PDF report endpoint returns `application/pdf` content type, not JSON
