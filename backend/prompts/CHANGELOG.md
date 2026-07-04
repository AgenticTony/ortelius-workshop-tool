# Prompt CHANGELOG

Each entry records what changed in a prompt version, why, and the measured
accuracy delta against the eval dataset (`eval/run_eval.py`). This is the
"prompt engineering is real engineering" artifact — the iteration history
with data behind it.

## Schema

```
## vX (YYYY-MM-DD)
- File: clustering_vX.md
- What changed: <concrete diff from the previous version>
- Why: <the failure mode / hypothesis that drove the change>
- Accuracy delta: <before → after, per framework>
```

## v2 (2026-07-04)

- **File:** `clustering_v2.md`
- **What changed:** Two fixes to the JSON skeleton in the prompt (wording
  and rules unchanged):
  1. Replaced the doubled `{{`/`}}` braces with single `{`/`}` — a leftover
     from the `.format()` era that survived the switch to `str.replace`, so
     v1's "valid JSON matching this exact structure" example was itself
     invalid JSON.
  2. Inject the real `session_id` (new `{session_id}` placeholder) instead of
     leaving the literal text `<session_id>`. `AnalysisResult.session_id` is
     required, so v1 relied on the model inferring the id from the user
     message; if it didn't, `AnalysisResult(**parsed)` raised
     `ValidationError` (now caught as `ClaudeParseError`, but the root cause
     was the prompt never naming the value).
- **Why:** A spec-following or smaller model is likelier to echo the example
  verbatim; v1 would then hand back malformed JSON or a placeholder id. v2
  shows correct, fillable JSON.
- **Accuracy:** not re-measured (no model behavior change expected — Sonnet
  already coped with both defects); rerun `eval/run_eval.py` to confirm.

## v1 (2026-07-03)

- **File:** `clustering_v1.md`
- **What changed:** Initial version — moved the prompt out of
  `frameworks.py:build_system_prompt` verbatim into a versioned file. No
  wording changes; this is a pure extraction so future edits are config
  (no code redeploy) and tracked here.
- **Why:** Prompt tuning needs a paper trail. Editing a Python string gave
  no history, no per-version accuracy, and required a code change for a
  wording tweak.
- **Accuracy:** unchanged from the prior in-code prompt — SWOT 97.8%,
  PESTEL 84.4%, overall 94.3% (live, 2026-05-21). The byte-identical
  render is asserted in `tests/`.

### Known follow-ups (not in v1)
- Few-shot examples (one SWOT, one PESTEL) — roadmap Step 8 TODO.
- Pass the real session topic through (done in the same PR that introduced
  this file — previously hardcoded `(workshop)`).
