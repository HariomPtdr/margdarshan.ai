# service-nlu

Stage 2 preprocessing. Cleans messy WhatsApp text, masks PII, extracts keywords and domain hints, builds the input text for the classifier.

Location is **NOT** extracted from text. It comes from the map picker.

## Pieces

- `normalize.py` — Devanagari digits, lowercase, expand abbreviations, strip noise
- `pii.py` — phone, pincode, vehicle, aadhaar, email, consumer-no extraction + masking
- `keywords.py` — domain dictionary (~50 entries × 9 domains) → matched keywords + canonical domain hints

## Endpoint

```
POST /api/v1/process
  body: { complaint_id, text_raw, language_hint? }
  returns: { text_normalized, text_for_classifier, entities, keywords, domain_hints }
```

Publishes `stage_2_nlu` events to Redis.

## Roadmap

- Add IndicNER for PERSON/ORG/INFRASTRUCTURE detection
- Add IndicXlit for Hinglish→Devanagari transliteration (when needed by classifier)
