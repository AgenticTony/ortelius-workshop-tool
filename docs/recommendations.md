# Recommendations for further development

An honest, Ortelius-facing assessment of the Workshop Tool prototype: what works, what's brittle, what we'd recommend doing next, and what it would cost to run for real. This is the strategic counterpart to the technical [`future_development.md`](future_development.md).

## What works

The full workshop loop is **live and demonstrable** end-to-end, deployed publicly on Render:

| Capability | Status |
|-----------|--------|
| Facilitator creates a session (SWOT, PESTEL, or **custom framework with any categories**) | ✅ |
| Participants join via access code or QR — **from a real phone** | ✅ |
| Ideas flow **live** across devices (SSE) | ✅ |
| One-click **Claude analysis** clusters ideas + extracts themes/decisions/questions/next steps | ✅ |
| Consultant-ready **PDF** download | ✅ |
| **Custom frameworks cluster at 100% accuracy** on the eval dataset | ✅ |
| Deployed: [`workshop-web-1gvl.onrender.com`](https://workshop-web-1gvl.onrender.com) | ✅ |

The standout result: **custom frameworks at 100% accuracy** is the strongest evidence that the pluggable, schema-driven framework system (Christian's *"beskrivning av innehållet"* feedback) generalizes beyond the built-in SWOT/PESTEL — the core of what Ortelius asked for.

## What's brittle (be aware before relying on it)

| Area | Risk | Mitigation |
|------|------|------------|
| **SSE is single-worker** | The real-time event bus is in-memory → one uvicorn worker only. Horizontal scaling breaks live updates. | Move to Postgres `LISTEN/NOTIFY` or Redis pub/sub (the documented next step). |
| **Voting has no dedup** | A participant can upvote repeatedly — counts aren't honest. | Add a `votes` table (participant_id + idea_id unique). |
| **Free-tier Render Postgres expires in 90 days** | The deployed DB will be deleted. | Move to a paid plan before relying on it; Supabase (already wired) is the alternative. |
| **Mobile PDF save** | Web downloads the PDF; iOS/macOS return a no-op (no share sheet). | Wire `share_plus`. |
| **Identity lost on refresh** | A participant who refreshes must re-join. | sessionStorage + a rejoin token. |
| **Cold-start latency** | Render free tier sleeps idle services; first request after idle takes ~30s. | Upgrade to a paid plan for always-on. |

None of these are architectural — they're all incremental, documented in [`future_development.md`](future_development.md), and don't require rework.

## Cost analysis

Assumptions: ~30 ideas per workshop, Claude Sonnet 4.5 pricing (~$3/M input + $15/M output tokens), ~900 input + ~400 output tokens per analysis ≈ **$0.009 per workshop**.

| Workshops/month | Claude cost | Render infra | **Total** |
|-----------------|-------------|--------------|-----------|
| 10 | $0.09 | $0 (free tier) | **< $1** |
| 100 | $0.90 | ~$7 (starter) | **~$8** |
| 1,000 | $9.00 | ~$20 (starter + managed PG) | **~$30** |

**Claude cost is negligible** at any realistic Ortelius volume. Infrastructure (hosting + managed Postgres) dominates. The rate limit (5 analyses/min/IP) bounds worst-case spend. See [`future_development.md`](future_development.md#cost-analysis-estimated-monthly-run-cost) for detail.

## Concrete recommendations (prioritized)

1. **Framework-editor UI.** Consultants currently define a custom framework by passing JSON. A UI where they author category *names + descriptions* (the lever most likely to push accuracy higher and satisfy the brief fully) is the single highest-value product addition. The backend already supports it — this is frontend-only work.
2. **Multi-worker SSE** (Postgres `LISTEN/NOTIFY`). Unlocks horizontal scaling — the biggest architectural item before this can serve many concurrent workshops.
3. **Vote dedup** + persistent participant identity. Small, makes the participant experience honest.
4. **Few-shot prompt (v2)** focused on ambiguous PESTEL ideas — the most likely accuracy improvement (PESTEL is the weakest at 81.2%).
5. **Move off the free-tier Postgres** (or wire Supabase, which is already supported) before relying on the deploy.
6. **Rotate the Claude key + DB password** before production use — they've lived in plaintext on the dev machine (gitignored, never committed, but should be rotated per hygiene).

## What we deliberately deferred

These are documented in [`future_development.md`](future_development.md) as out-of-scope for the prototype, not forgotten: multi-tenant isolation, SSO, real-time analysis editing, webhooks, matrix-form PDF rendering, internationalisation, mobile-native facilitator app, workshop replay, Word/PowerPoint export, real-time AI suggestions during the workshop, and vector search across past workshops.

## Bottom line

The prototype is **demo-ready and deployed**, the architecture is sound and well-documented, and the path to production is **configuration + incremental work, not rearchitecting**. The eval framework + the pluggable framework system are the portfolio-grade artefacts that distinguish this from a generic "I used an LLM" project. The honest brittleness list above is short and every item has a clear fix.
