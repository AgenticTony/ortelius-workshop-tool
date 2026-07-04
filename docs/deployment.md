# Deployment — Render

The Workshop Tool deploys as three Render services from the `render.yaml` Blueprint: a managed Postgres, the FastAPI backend (Docker), and the Flutter web frontend (Docker → nginx). This doc walks through the first deploy.

> Render provides HTTPS automatically on `*.onrender.com` — no cert management needed.

## Prerequisites

- A Render account (https://render.com — the free tier works for a prototype).
- This repo connected to Render (Render reads `render.yaml` from the connected GitHub repo).
- Your **Anthropic API key** (`CLAUDE_API_KEY`) — set as a secret, never committed.

## ⚠️ Security — rotate before going live

The Claude API key and Supabase DB password currently sit in plaintext in `backend/.env` (correctly gitignored — never committed — but readable on your dev machine). **Before relying on a production deploy, rotate both** and put only the new values in Render's secret store. See [`future_development.md`](future_development.md#what-s-brittle-known-limitations).

## First deploy — step by step

1. **Create the Blueprint:**
   - Render dashboard → **New** → **Blueprint**
   - Select this GitHub repo. Render reads `render.yaml` and shows the three services (workshop-db, workshop-api, workshop-web).
   - Pick a region (the Blueprint defaults to `frankfurt` — change in `render.yaml` if needed).

2. **Set the secret before applying:**
   - In the preview screen, find `workshop-api` → `CLAUDE_API_KEY` and paste your Anthropic key.
   - Apply. Render provisions the Postgres, builds + deploys both web services.

3. **Wait for the build** (first build is slow — the Flutter image pulls the SDK). Both services have health checks:
   - API health: `https://workshop-api.onrender.com/health` → `{"status":"ok",...}`
   - Web: `https://workshop-web.onrender.com` → the Flutter app loads.

4. **Tighten CORS** (after first deploy):
   - The Blueprint ships with `CORS_ORIGINS=*` so the first deploy works regardless of the web URL. Once `workshop-web.onrender.com` is live, set `CORS_ORIGINS` on the API to `https://workshop-web.onrender.com` (Render dashboard → workshop-api → Environment).

5. **Migrations:**
   - The API container runs `alembic upgrade head` on every boot via its entrypoint. Against a fresh managed Postgres this creates all four tables. **No manual step needed for a fresh DB.**
   - If you ever point this at the *existing* Supabase DB (already populated by the old `init_db.create_all`), first run `alembic stamp head` once against it (marks it as migrated without running DDL), then deploys run normally.

## Verifying the live deploy

```bash
# API health
curl https://workshop-api.onrender.com/health
# → {"status":"ok","service":"workshop-tool"}

# Create a session (returns access_code + facilitator_token)
curl -X POST https://workshop-api.onrender.com/sessions \
  -H "Content-Type: application.json" \
  -d '{"topic":"Live deploy test","framework":"swot"}'

# Open the frontend in a browser, create a session, run the full loop.
# The web build has the API URL baked in via the API_BASE_URL build arg
# (see render.yaml → workshop-web → envVars).
```

## Cost

See [`future_development.md`](future_development.md#cost-analysis-estimated-monthly-run-cost) for the breakdown. Short version: Claude cost is negligible (~$1/mo at 100 workshops); Render free/starter infra dominates (~$8/mo at the starter tier). The free-tier Postgres is deleted after 90 days — fine for a prototype, move to a paid plan for persistence.

## Custom domain

Render supports custom domains on paid plans (Settings → Custom Domains). The Blueprint doesn't include one — add it via the dashboard when ready. HTTPS is provisioned automatically.

## Out of scope

- Multi-worker SSE (the in-memory bus is single-worker) — documented in [`future_development.md`](future_development.md).
- A separate secret manager beyond Render's env vars.
- Managed Postgres backups beyond Render's defaults.
