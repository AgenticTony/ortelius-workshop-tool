# Demo Script — Workshop Tool (3–5 minute walkthrough)

A beats-by-minute script for demonstrating the Workshop Tool end-to-end. Shows **two frameworks** (SWOT + a custom one) per the roadmap requirement. Use the live deploy: `https://workshop-web-1gvl.onrender.com` (facilitator) — or run locally via `docker compose up` + `flutter run`.

> Open the deployed app on your laptop (facilitator) and have a phone or second browser tab ready (participant) before starting.

## Before you start (1 min)

- **Facilitator device:** open `https://workshop-web-1gvl.onrender.com` → tap **"I'm the facilitator"**.
- **Participant device:** open the same URL on a phone or second tab → tap **"I'm a participant"**.
- Have the demo talking points below ready.

## Script

### 0:00 — The problem (30s)
> "In a workshop, consultants capture dozens of ideas on sticky notes, then spend hours manually sorting them into a framework like SWOT. This tool captures them live, uses AI to cluster them in seconds, and produces a consultant-ready PDF."

### 0:30 — Create a session (45s) — *SWOT framework*
- On the facilitator device: tap **Create session**.
- Topic: **"Should we expand into the German market?"**
- Framework: **SWOT** (leave selected).
- Tap **Create**.
> "The facilitator picks a topic and a framework. We get an access code and a QR code participants can scan."

*Point at the access code + QR on the dashboard.*

### 1:15 — Participant joins + live ideas (1 min)
- On the participant device: type the access code + name "Anna" → **Join**.
- Submit 3–4 ideas quickly:
  - "Strong existing EU client relationships"
  - "Competitor already has a Berlin office"
  - "New German data privacy regulation"
  - "Hire a German-speaking sales lead"
> "Ideas appear live on the facilitator's dashboard the moment they're submitted — that's real-time over SSE."

*Point at the ideas appearing live on the facilitator dashboard as you submit.*

### 2:15 — Run AI analysis (1 min)
- On the facilitator dashboard: tap **Run AI analysis**.
- Wait ~10–15s (Claude is clustering).
> "Claude reads every idea, understands the SWOT framework from the category descriptions, and clusters each one. It also extracts key themes, decisions, and next steps."

*When it completes, tap **View analysis & download PDF** — walk through the category grid + themes.*

### 3:15 — Show the custom-framework capability (1 min) — *the differentiator*
> "SWOT is built-in. But a consultant's real value is their own frameworks. Watch this."

- Go back → create a new session.
- Topic: **"Q3 engineering retrospective"**
- Framework: **Custom** → categories: **"Start", "Stop", "Continue"**.
- Create, join from the participant device, submit 2–3 ideas.
- Run analysis.
> "The AI clusters into *our* categories — not a preset. Adding a framework is config, not code. We measured this: custom frameworks hit 100% accuracy on our eval dataset."

### 4:15 — The PDF + close (30s)
- On the analysis screen: tap **Download PDF report**.
> "A consultant-ready PDF — clustered ideas, themes, decisions, next steps. What used to take an hour now takes the length of this demo. Thank you."

## Demo notes
- **If the live deploy is slow** (free-tier cold starts take ~30s), fall back to local: `docker compose up` + `flutter run -d chrome`.
- **If Claude analysis times out**, show the stored analysis from a pre-run session (`GET /sessions/{id}/analysis`).
- **The two-framework requirement is met**: SWOT (1:15) + custom Start/Stop/Continue (3:15).
