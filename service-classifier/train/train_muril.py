"""
MuRIL-based multi-task classifier for grievance complaints.

Trains 4 sklearn classifiers on top of MuRIL CLS embeddings:
  - department     (25 classes)
  - sub_category   (142 classes)
  - sentiment      (3 classes)
  - priority       (4 classes)

Run from repo root:
    python service-classifier/train/train_muril.py \
        --data /path/to/v3_enriched.csv \
        --out  service-classifier/model
"""

import argparse
import json
import os
import pickle
import time
import warnings

import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")

from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import Pipeline
import torch
from transformers import AutoModel, AutoTokenizer

MODEL_NAME = "google/muril-base-cased"
BATCH_SIZE = 32
MAX_LEN = 128  # most complaints fit in 128 tokens; saves memory vs 512

DEPT_CONFIDENCE_THRESHOLD = 0.40  # below this → ask clarifying question


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")

    # Use text_normalized as primary; fall back to text_en
    df["input_text"] = df["text_normalized"].fillna("").str.strip()
    empty = df["input_text"] == ""
    df.loc[empty, "input_text"] = df.loc[empty, "text_en"].fillna("").str.strip()

    # Drop rows missing any required label
    required = ["department", "sub_category", "sentiment", "priority"]
    before = len(df)
    df = df.dropna(subset=required)
    df = df[df[required].apply(lambda c: c.str.strip() != "").all(axis=1)]
    print(f"Dropped {before - len(df)} rows with missing labels. {len(df)} remain.")
    return df.reset_index(drop=True)


def get_muril_embeddings(texts: list[str], tokenizer, model, device: str) -> np.ndarray:
    """Mean-pool over all non-padding tokens — consistently better than CLS for classification."""
    model.eval()
    all_embs = []
    n = len(texts)
    for i in range(0, n, BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        enc = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=MAX_LEN,
            return_tensors="pt",
        ).to(device)
        with torch.no_grad():
            out = model(**enc)
        # Mean pooling: average token embeddings weighted by attention mask
        hidden = out.last_hidden_state  # (B, T, 768)
        mask = enc["attention_mask"].unsqueeze(-1).float()  # (B, T, 1)
        mean_emb = (hidden * mask).sum(dim=1) / mask.sum(dim=1)
        all_embs.append(mean_emb.cpu().numpy())
        if (i // BATCH_SIZE) % 20 == 0:
            pct = 100 * (i + len(batch)) / n
            print(f"  Embedded {i + len(batch):>6}/{n}  ({pct:.1f}%)")
    return np.vstack(all_embs)


def train_classifier(X_train, y_train, X_val, y_val, label: str):
    print(f"\n--- Training {label} ---")
    n_classes = len(set(y_train))
    print(f"  Classes: {n_classes}")

    if n_classes > 30:
        # SGDClassifier with modified_huber: O(n_samples) per epoch, gives
        # calibrated probabilities, handles 100+ classes in seconds.
        clf = Pipeline([
            ("scaler", StandardScaler()),
            ("sgd", SGDClassifier(
                loss="modified_huber",
                alpha=1e-4,
                max_iter=200,
                tol=1e-3,
                n_jobs=-1,
                random_state=42,
                class_weight="balanced",
            )),
        ])
    else:
        clf = Pipeline([
            ("scaler", StandardScaler()),
            ("lr", LogisticRegression(
                max_iter=2000,
                C=1.0,
                solver="saga",
                n_jobs=-1,
                verbose=0,
            )),
        ])

    clf.fit(X_train, y_train)
    preds = clf.predict(X_val)
    f1 = f1_score(y_val, preds, average="weighted")
    print(f"  Val weighted-F1: {f1:.4f}")
    report = classification_report(y_val, preds, zero_division=0)
    print(report)
    return clf, report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", default="service-classifier/model")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    # ── Load data ────────────────────────────────────────────────────────
    df = load_data(args.data)

    # ── Embed (with disk cache so reruns skip model load entirely) ───────
    texts = df["input_text"].tolist()
    cache_path = os.path.join(args.out, "embeddings_cache.npy")
    if os.path.exists(cache_path):
        print(f"\nLoading cached embeddings (skipping MuRIL load)…")
        X = np.load(cache_path)
        print(f"Loaded  shape={X.shape}")
    else:
        print(f"\nLoading MuRIL ({MODEL_NAME})…")
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"Device: {device}")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        muril = AutoModel.from_pretrained(MODEL_NAME).to(device)

        print(f"Embedding {len(texts)} texts (batch={BATCH_SIZE}, max_len={MAX_LEN})…")
        t0 = time.time()
        X = get_muril_embeddings(texts, tokenizer, muril, device)
        print(f"Embedding done in {time.time()-t0:.1f}s  shape={X.shape}")
        np.save(cache_path, X)
        print(f"Embeddings cached → {cache_path}")
        del muril  # free GPU memory

    # ── Encode labels ────────────────────────────────────────────────────
    encoders = {}
    tasks = ["department", "sub_category", "sentiment", "priority"]
    labels = {}
    for task in tasks:
        le = LabelEncoder()
        labels[task] = le.fit_transform(df[task].values)
        encoders[task] = le
        print(f"  {task}: {len(le.classes_)} classes")

    # ── Train / eval split ───────────────────────────────────────────────
    idx = np.arange(len(df))
    idx_tr, idx_val = train_test_split(idx, test_size=0.15, random_state=42,
                                       stratify=labels["department"])
    X_tr, X_val = X[idx_tr], X[idx_val]

    reports = {}
    classifiers = {}
    for task in tasks:
        y_tr = labels[task][idx_tr]
        y_val = labels[task][idx_val]
        clf, report = train_classifier(X_tr, y_tr, X_val, y_val, task)
        classifiers[task] = clf
        reports[task] = report

    # ── Save artifacts ───────────────────────────────────────────────────
    print("\nSaving model artifacts…")
    with open(os.path.join(args.out, "classifiers.pkl"), "wb") as f:
        pickle.dump(classifiers, f)
    with open(os.path.join(args.out, "encoders.pkl"), "wb") as f:
        pickle.dump(encoders, f)

    meta = {
        "muril_model": MODEL_NAME,
        "max_len": MAX_LEN,
        "confidence_threshold": DEPT_CONFIDENCE_THRESHOLD,
        "classes": {task: list(encoders[task].classes_) for task in tasks},
    }
    with open(os.path.join(args.out, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    with open(os.path.join(args.out, "reports.txt"), "w") as f:
        for task, report in reports.items():
            f.write(f"\n{'='*60}\n{task.upper()}\n{'='*60}\n{report}\n")

    print(f"\nAll artifacts saved to: {args.out}/")
    print("  classifiers.pkl  encoders.pkl  meta.json  reports.txt")
    print("\nDone.")


if __name__ == "__main__":
    main()
