"""Evaluate the trained MuRIL classifier on the refined MP test set.

Usage (from repo root):
    python service-classifier/eval/evaluate_on_mp.py \
        --data /Users/hariom/Desktop/mp_grievances_refined.csv \
        --out  service-classifier/eval/report

Outputs:
    report/predictions.csv     — per-row prediction + gold + match flag
    report/metrics.json        — accuracy / weighted-F1 per head
    report/confusion_dept.csv  — confusion matrix for department
    report/errors_dept.csv     — first 200 misclassified rows for inspection
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, classification_report,
                              confusion_matrix, f1_score)

# Import the project's predictor directly — no need to spin up the FastAPI service.
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))
from app.muril_predictor import predictor  # noqa: E402


# ---------------------------------------------------------------------------
# Label mapping: dataset labels  →  model class names
# ---------------------------------------------------------------------------
DEPT_MAP = {
    "Public Works Department (PWD)":            "Roads & Transportation",
    "Urban Administration & Development":       "Waste Management",  # most UAD rows are sanitation
    "Energy Department (MPMKVVCL)":             "Electricity",
    "Public Health Engineering (PHED)":         "Water Supply",
    "Public Health & Family Welfare":           "Health & Family Welfare",
    "Revenue Department":                       "Public Safety & Encroachment",
    "Home Department (Police)":                 "Police",
    "Pollution Control Board":                  "Public Safety & Encroachment",
    "Transport Department":                     "RTO / State Transport",
    "School Education Department":              "Education (Higher / School)",
    "Forest Department":                        "Public Safety & Encroachment",
    "Food, Civil Supplies & Consumer Protection": "Public Distribution (PDS)",
}

PRIORITY_MAP = {"high": "High", "medium": "Med", "low": "Low"}

# Your dataset has positive/negative/neutral; model has Distressed/Frustrated/Neutral.
# Negative complaints map to Frustrated by default; rows with high-priority keywords
# would map to Distressed, but we keep this simple — refine if you re-annotate.
SENTIMENT_MAP = {"negative": "Frustrated", "neutral": "Neutral", "positive": "Neutral"}


def map_gold(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["department_gold"]  = df["department"].map(DEPT_MAP).fillna(df["department"])
    df["priority_gold"]    = df["priority"].map(PRIORITY_MAP).fillna(df["priority"])
    df["sentiment_gold"]   = df["sentiment"].map(SENTIMENT_MAP).fillna(df["sentiment"])
    # sub_category — keep raw; we evaluate it only loosely (string contains)
    df["sub_category_gold"] = df["sub_category"].fillna("")
    return df


# ---------------------------------------------------------------------------
# Predict
# ---------------------------------------------------------------------------
def run_inference(texts: list[str]) -> list[dict]:
    if not predictor.ready:
        predictor.load()
    if not predictor.ready:
        raise SystemExit("MuRIL predictor failed to load — check service-classifier/model/")
    preds = []
    n = len(texts)
    for i, t in enumerate(texts):
        if not isinstance(t, str) or not t.strip():
            preds.append(None)
            continue
        preds.append(predictor.predict(t))
        if (i + 1) % 200 == 0 or i + 1 == n:
            print(f"  predicted {i+1}/{n}")
    return preds


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
def score(y_true, y_pred, label: str, top_n: int = 25):
    mask = [yp is not None for yp in y_pred]
    yt = [y for y, m in zip(y_true, mask) if m]
    yp = [y for y, m in zip(y_pred, mask) if m]
    acc = accuracy_score(yt, yp)
    f1m = f1_score(yt, yp, average="macro", zero_division=0)
    f1w = f1_score(yt, yp, average="weighted", zero_division=0)
    print(f"\n{label}:  acc={acc:.4f}  macro-F1={f1m:.4f}  weighted-F1={f1w:.4f}")
    rpt = classification_report(yt, yp, zero_division=0)
    print(rpt)
    return {"accuracy": acc, "macro_f1": f1m, "weighted_f1": f1w}, rpt


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out",  default=os.path.join(HERE, "report"))
    ap.add_argument("--limit", type=int, default=0,
                    help="If >0, evaluate only the first N rows (smoke test)")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    df = pd.read_csv(args.data)
    if args.limit:
        df = df.head(args.limit).copy()
    print(f"loaded {len(df)} rows")
    df = map_gold(df)

    # Use text_normalized as the primary input (matches training).
    texts = df["text_normalized"].fillna("").astype(str).tolist()
    blank = sum(1 for t in texts if not t.strip())
    if blank:
        # Fall back to text_en for blank rows.
        for i, t in enumerate(texts):
            if not t.strip():
                texts[i] = str(df["text_en"].iloc[i] or "")

    print("\nRunning MuRIL inference…")
    preds = run_inference(texts)

    # Flatten predictions into columns.
    df["pred_department"]   = [p["department"]["label"]  if p else None for p in preds]
    df["pred_sub_category"] = [p["sub_category"]["label"] if p else None for p in preds]
    df["pred_priority"]     = [p["priority"]["label"]    if p else None for p in preds]
    df["pred_sentiment"]    = [p["sentiment"]["label"]   if p else None for p in preds]
    df["pred_confidence"]   = [p["department"]["confidence"] if p else None for p in preds]
    df["needs_clarification"] = [p["needs_clarification"] if p else None for p in preds]

    df["match_department"] = df["pred_department"] == df["department_gold"]
    df["match_priority"]   = df["pred_priority"]   == df["priority_gold"]
    df["match_sentiment"]  = df["pred_sentiment"]  == df["sentiment_gold"]

    # Save per-row predictions.
    cols = ["text_en", "department", "department_gold", "pred_department",
            "pred_confidence", "match_department",
            "sub_category", "pred_sub_category",
            "priority", "priority_gold", "pred_priority", "match_priority",
            "sentiment", "sentiment_gold", "pred_sentiment", "match_sentiment",
            "city", "needs_clarification"]
    df[cols].to_csv(os.path.join(args.out, "predictions.csv"), index=False)

    # Scores.
    metrics, rpt_dept = score(df["department_gold"].tolist(),
                              df["pred_department"].tolist(), "DEPARTMENT")
    metrics_p, _ = score(df["priority_gold"].tolist(),
                         df["pred_priority"].tolist(), "PRIORITY")
    metrics_s, _ = score(df["sentiment_gold"].tolist(),
                         df["pred_sentiment"].tolist(), "SENTIMENT")

    with open(os.path.join(args.out, "metrics.json"), "w") as f:
        json.dump({
            "n_rows": int(len(df)),
            "department": metrics,
            "priority":   metrics_p,
            "sentiment":  metrics_s,
            "needs_clarification_rate": float(df["needs_clarification"].mean()),
        }, f, indent=2)

    # Confusion matrix for department.
    labels = sorted(set(df["department_gold"]) | set(p for p in df["pred_department"] if p))
    cm = confusion_matrix(df["department_gold"], df["pred_department"], labels=labels)
    pd.DataFrame(cm, index=labels, columns=labels).to_csv(
        os.path.join(args.out, "confusion_dept.csv"))

    # First 200 department errors (for visual inspection).
    errs = df[~df["match_department"]].head(200)
    errs[["text_en", "department_gold", "pred_department",
          "pred_confidence", "city"]].to_csv(
        os.path.join(args.out, "errors_dept.csv"), index=False)

    print(f"\nArtifacts written to {args.out}/")


if __name__ == "__main__":
    main()
