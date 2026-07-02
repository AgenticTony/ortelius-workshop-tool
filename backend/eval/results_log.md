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
| 2026-05-21 | Claude Sonnet 4 (SWOT + PESTEL cases) | live | 115/122 (94.3%) | SWOT 97.8%, PESTEL 80.0% |
| 2026-07-02 | Everything → strengths (mock floor) | mock | 25/122 (20.5%) | Re-run after dataset grew to 15 cases / 122 ideas. Mock assigns all ideas to a single category, so accuracy drops as the dataset gains more categories — expected behaviour, not a regression |

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

Target: ≥80% accuracy on each framework (SWOT, PESTEL, custom) — see Step 19.
