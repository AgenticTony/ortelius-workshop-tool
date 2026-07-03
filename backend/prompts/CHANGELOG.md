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
