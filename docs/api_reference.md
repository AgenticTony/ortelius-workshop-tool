# API Reference

The Workshop Tool backend API. Base URL: `http://localhost:8000` (local) or your deployed URL. Interactive docs at `/docs` (Swagger UI).

> This reference supersedes `api-contract.md` (kept for history). For the architecture and data flow, see [`architecture.md`](architecture.md).

## Authentication — facilitator token

`POST /sessions` issues a one-time **facilitator token** in the response (`facilitator_token`). Store it; send it as `Authorization: Bearer <token>` on the protected routes below. It is never re-served by any other endpoint.

| Route | Auth |
|-------|------|
| `POST /sessions/{id}/analyse` | Required |
| `GET /sessions/{id}/report` | Required |
| All other routes | None |

## Sessions

### Create a session
```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"topic": "Q3 strategy review", "framework": "swot"}'
```
Response (`201`-ish, actually `200`):
```json
{
  "id": "a1b2...",
  "topic": "Q3 strategy review",
  "framework": "swot",
  "custom_categories": [],
  "access_code": "MNJ36M",
  "status": "active",
  "participants": [],
  "created_at": "2026-07-04T...",
  "facilitator_token": "agmgyywxw6i..."   // one-time — store it
}
```
For a custom framework:
```json
{"topic": "Retro", "framework": "custom", "custom_categories": ["Wins","Risks","Actions"]}
```

### Get a session
```bash
curl http://localhost:8000/sessions/{session_id}
```

### Join by access code
```bash
curl -X POST http://localhost:8000/sessions/join/{access_code} \
  -H "Content-Type: application/json" \
  -d '{"name": "Anna"}'
```
Response: `{"participant_id": "...", "session_id": "..."}`

### Join by session id
```bash
curl -X POST "http://localhost:8000/sessions/{session_id}/join?name=Anna"
```

## Ideas

### Submit an idea
```bash
curl -X POST http://localhost:8000/sessions/{session_id}/ideas \
  -H "Content-Type: application/json" \
  -d '{"participant_id":"p1","participant_name":"Anna","content":"Strong team","category":"strength"}'
```
`category` is optional (participants can pre-tag; the AI categorises regardless).

### List ideas
```bash
curl http://localhost:8000/sessions/{session_id}/ideas
```

### Vote on an idea
```bash
curl -X POST http://localhost:8000/sessions/{session_id}/ideas/{idea_id}/vote
```
Returns the updated idea with the new vote count. v1 is a simple increment; per-participant dedup is future work.

### Live stream (SSE)
```bash
curl -N http://localhost:8000/sessions/{session_id}/ideas/stream
```
A `text/event-stream` of `idea_added`, `idea_voted`, `participant_joined` events. See [SSE events](#sse-events) below.

## Analysis

### Run AI analysis (facilitator token required)
```bash
curl -X POST http://localhost:8000/sessions/{session_id}/analyse \
  -H "Authorization: Bearer {facilitator_token}"
```
Synchronous — returns the full `AnalysisResult` JSON in the response. Categories are keyed by the framework's category ids.

### Get stored analysis (no re-run)
```bash
curl http://localhost:8000/sessions/{session_id}/analysis
```

### Download PDF report (facilitator token required)
```bash
curl -X GET http://localhost:8000/sessions/{session_id}/report \
  -H "Authorization: Bearer {facilitator_token}" \
  -o workshop-report.pdf
```

## SSE events

The stream emits frames like:
```
event: idea_added
data: {"type":"idea_added","data":{"id":"...","content":"...","votes":0,...}}

event: idea_voted
data: {"type":"idea_voted","data":{"idea_id":"...","votes":3}}

event: participant_joined
data: {"type":"participant_joined","data":{"participant_id":"...","name":"Anna","participant_count":2}}
```
Lines starting with `:` are heartbeats / connection confirmations — ignore them.

## Error responses

All errors use a consistent JSON shape: `{"detail": "...", "code": "..."}` (plus `request_id` on internal errors).

| Status | `code` | Meaning |
|--------|--------|---------|
| 200 | — | Success |
| 401 | `unauthorized` | Facilitator token missing/invalid (includes `WWW-Authenticate: Bearer`) |
| 404 | `session_not_found` / `idea_not_found` / `analysis_not_found` / `invalid_access_code` | Resource doesn't exist |
| 422 | `framework_not_found` / `invalid_framework` | Unknown framework id or malformed custom framework (also Pydantic's native 422 for body validation) |
| 429 | — | Rate limit exceeded (slowapi) |
| 500 | `internal_error` | Unexpected error — never a stack trace; includes `request_id` |
| 502 | `claude_parse_error` | Claude returned unparseable JSON even after the retry |
| 503 | `claude_error` | Claude API call failed (outage, rate limit, network) |

Every response includes an `X-Request-ID` header (reuses the client's `X-Request-ID` if sent) for log correlation.
