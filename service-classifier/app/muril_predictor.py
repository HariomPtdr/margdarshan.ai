"""Loads trained MuRIL + sklearn artifacts and runs inference."""

import json
import logging
import os
import pickle
from typing import Optional

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

logger = logging.getLogger(__name__)

# MODEL_VERSION env var lets us flip between "model" (v1) and "model_v2"
# without code changes — set in docker-compose or shell.
MODEL_DIR = os.path.join(
    os.path.dirname(__file__), "..", os.getenv("MODEL_VERSION", "model")
)


class MuRILPredictor:
    def __init__(self):
        self.ready = False
        self.tokenizer = None
        self.muril = None
        self.classifiers: dict = {}
        self.encoders: dict = {}
        self.scaler = None  # optional — only present in v2+
        self.meta: dict = {}
        self.device = "cpu"

    def load(self):
        meta_path = os.path.join(MODEL_DIR, "meta.json")
        clf_path = os.path.join(MODEL_DIR, "classifiers.pkl")
        enc_path = os.path.join(MODEL_DIR, "encoders.pkl")
        scaler_path = os.path.join(MODEL_DIR, "scaler.pkl")

        if not all(os.path.exists(p) for p in [meta_path, clf_path, enc_path]):
            logger.warning("MuRIL model artifacts not found — falling back to rule-based classifier")
            return

        with open(meta_path) as f:
            self.meta = json.load(f)
        with open(clf_path, "rb") as f:
            self.classifiers = pickle.load(f)
        with open(enc_path, "rb") as f:
            self.encoders = pickle.load(f)
        if os.path.exists(scaler_path):
            with open(scaler_path, "rb") as f:
                self.scaler = pickle.load(f)
            logger.info(f"Loaded StandardScaler from {scaler_path}")

        muril_name = self.meta.get("muril_model", "google/muril-base-cased")
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        logger.info(f"Loading MuRIL ({muril_name}) on {self.device}…")
        self.tokenizer = AutoTokenizer.from_pretrained(muril_name)
        self.muril = AutoModel.from_pretrained(muril_name).to(self.device)
        self.muril.eval()
        self.ready = True
        logger.info("MuRIL predictor ready")

    def _embed(self, text: str) -> np.ndarray:
        max_len = self.meta.get("max_len", 128)
        enc = self.tokenizer(
            [text],
            padding=True,
            truncation=True,
            max_length=max_len,
            return_tensors="pt",
        ).to(self.device)
        with torch.no_grad():
            out = self.muril(**enc)
        # Mean pooling over non-padding tokens (matches training)
        hidden = out.last_hidden_state          # (1, T, 768)
        mask = enc["attention_mask"].unsqueeze(-1).float()
        mean_emb = (hidden * mask).sum(dim=1) / mask.sum(dim=1)
        # Use tolist() to avoid torch-numpy ABI compatibility issues
        return np.array(mean_emb.cpu().float().tolist())

    def predict(self, text: str) -> dict:
        if not self.ready:
            return None  # caller falls back to rule-based

        emb = self._embed(text)
        # v2 models were trained on standard-scaled embeddings; apply the same
        # transform at inference. v1 has no scaler — skip in that case.
        if self.scaler is not None:
            emb = self.scaler.transform(emb).astype(np.float32)
        threshold = self.meta.get("confidence_threshold", 0.40)

        result = {}
        for task in ["department", "sub_category", "sentiment", "priority"]:
            clf = self.classifiers[task]
            le = self.encoders[task]
            proba = clf.predict_proba(emb)[0]
            idx = int(np.argmax(proba))
            confidence = float(proba[idx])
            result[task] = {
                "label": le.classes_[idx],
                "confidence": round(confidence, 4),
                "top3": [
                    {"label": le.classes_[i], "confidence": round(float(proba[i]), 4)}
                    for i in np.argsort(proba)[::-1][:3]
                ],
            }

        # Keyword-based priority override — MuRIL priority model is weak on Hinglish.
        text_lower = text.lower()
        critical_kw = {
            "accident","injury","injured","ghayel","death","died","maut","fire","blast",
            "electrocution","short circuit","electric shock","flood","burst","fata",
            "collapsed","girna","emergency","critical","ambulance","hospital","unconscious",
        }
        high_kw = {
            "urgent","jaldi","abhi","immediately","asap","bahut bura","nahi aa raha",
            "3 din","4 din","5 din","7 din","hafte se","week se","weeks",
            "no supply","no water","no electricity","no power",
        }
        med_kw = {
            "pension","vridha","vidhwa","widow","disability",
            "scholarship","certificate","documents","affidavit","id card",
            "atm","bank account","refund","insurance","complaint registration",
        }
        if any(kw in text_lower for kw in critical_kw):
            result["priority"]["label"] = "Critical"
        elif any(kw in text_lower for kw in high_kw) and result["priority"]["label"] not in ("Critical",):
            result["priority"]["label"] = "High"
        elif any(kw in text_lower for kw in med_kw) and result["priority"]["label"] in ("Low", "High"):
            result["priority"]["label"] = "Med"

        dept_conf = result["department"]["confidence"]
        result["needs_clarification"] = dept_conf < threshold
        result["clarifying_question"] = (
            _make_clarifying_question(result["department"]["top3"])
            if result["needs_clarification"]
            else None
        )
        return result


def _make_clarifying_question(top3: list) -> str:
    labels = [t["label"] for t in top3[:3]]
    opts = " / ".join(labels)
    return (
        f"Aapki samasya kis vibhag se related hai? "
        f"Kya yeh {opts} ke baare mein hai? "
        f"Thodi aur details dijiye taaki sahi jagah bheja ja sake."
    )


predictor = MuRILPredictor()
