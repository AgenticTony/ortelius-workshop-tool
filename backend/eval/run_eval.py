"""
Eval runner — measures framework clustering accuracy.

Usage:
    python eval/run_eval.py              # mock mode (fast, no API calls)
    python eval/run_eval.py --live        # live mode (calls Claude, costs money)
    python eval/run_eval.py --bart        # BART-large-MNLI (free, runs locally)

The eval dataset lives in eval/test_inputs.json.
Each entry has: topic, ideas, expected category per idea_id.

Scoring: accuracy = correct_category_assignments / total_ideas
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Backend is one level up from eval/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

EVAL_DATA = Path(__file__).resolve().parent / "test_inputs.json"


def load_dataset() -> list[dict]:
    with open(EVAL_DATA) as f:
        return json.load(f)


def _case_labels(case: dict) -> list[str]:
    """Extract unique category labels from a test case's expected values."""
    return sorted(set(case["expected"].values()))


def run_mock(case: dict) -> dict[str, str]:
    """Mock clustering — assigns everything to the first expected category.

    This is the baseline floor. Accuracy depends on class balance.
    The point is that the pipeline works end-to-end before the AI is good.
    """
    first_label = _case_labels(case)[0]
    return {idea["id"]: first_label for idea in case["ideas"]}


def run_bart(case: dict) -> dict[str, str]:
    """Zero-shot classification using facebook/bart-large-mnli.

    Classifies each idea independently against the case's category labels.
    No context from other ideas — pure label-text matching.
    Free, runs locally, first run downloads ~1.3GB model.
    """
    from transformers import pipeline

    if not hasattr(run_bart, "_classifier"):
        run_bart._classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
        )

    classifier = run_bart._classifier
    labels = _case_labels(case)
    assignments = {}
    for idea in case["ideas"]:
        result = classifier(
            idea["content"],
            candidate_labels=labels,
        )
        assignments[idea["id"]] = result["labels"][0]
    return assignments


def run_live(case: dict) -> dict[str, str]:
    """Call the real Claude service — costs tokens."""
    from app.services.claude_service import analyse_ideas

    custom_cats = case.get("custom_categories")
    result = analyse_ideas(
        session_id=case["id"],
        framework=case["framework"],
        ideas=case["ideas"],
        custom_categories=custom_cats if custom_cats else None,
    )

    # Flatten all categories into {idea_id: category_name}
    assignments = {}
    for cat_name, clustered_list in result.categories.items():
        for clustered in clustered_list:
            assignments[clustered.idea_id] = cat_name
    return assignments


def score_case(case: dict, predictions: dict[str, str]) -> dict:
    """Compare predictions against ground truth, return detailed results."""
    expected = case["expected"]
    correct = 0
    total = len(expected)
    mismatches = []

    for idea_id, expected_cat in expected.items():
        predicted = predictions.get(idea_id, "MISSING")
        if predicted == expected_cat:
            correct += 1
        else:
            mismatches.append({
                "idea_id": idea_id,
                "expected": expected_cat,
                "predicted": predicted,
            })

    return {
        "case_id": case["id"],
        "topic": case["topic"],
        "correct": correct,
        "total": total,
        "accuracy": round(correct / total * 100, 1) if total else 0,
        "mismatches": mismatches,
    }


def print_report(results: list[dict], dataset: list[dict]) -> None:
    """Print per-case breakdown + per-framework + overall accuracy."""
    print("\n" + "=" * 60)
    print("EVAL RESULTS")
    print("=" * 60)

    # Map case_id -> framework so we can group.
    case_framework = {c["id"]: c.get("framework", "swot") for c in dataset}

    for r in results:
        status = "PASS" if r["accuracy"] == 100 else "PARTIAL" if r["accuracy"] > 0 else "FAIL"
        print(f"\n  {r['case_id']}: {r['topic']}")
        print(f"    Accuracy: {r['correct']}/{r['total']} ({r['accuracy']}%) [{status}]")

        if r["mismatches"]:
            for m in r["mismatches"]:
                print(f"    MISS: {m['idea_id']} -> expected {m['expected']}, got {m['predicted']}")

    total_correct = sum(r["correct"] for r in results)
    total_ideas = sum(r["total"] for r in results)
    overall = round(total_correct / total_ideas * 100, 1) if total_ideas else 0

    # Per-framework aggregation (group results by the case's framework field).
    fw_groups: dict[str, list[dict]] = {}
    for r in results:
        fw = case_framework.get(r["case_id"], "unknown")
        fw_groups.setdefault(fw, []).append(r)

    print("\n" + "-" * 60)
    print("PER-FRAMEWORK")
    for fw in sorted(fw_groups):
        rs = fw_groups[fw]
        fc = sum(r["correct"] for r in rs)
        ft = sum(r["total"] for r in rs)
        facc = round(fc / ft * 100, 1) if ft else 0
        print(f"  {fw:8s}: {fc}/{ft} ({facc}%) — {len(rs)} case(s)")

    print("\n" + "-" * 60)
    print(f"OVERALL: {total_correct}/{total_ideas} ({overall}%)")
    print(f"Cases: {len(results)} | Perfect: {sum(1 for r in results if r['accuracy'] == 100)}")
    print("-" * 60)


def main():
    parser = argparse.ArgumentParser(description="Run SWOT clustering eval")
    parser.add_argument("--live", action="store_true", help="Call real Claude API (costs money)")
    parser.add_argument("--bart", action="store_true", help="Use BART-large-MNLI (free, local)")
    args = parser.parse_args()

    dataset = load_dataset()
    print(f"Loaded {len(dataset)} test cases ({sum(len(c['ideas']) for c in dataset)} total ideas)")

    if args.live:
        mode = "LIVE (Claude API)"
        run_fn = run_live
    elif args.bart:
        mode = "BART-large-MNLI (local)"
        run_fn = run_bart
    else:
        mode = "MOCK (baseline)"
        run_fn = run_mock

    print(f"Mode: {mode}")
    results = []

    start = time.time()
    for case in dataset:
        predictions = run_fn(case)
        result = score_case(case, predictions)
        results.append(result)
        print(f"  {case['id']}: {result['accuracy']}%", flush=True)

    elapsed = round(time.time() - start, 1)
    print(f"\nCompleted in {elapsed}s")

    print_report(results, dataset)


if __name__ == "__main__":
    main()
