# Evaluation — measuring AI clustering accuracy

The Workshop Tool doesn't just *use* an LLM — it **evaluates** one. This doc covers the eval methodology, the dataset, and the results. The eval framework is the single biggest difference between "I used an LLM in a project" and "I evaluated an LLM in a project."

## Why eval

Without a labelled dataset and a runner, prompt changes are vibes-tuned — you tweak wording, eyeball a couple of outputs, and hope. The eval framework turns prompt iteration into measured engineering: change the prompt, run the eval, see the accuracy delta. Regressions show up in seconds, not in a demo.

## The runner — `backend/eval/run_eval.py`

Three modes:

| Mode | Command | What it does |
|------|---------|--------------|
| **Mock** | `python eval/run_eval.py` | Assigns every idea to the first expected category. The accuracy floor — proves the pipeline runs end-to-end before the AI is any good. Free, instant. |
| **BART** | `python eval/run_eval.py --bart` | Zero-shot classification via `facebook/bart-large-mnli` (HuggingFace, ~1.3GB first download). Classifies each idea independently against the category labels — no cross-idea context, no reasoning. Free, local, a comparison baseline. |
| **Live** | `python eval/run_eval.py --live` | Calls the real Claude service. Costs tokens. The number that matters. |

### Scoring
`accuracy = correct_category_assignments / total_ideas`. A prediction is "correct" if the category id Claude returned matches the labelled expected category for that idea id. The runner reports per-case accuracy (PASS = 100%, PARTIAL >0%, FAIL = 0%) plus an **automated per-framework breakdown** (SWOT / PESTEL / custom).

## The dataset — `backend/eval/test_inputs.json`

- **17 test cases, 137 ideas total.**
- **SWOT:** 12 cases / 90 ideas (eval-001 … eval-012). Includes clear cases and an adversarial one (eval-012: single-word idea contents — the failure mode).
- **PESTEL:** 3 cases / 32 ideas (Nordic healthcare, EV charging, fintech launch).
- **Custom:** 2 cases / 15 ideas (a Start/Stop/Continue retrospective; a Champions/Skeptics/Neutral stakeholder map). Both realistic facilitation frameworks a consultant would run.
- Each idea has an `expected` category id assigned by hand as ground truth.

## Results (live, 2026-07-03)

| Framework | Correct | Total | Accuracy | Cases |
|-----------|---------|-------|----------|-------|
| SWOT | 87 | 90 | **96.7%** | 12 |
| PESTEL | 26 | 32 | **81.2%** | 3 |
| Custom | 15 | 15 | **100.0%** | 2 |
| **Overall** | **128** | **137** | **93.4%** | **17** |

11 of 17 cases perfect (100%).

### Comparison across modes (the "why Claude" story)
| Model | Mode | Overall |
|-------|------|---------|
| Everything → first category | mock | 20.5% (floor) |
| BART-large-MNLI | bart | 68.9% (zero-shot, no context) |
| Claude Sonnet 4.5 | live | 93.4% (reasoning with context) |

The gap between BART (label-matching) and Claude (reasoning with the framework descriptions + cross-idea context) is the value of the approach.

### What the numbers tell us
- **Custom frameworks at 100%** is the strongest evidence that the pluggable, schema-driven framework system (Christian's feedback) generalizes — not just the built-in SWOT/PESTEL.
- **PESTEL is the weakest** because its categories overlap semantically (a "carbon tax" idea is both environmental and economic). This is the prompt-tuning headroom: few-shot examples of ambiguous PESTEL ideas would likely help most.

## Target

The roadmap target (Step 19) is **≥80% accuracy on each framework**. **Met:** SWOT 96.7%, PESTEL 81.2%, Custom 100%.

## Where the numbers live

- **Per-run history + the per-framework table:** [`backend/eval/results_log.md`](../backend/eval/results_log.md). Each live run appends a dated row.
- **Prompt iteration history:** [`backend/prompts/CHANGELOG.md`](../backend/prompts/CHANGELOG.md).
- **Per-call logs** (tokens, latency, version): emitted by the backend at runtime — see [`prompt_design.md`](prompt_design.md#per-call-logging).
