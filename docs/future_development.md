# Future development — what's next, what's brittle

An honest assessment of where the prototype stops and what it would take to make it production-grade. Intended for whoever picks this up next (Ortelius or another developer).

## What works (the demoable loop)

- Facilitator creates a session (SWOT / PESTEL / **custom framework with any categories**).
- Participants join via access code or QR, from a real phone over WiFi.
- Ideas flow **live** across devices via SSE; voting updates counts everywhere.
- One-click Claude analysis clusters ideas into the chosen framework with themes, decisions, questions, and next steps.
- Consultant-ready **PDF** downloads in the browser.
- Custom frameworks cluster at **100% accuracy** on the eval dataset; SWOT 96.7%, PESTEL 81.2%.
- Migrations (Alembic), typed errors, per-call logging, CI.

## What's brittle / known limitations

| Area | Limitation | Impact |
|------|------------|--------|
| **SSE transport** | In-memory event bus → **single uvicorn worker only**. | Horizontal scaling breaks real-time. Needs Postgres `LISTEN/NOTIFY` or Redis pub/sub for multi-worker. |
| **Voting** | Simple increment, no per-participant dedup. | A participant can upvote repeatedly. Needs a `votes` table (participant_id + idea_id unique) for honest counts. |
| **Mobile PDF save** | Web downloads the PDF; iOS/macOS return a no-op (no share sheet wired). | Mobile users can't save the report locally yet. Needs `share_plus`. |
| **Identity persistence** | Participant identity lost on page refresh. | Re-join required after a refresh. Needs sessionStorage / a rejoin token. |
| **Facilitator auth** | Opaque bearer token, not accounts. | Fine for workshops; no SSO, no multi-tenant isolation. |
| **Custom framework descriptions** | Auto-generated placeholders, not authored. | Accuracy for custom frameworks could be higher with real per-category descriptions. Needs a framework-editor UI. |
| **Existing Supabase DB migration** | Schema was created by `init_db.create_all` before Alembic landed. | On first Alembic deploy against that DB, run `alembic stamp head` (marks as migrated without running DDL) before `alembic upgrade head`. |
| **Cost protection** | Rate limits exist (5/min analyse, 30/min ideas) but no daily token-budget cap. | A malicious/buggy client could overspend. Needs a token-budget guard. |

## Concrete next steps (prioritized)

1. **Multi-worker SSE** — move the event bus onto Postgres `LISTEN/NOTIFY`. Unlocks horizontal scaling. The biggest single architectural item.
2. **Vote dedup** — add a `votes` table; one vote per participant per idea.
3. **Framework-editor UI** — let consultants author per-category descriptions (the lever most likely to push custom-framework accuracy higher and satisfy Christian's brief fully).
4. **Few-shot prompt examples (v2)** — add 1–2 examples to the prompt, focused on ambiguous PESTEL ideas. Re-run eval. See [`prompt_design.md`](prompt_design.md).
5. **Persistent participant identity** — survive refresh via sessionStorage + a rejoin endpoint.
6. **Daily token budget** — hard cap with a logged warning before hitting it.
7. **Mobile PDF share** — wire `share_plus` for iOS/Android.
8. **Cloud deployment** — Render Blueprint exists (see [`deployment.md`](deployment.md)); productionise with a custom domain + managed Postgres backups.

## Cost analysis (estimated monthly run cost)

Assumptions: a workshop = 1 analysis call; ~30 ideas per workshop; Claude Sonnet 4.5 pricing ~$3/M input + $15/M output tokens; a typical 30-idea analysis uses ~900 input + ~400 output tokens ≈ $0.009 per analysis.

| Workshops/month | Claude cost | Infra (Render free/starter) | Approx total |
|----------------|-------------|------------------------------|--------------|
| 10 | $0.09 | $0 (free tier) | **< $1** |
| 100 | $0.90 | ~$7 (starter web svc) | **~$8** |
| 1,000 | $9.00 | ~$20 (starter + managed PG) | **~$30** |

Claude cost is negligible at this scale; infrastructure (hosting + managed Postgres) dominates. The rate limit (5 analyses/min/IP) bounds worst-case spend.

## Deliberately deferred (out of scope for the prototype)

- Multi-tenant isolation (one instance per Ortelius client).
- SSO for facilitators.
- Real-time collaboration on analysis editing.
- Webhooks (e.g. notify Slack when a workshop ends).
- Matrix-form PDF rendering using the `Axis` metadata (structure is in place; rendering deferred).
- Internationalisation (English-only).
- Mobile-native facilitator app.
- Workshop replay / history view.
- Export to Word or PowerPoint (PDF only).
- Real-time AI suggestions during the workshop (batch analysis at the end only).
- Vector search across past workshops ("have we seen this idea before").
