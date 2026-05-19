# API Contract

Backend ↔ Frontend integration boundary.

## Endpoints

### Sessions

| Method | Path | Description |
|--------|------|-------------|
| POST | `/sessions` | Create a new workshop session |
| GET | `/sessions/{session_id}` | Get session details |
| POST | `/sessions/{session_id}/join` | Participant joins session |

### Ideas

| Method | Path | Description |
|--------|------|-------------|
| POST | `/sessions/{session_id}/ideas` | Submit an idea |
| GET | `/sessions/{session_id}/ideas` | List all ideas in session |

### Analysis

| Method | Path | Description |
|--------|------|-------------|
| POST | `/sessions/{session_id}/analyse` | Run AI clustering + summarisation |
| GET | `/sessions/{session_id}/report` | Download generated PDF |

## Core Data Models

### Session

```json
{
  "id": "uuid",
  "topic": "string",
  "framework": "swot | pestel | custom",
  "custom_categories": ["string"],
  "status": "active | closed | analysed",
  "created_at": "ISO 8601",
  "participants": [{"id": "uuid", "name": "string"}]
}
```

### Idea

```json
{
  "id": "uuid",
  "session_id": "uuid",
  "participant_id": "uuid",
  "content": "string",
  "votes": 0,
  "created_at": "ISO 8601"
}
```

### Analysis Result

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

## Notes

- Real-time idea sync uses Firebase Firestore — these REST endpoints are for AI analysis and session management only
- All AI responses return structured JSON for auditability
- Every clustered idea references the original participant (provenance)
