"""Consolidated accuracy report across all Pravah models.

Reads models/registry.json (written by train_all.py) and expresses each model's
performance as a single 0-1 "accuracy" figure in its own natural terms, then a
simple mean as the headline overall number.

Note: the three models are different task types, so each accuracy is defined
differently. Definitions are printed alongside the numbers so nothing is hidden.
"""
from __future__ import annotations

import json
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parents[2] / "models"


def load_registry() -> dict:
    with open(MODELS_DIR / "registry.json", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    reg = load_registry()

    rows = []

    # Clearance: quantile regression -> P90 interval coverage is the natural
    # "accuracy" (share of events that actually clear within the predicted bound).
    cl = reg["clearance"]["metrics"]
    clearance_acc = cl["p90_coverage"]
    rows.append((
        "clearance",
        clearance_acc,
        f"P90 interval coverage (p50 MAE {cl['p50_mae']:.0f} min vs "
        f"baseline {cl['median_baseline_mae']:.0f})",
    ))

    # Triage: classification. Headline = mean of the two heads' MACRO-F1 (not
    # accuracy — macro-F1 is the honest metric under class imbalance). Per-head
    # macro-F1/accuracy and the Indic subset are printed in detail below.
    tr = reg["triage"]["metrics"]
    triage_macro_f1 = (tr["cause_macro_f1"] + tr["priority_macro_f1"]) / 2
    rows.append((
        "triage",
        triage_macro_f1,
        f"mean macro-F1: cause {tr['cause_macro_f1']:.3f} (16-class) / "
        f"priority {tr['priority_macro_f1']:.3f} (binary)",
    ))

    # Foresee: ranking -> precision@10 (top-10 predicted hotspots that were real).
    fs = reg["foresee"]["metrics"]
    foresee_acc = fs["precision_at_10"]
    rows.append((
        "foresee",
        foresee_acc,
        f"precision@10 hotspots (p@20 {fs['precision_at_20']:.2f}, "
        f"p@50 {fs['precision_at_50']:.2f})",
    ))

    overall = sum(acc for _, acc, _ in rows) / len(rows)

    width = 70
    print("=" * width)
    print("PRAVAH — MODEL ACCURACY REPORT")
    print(f"trained_at: {reg.get('trained_at', 'n/a')}")
    print("=" * width)
    print(f"{'model':<12}{'accuracy':>10}   definition")
    print("-" * width)
    for name, acc, desc in rows:
        print(f"{name:<12}{acc * 100:>9.1f}%   {desc}")
    print("-" * width)
    print(f"{'OVERALL':<12}{overall * 100:>9.1f}%   "
          f"unweighted mean of the three")
    print("=" * width)

    # Triage macro-F1 detail (overall vs Indic subset).
    print("\nTRIAGE — macro-F1 detail (head: "
          f"{reg['triage'].get('head_estimator', 'n/a')})")
    print("-" * width)
    print(f"{'head':<12}{'macro-F1':>10}{'accuracy':>10}{'macroF1@Indic':>16}")
    print(f"{'cause':<12}{tr['cause_macro_f1']:>10.3f}{tr['cause_accuracy']:>10.3f}"
          f"{tr.get('cause_macro_f1_indic', float('nan')):>16.3f}")
    print(f"{'priority':<12}{tr['priority_macro_f1']:>10.3f}{tr['priority_accuracy']:>10.3f}"
          f"{tr.get('priority_macro_f1_indic', float('nan')):>16.3f}")
    print(f"(test n={tr['test_n']}, Indic subset n={tr['indic_test_n']})")
    print("=" * width)


if __name__ == "__main__":
    main()