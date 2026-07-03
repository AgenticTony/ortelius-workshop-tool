# Workshop Support Tool

### Ortelius Internship — Project 5 | May–August 2026

A lightweight digital tool for capturing, structuring, and summarising workshop input in real time.

## What It Does

- Participants submit ideas live from their phone or browser
- AI automatically clusters input into SWOT, PESTEL, or custom frameworks
- Generates a formatted consultant-ready PDF report instantly

## Tech Stack

| Layer             | Technology             |
| ----------------- | ---------------------- |
| Frontend          | Flutter (Web + Mobile) |
| Real-time sync    | Firebase Firestore     |
| Backend / API     | Python + FastAPI       |
| AI Analysis       | Anthropic Claude API   |
| Report Generation | Python (ReportLab)     |
| Version Control   | GitHub                 |

## Project Structure

workshop-tool/
├── backend/ # FastAPI server, Claude API integration, PDF generation
├── frontend/ # Flutter app (mobile + web)
├── docs/ # Architecture diagrams, API contract
├── tests/ # AI evaluation dataset and test cases

## Setup

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) with the Compose plugin (Docker Desktop includes both)

### Run the stack locally (recommended)

One command brings up Postgres and the API together:

```bash
docker compose up          # build + start (add --build to force a rebuild)
```

The API boots once Postgres is healthy, creates its tables if missing, and serves on `http://localhost:8000`.

- Interactive API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

```bash
docker compose down        # stop (keeps the database volume)
docker compose down -v     # stop and wipe the local database
```

### Set the Claude API key (needed only for AI analysis)

The app boots without it. To run `POST /sessions/{id}/analyse`, provide a key
either via an environment variable or a `.env` file in the repo root:

```bash
# .env
CLAUDE_API_KEY=sk-ant-...
CORS_ORIGINS=http://localhost:3000
```

`docker compose up` picks up `.env` automatically.

### Run without Docker (local dev)

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload
```

Tests use an in-memory SQLite database, so they run with no Postgres running:

```bash
cd backend && pytest tests/
```

## Team

- Anthony —
- Mohand —

## Internship Timeline

- Weeks 1–2: Onboarding and scope
- Weeks 3–4: Architecture and proof of concept
- Weeks 5–8: Core development
- Weeks 9–10: Testing and QA
- Weeks 11–12: Final demo and documentation

For the full 12-week project, here's everything:

  Foundation (Steps 1-4) — Weeks 3-4
  1. FastAPI skeleton
  2. Pydantic models
  3. Routes (sessions, ideas)
  4. Config and env vars

  Core Features (Steps 5-7) — Weeks 5-6
  5. Claude integration (clustering + summarisation)
  6. PDF generation (ReportLab)
  7. Wire up analysis route (one-click AI → PDF)

  Production Readiness (Steps 8-11) — Weeks 7-8
  8. Database — swap in-memory dicts for PostgreSQL or Firebase
  9. Evaluation dataset — test workshop inputs to measure AI accuracy (target: 80%)
  10. Error handling — proper error responses, edge cases, input sanitisation
  11. Prompt tuning — iterate on Claude prompts against the evaluation dataset

  Testing & Polish (Steps 12-14) — Weeks 9-10
  12. Backend tests — unit tests for routes, services, models
  13. Integration testing with frontend — Mohand's Flutter app hitting your API
  14. User testing with Ortelius consultants — real feedback

  Final Delivery (Steps 15-16) — Weeks 11-12
  15. Docker + deployment — containerise, deploy (Azure?)
  16. Documentation — README, setup guide, API reference, architecture diagram

