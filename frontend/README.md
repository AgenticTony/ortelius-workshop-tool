# Workshop Tool — Frontend (Flutter)

The Flutter app (web + mobile) for the Workshop Tool. Participants join a workshop and submit/vote on ideas live; facilitators create sessions, run AI analysis, and download a PDF report.

See the root [`README.md`](../README.md) for the full project overview and [`docs/architecture.md`](../docs/architecture.md) for how the frontend fits into the system.

## Run

The app needs the backend running first (see root README — `docker compose up`).

```bash
cd frontend
flutter pub get
flutter run -d chrome       # web (recommended for local dev)
flutter run                 # macOS desktop / a connected device
```

The app points at `http://localhost:8000` by default. On web it **auto-discovers** the backend from the browser's own origin, so the same build works from a simulator, a phone over LAN, or a deployed URL without rebuilding. Edit `frontend/.env` (copy from `.env.example`) for non-web dev.

## Two roles

- **Facilitator** (`/facilitate/new`): create a session — pick a topic + framework (SWOT / PESTEL / **custom with your own categories**). Share the access code or QR. Watch ideas arrive live. Run AI analysis. Download the PDF.
- **Participant** (`/join`): enter the access code + your name. Submit ideas, see others' appear live over SSE, vote.

## Architecture

- **State:** Riverpod (`Notifier` providers in `lib/features/*/`).
- **HTTP:** `dio` with a bearer-token interceptor that auto-attaches the facilitator token to protected routes (`lib/core/api/workshop_api.dart`).
- **Real-time:** `SseClient` reads `text/event-stream` and emits typed events; auto-reconnects on drop (`lib/services/sse_client.dart`).
- **Routing:** `go_router` — `/` (role picker) → `/facilitate/new` → `/facilitate` → `/facilitate/report`, and `/join` → `/workshop` for participants.
- **Models:** typed classes mirroring the backend 1:1 (`lib/models/`).

## Test on a real phone over WiFi

1. Build the web app: `flutter build web --release`.
2. Serve it on your LAN: `cd build/web && python3 -m http.server 7355 --bind 0.0.0.0`.
3. Ensure the backend's `CORS_ORIGINS` includes your Mac's LAN origin (the compose defaults cover port 7355).
4. Open `http://<your-mac-LAN-ip>:7355` on your phone (same WiFi). Type the URL — some QR scanners force-upgrade to HTTPS.

## Checks

```bash
flutter analyze             # static analysis (should be clean)
flutter test                # widget tests
flutter build web --release # production web build
```

CI runs `flutter analyze` on every push/PR (see `.github/workflows/ci.yml`).

## Roadmap

Frontend progress is tracked in [`docs/frontend-roadmap.md`](../docs/frontend-roadmap.md). All 5 milestones (scaffold → participant → facilitator → polish → real-device hardening) are complete.
