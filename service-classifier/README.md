# service-classifier

Stage 3 — multi-head classifier (department, sub-category, priority, sentiment).

**Current:** rule-based stub using NLU domain_hints. Lets the full pipeline demo work.

**Next:** swap `_classify_stub` for fine-tuned MuRIL multi-head model loaded from HuggingFace.

## Endpoint

```
POST /api/v1/classify
  body: { complaint_id, text_normalized, text_for_classifier, domain_hints, keywords, language }
  returns: { department, sub_category, priority, sentiment, confidence, tier3_used }
```
