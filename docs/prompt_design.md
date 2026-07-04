# Prompt design — how the AI layer works

The Workshop Tool uses Anthropic Claude to cluster participant ideas into a framework (SWOT, PESTEL, or custom) and extract themes, decisions, open questions, and next steps. This doc covers the prompt, the versioning system, the reliability patterns, and the eval-driven approach.

## The prompt

The clustering prompt lives in **`backend/prompts/clustering_v1.md`** as a versioned template (config, not code). It's loaded + rendered at runtime by `app/prompts.render_clustering_prompt`, which substitutes the framework-specific values:

- `{framework_name}` — e.g. "SWOT Analysis"
- `{framework_description}` — the framework's short context
- `{categories_block}` — one `- {id}: {description}` line per category
- `{categories_json_keys}` — the JSON shape Claude must return

The prompt instructs Claude to:
1. Assign every idea to exactly one category
2. Reference the original `idea_id` for each clustered idea (provenance — an Ortelius governance requirement)
3. Write a short summary per idea in context
4. Identify 3–5 key themes, list decisions, open questions, and recommended next steps
5. Respond with **valid JSON only** — no markdown, no explanation

The category **descriptions** (not just names) are injected because that's what makes clustering accurate — Christian's *"beskrivning av innehållet"* feedback. See [`frameworks.md`](frameworks.md).

## Why structured JSON output

Claude returns a JSON object matching the `AnalysisResult` Pydantic schema. This is the schema-driven-LLM-output pattern (cf. Instructor, OpenAI structured outputs): the prompt constrains the shape, the backend parses it into typed models, and the result is stored queryably + renders deterministically into a PDF. No free-text parsing, no fragile regex.

## Reliability patterns

### Retry on bad JSON
If Claude's first response isn't valid JSON, `_call_claude` retries **once** with a corrective turn appended ("Your previous response was not valid JSON. Return ONLY the JSON object..."). If the retry also fails to parse, the call raises `ClaudeParseError` → HTTP 502 (a clean error, not a 500). See [`api_reference.md`](api_reference.md#error-responses).

### Upstream failure → typed error
Any `anthropic.AnthropicError` (outage, rate limit, auth, network) is caught and re-raised as `ClaudeAPIError` → HTTP 503. A Claude outage surfaces as a clean "AI service unavailable" rather than an opaque 500 with a stack trace.

### The session topic is passed through
The user message includes the real `session.topic` (previously hardcoded to `(workshop)` — a bug fixed in the prompt-versioning PR). Giving Claude the actual workshop topic measurably improves the relevance of themes and next steps.

## Versioning

The prompt is versioned so changes are tracked with accuracy deltas:

- **`PROMPT_VERSION = "clustering_v1"`** (in `app/prompts.py`) — logged on every Claude call.
- **`backend/prompts/CHANGELOG.md`** — each version records what changed, why, and the accuracy delta from the eval run.

To introduce a new version:
1. Copy `clustering_v1.md` → `clustering_v2.md`, edit the wording.
2. Bump `PROMPT_VERSION` to `"clustering_v2"`.
3. Run `python eval/run_eval.py --live` and record the accuracy delta in `CHANGELOG.md`.
4. (The byte-identical assertion in `tests/test_prompt.py` only pins v1 — a v2 needs its own fixture or the test updated.)

v1 is a pure extraction of the original in-code prompt (no wording change), asserted byte-identical to the legacy string so the move was a provable no-op for accuracy.

## Per-call logging

Every Claude call emits a structured log line — the production-readiness Step 7 requirement:

```
claude_call prompt_version=clustering_v1 framework=swot model=claude-sonnet-4-5-20250929 \
            input_tokens=926 output_tokens=403 latency_ms=17223 retry=True
```

Fields: `prompt_version`, `framework`, `model`, `input_tokens`, `output_tokens`, `latency_ms`, `retry` (whether the JSON-parse retry fired). Pulled from Anthropic's `response.usage`. This makes cost and quality observable per call.

## The eval-driven approach

The prompt is measured, not vibes-tuned. The eval framework (`backend/eval/run_eval.py`) runs the clustering against a labelled dataset and reports per-framework accuracy. See [`evaluation.md`](evaluation.md) for the methodology and results. Current numbers (live, 2026-07-03):

| Framework | Accuracy |
|-----------|----------|
| SWOT | 96.7% |
| PESTEL | 81.2% |
| Custom | 100.0% |

Any prompt change is validated by re-running the eval — a regression shows up immediately rather than in a demo.

## Few-shot examples (not yet in v1)

The roadmap (Step 8) calls for 1–2 few-shot examples in the prompt (one SWOT, one PESTEL). v1 is zero-shot. PESTEL is the weakest framework (overlapping categories — "carbon tax" is both environmental and economic), so few-shot examples of ambiguous PESTEL ideas are the most likely v2 improvement.
