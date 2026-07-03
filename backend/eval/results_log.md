# Eval Results Log

Accuracy history for the idea-clustering eval (`eval/run_eval.py`), tracked so
prompt regressions show up immediately. Run before and after any change that
touches the prompt, framework config, or Claude integration.

## How to reproduce

```bash
cd backend
python eval/run_eval.py            # mock mode — fast, no API cost
python eval/run_eval.py --live     # live Claude (slow, costs tokens)
python eval/run_eval.py --bart     # BART-large-MNLI zero-shot comparison
```

Add a row here for every AI-layer change. Format:

| Date | Prompt/model | Mode | Accuracy | Notes |
|------|--------------|------|----------|-------|
| YYYY-MM-DD | description | mock/live/bart | N/M (P%) | what changed & why |

## History

| Date | Prompt / model | Mode | Accuracy | Notes |
|------|----------------|------|----------|-------|
| 2026-05-21 | Everything → strengths (mock floor) | mock | 26/90 (28.9%) | Baseline before PESTEL cases were added |
| 2026-05-21 | BART-large-MNLI (zero-shot) | bart | 62/90 (68.9%) | Free local comparison model |
| 2026-05-21 | Claude Sonnet 4 (framework-aware prompt) | live | 88/90 (97.8%) | SWOT reasoning with context |
| 2026-05-21 | Claude Sonnet 4 (SWOT + PESTEL cases) | live | 115/122 (94.3%) | SWOT 97.8%, PESTEL 84.4% (prose "80.0%" was a typo) |
| 2026-07-02 | Everything → strengths (mock floor) | mock | 25/122 (20.5%) | Re-run after dataset grew to 15 cases / 122 ideas. Mock assigns all ideas to a single category, so accuracy drops as the dataset gains more categories — expected behaviour, not a regression |
| 2026-07-03 | Claude Sonnet 4.5 (prompt v1, topic passed) | live | 128/137 (93.4%) | +2 custom-framework cases. SWOT 96.7%, PESTEL 81.2%, Custom 100%. ≥80% target met on all three frameworks. 11/17 cases perfect. |

> The 2026-07-02 mock number is lower than the 2026-05-21 mock number only because
> the dataset expanded (90 → 122 ideas, more PESTEL cases). The mock classifier
> dumps everything into one bucket, so a larger, more diverse dataset scores
> worse — this is the floor working as intended. Compare like-for-like (same
> dataset) when judging prompt changes.

## Per-framework breakdown (live, 2026-05-21)

| Framework | Correct | Total | Accuracy |
|-----------|---------|-------|----------|
| SWOT | 88 | 90 | 97.8% |
| PESTEL | 27 | 32 | 84.4% |
| **Overall** | **115** | **122** | **94.3%** |

## Per-framework breakdown (live, 2026-07-03)

Re-run after Phase 3: prompt extracted to v1 file (byte-identical), session
topic now passed through, + 2 custom-framework cases added. Dataset grew to
17 cases / 137 ideas. The runner now emits the per-framework table directly
(no longer hand-computed).

| Framework | Correct | Total | Accuracy | Cases |
|-----------|---------|-------|----------|-------|
| SWOT | 87 | 90 | 96.7% | 12 |
| PESTEL | 26 | 32 | 81.2% | 3 |
| Custom | 15 | 15 | 100.0% | 2 |
| **Overall** | **128** | **137** | **93.4%** | **17** |

11 of 17 cases perfect (100%).

### Notes
- **Custom frameworks hit 100%** — the pluggable framework system generalizes
  cleanly. Both new cases (Start/Stop/Continue; Champions/Skeptics/Neutral)
  were clustered perfectly. This is the strongest evidence that the
  schema-driven approach (Christian's feedback) works end-to-end.
- **PESTEL stays the weakest** (81.2%) — its categories overlap semantically
  (e.g. a "carbon tax" idea is both environmental and economic). This is the
  prompt-tuning headroom for a future v2 (Step 19): few-shot examples of
  ambiguous PESTEL ideas would likely help most here.
- **Reconciled the prior PESTEL number**: the 2026-05-21 row text said
  "80.0%" but the breakdown table said 84.4% (27/32). The breakdown was
  correct; the prose figure was a typo. Both are now superseded by the
  2026-07-03 run.

Target: ≥80% accuracy on each framework (SWOT, PESTEL, custom) — **met**
(SWOT 96.7%, PESTEL 81.2%, Custom 100%). See Step 19.
