#!/usr/bin/env python3
"""
Compare a chapter’s tension profile to Nicholas-Sparks baseline data.

Usage:
    python compare_pacing.py  --chapter 3 \
                              --current  docs/pacing/chapter_tension_scores.csv \
                              --baseline docs/pacing/baseline_tension_dear_john.csv
"""
import argparse, pandas as pd, pathlib, sys, matplotlib.pyplot as plt

def load_scores(path: str, chapter: int) -> pd.Series:
    df = pd.read_csv(path)
    chap = df[df["chapter"] == chapter].set_index("scene").sort_index()
    if chap.empty:
        sys.exit(f"No rows for chapter {chapter} in {path}")
    return chap["tension_0-10"]

def main(chapter, current, baseline):
    cur = load_scores(current, chapter)
    base = load_scores(baseline, chapter)

    # Align by scene # (scenes present in either but not both → NaN)
    aligned = pd.concat({"current": cur, "baseline": base}, axis=1)
    aligned["diff"] = aligned["current"] - aligned["baseline"]
    aligned["abs_diff"] = aligned["diff"].abs()

    # Metrics
    mae = aligned["abs_diff"].mean()          # mean absolute error
    corr = aligned["current"].corr(aligned["baseline"])

    print(f"\nChapter {chapter} pacing comparison")
    print("-" * 32)
    print(aligned.fillna("-"))
    print(f"\nMean Abs. Diff: {mae:.2f}   |   Pearson r: {corr:.2f}")

    # Simple pass/fail rule (tweak as you like)
    if mae > 2 or corr < 0.3:
        print("\n⚠️  WARNING: Tension curve deviates strongly from baseline.")
    else:
        print("\n✅  Curve is comfortably Sparks-ish.")

    # Optional visual
    plt.plot(aligned.index, aligned["current"], marker="o", label="current")
    plt.plot(aligned.index, aligned["baseline"], marker="o", label="baseline")
    plt.title(f"Tension Comparison – Chapter {chapter}")
    plt.xlabel("Scene")
    plt.ylabel("Tension (0–10)")
    plt.ylim(0, 10)
    plt.legend()
    out = pathlib.Path(f"docs/pacing/ch{chapter:02d}_compare.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    print("saved plot →", out)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", type=int, required=True)
    ap.add_argument("--current", required=True)
    ap.add_argument("--baseline", required=True)
    main(**vars(ap.parse_args()))
