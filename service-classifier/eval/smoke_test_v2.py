"""End-to-end smoke test for service-classifier model_v2.

Loads v2 artifacts directly (no FastAPI service needed), predicts on a small
set of representative complaints in English / Hindi / Hinglish, and prints
predictions with confidence + top-3 for each head.

Usage:
    cd /Users/hariom/Desktop/grievance-system
    source .venv/bin/activate
    MODEL_VERSION=model_v2 python service-classifier/eval/smoke_test_v2.py
"""
import os
import sys
import json
import pickle
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(HERE, "..", os.getenv("MODEL_VERSION", "model_v2"))
MODEL_DIR = os.path.abspath(MODEL_DIR)
print(f"using MODEL_DIR = {MODEL_DIR}")

# --- Load artifacts ---
with open(os.path.join(MODEL_DIR, "meta.json")) as f:        meta = json.load(f)
with open(os.path.join(MODEL_DIR, "classifiers.pkl"), "rb") as f: clfs = pickle.load(f)
with open(os.path.join(MODEL_DIR, "encoders.pkl"),    "rb") as f: encs = pickle.load(f)
scaler_path = os.path.join(MODEL_DIR, "scaler.pkl")
scaler = None
if os.path.exists(scaler_path):
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    print("loaded scaler.pkl (v2)")
else:
    print("no scaler.pkl — running in v1 mode")

print(f"trained_on: {meta.get('trained_on')}")
print(f"classifier: {meta.get('classifier')}")
print(f"train rows: {meta.get('train_rows')}")

DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"device: {DEVICE}\n")
tok = AutoTokenizer.from_pretrained(meta["muril_model"])
mod = AutoModel.from_pretrained(meta["muril_model"]).to(DEVICE).eval()
MAX_LEN = meta.get("max_len", 128)


def embed(text: str) -> np.ndarray:
    enc = tok([text], padding=True, truncation=True, max_length=MAX_LEN,
              return_tensors="pt").to(DEVICE)
    with torch.no_grad():
        h = mod(**enc).last_hidden_state
    m = enc["attention_mask"].unsqueeze(-1).float()
    e = ((h * m).sum(1) / m.sum(1)).cpu().numpy()
    if scaler is not None:
        e = scaler.transform(e).astype(np.float32)
    return e


def predict(text: str) -> dict:
    e = embed(text)
    out = {}
    for task in ["department", "sub_category", "priority", "sentiment"]:
        p = clfs[task].predict_proba(e)[0]
        order = np.argsort(p)[::-1][:3]
        out[task] = {
            "label": encs[task].classes_[int(order[0])],
            "conf":  float(p[order[0]]),
            "top3":  [(encs[task].classes_[int(i)], round(float(p[i]), 3)) for i in order],
        }
    return out


# --- Representative complaints across languages + domains ---
TESTS = [
    # Civic — should be strong (eligible departments)
    ("EN civic — water",
     "No water supply in our colony for the past 5 days. Tanker also not coming. "
     "Children and elderly suffering in Bhopal."),
    ("HI civic — roads",
     "हमारी गली में बहुत बड़ा गड्ढा है। बारिश के बाद पानी भर जाता है और दुर्घटनाएं हो रही हैं। "
     "जल्दी मरम्मत कराइए।"),
    ("HING civic — electricity",
     "Bijli 3 din se nahi aa rahi hai. Transformer fata hua hai. MPMKVVCL ke complaint number "
     "pe koi response nahi mil raha. Indore, Vijay Nagar."),
    ("EN civic — garbage",
     "Garbage has been piling up at the corner of our street for over a week. Nagar Nigam "
     "trucks are not coming. Bad smell, stray dogs everywhere. Gwalior."),

    # Rare/synthetic-trained — should still classify correctly via memorized templates
    ("EN rare — pension",
     "My pension of Rs. 8000 has not been credited for 4 months. I am a senior citizen of "
     "Bhopal, dependent on this for medicines. Life certificate already submitted."),
    ("HING rare — PM-Kisan",
     "PM-Kisan ki kisht 3 mahine se nahi aayi. Main Sagar ke paas kisan hu. Aadhaar bank "
     "account se link hai aur eKYC bhi ho chuki hai."),
    ("EN rare — GST",
     "GSTR-3B filing failed with portal error for 10 days. Penalty notice issued though "
     "I tried multiple times. Small business in Indore."),

    # Edge cases
    ("HING critical — fire/electrocution",
     "Live wire gir gaya hai hamare ghar ke saamne. Bachcha touch karke ghayel ho gaya. "
     "Ambulance aur MPMKVVCL emergency response chahiye, Khandwa."),
    ("EN short complaint",
     "Streetlight not working near my house for 2 weeks."),
]

print(f"{'='*78}\nSMOKE TEST — {len(TESTS)} complaints\n{'='*78}")
for label, text in TESTS:
    print(f"\n── {label} ──")
    print(f"text: {text[:140]}{'…' if len(text)>140 else ''}")
    r = predict(text)
    for task, v in r.items():
        top3str = "  ".join([f"{lbl}({c:.2f})" for lbl, c in v["top3"]])
        print(f"  {task:14s}  {v['label']:38s}  conf={v['conf']:.3f}  | top3: {top3str}")
print(f"\n{'='*78}\nSMOKE TEST DONE\n{'='*78}")
