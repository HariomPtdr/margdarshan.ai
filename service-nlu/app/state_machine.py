"""Backend-controlled State Machine for grievance intake.

States:
  IDLE               - fresh start
  INTENT_DISCOVERY   - showing category menu (category unclear)
  DIAGNOSTIC_Q       - conversational root-cause question (replaces chips menu)
  CONTEXT_SCOPE      - asking scope only if diagnostic didn't capture it
  CLARIFICATION      - one targeted follow-up
  LOCATION_CAPTURE   - waiting for GPS or text address
  FIELD_COLLECTION   - portal form filling (handled in main.py)
  SUBMITTED          - done

LLM used for:
  1. extract_intent()    - detect category from freetext when keywords miss
  2. extract_diagnostic() - extract sub_issue + scope + root_cause from diagnostic answer
  3. extract_field()     - field values during form filling
"""

import logging
import re as _re
from typing import Optional

from .decision_tree import (
    MAIN_CATEGORIES, SUB_ISSUES, SCOPE_NEEDED, SCOPE_OPTIONS,
    NON_LOCATION_ISSUES, CLARIFY_QUESTIONS,
    CATEGORY_KEYWORDS, SUB_ISSUE_KEYWORDS, CATEGORY_NAMES,
)

logger = logging.getLogger(__name__)

# ── Diagnostic questions per category ─────────────────────────────────────────
# One open-ended question that captures: sub_issue + scope + root_cause
# LLM extracts the answer — no numbered menu needed.

DIAGNOSTIC_QUESTIONS = {
    "Electricity": {
        "hinglish": "Theek hai — bijli ki samasya. Kuch batayein:\n- Kya sirf aapke ghar mein bijli gayi hai ya aas-paas sab logon ko bhi? (scope)\n- Aur kya aapko pata hai kyun — jaise area power cut, transformer fault, ya koi aur reason?\n(Agar bill nahi bhara tha toh bhi batayein — hum sahi direction mein help karenge)",
        "en":       "I see — electricity issue. Please tell me:\n- Is it only your house/meter, or has the entire area lost power?\n- Do you know the reason — area power cut, transformer fault, unpaid bill, or something else?",
        "hi":       "समझ गया — बिजली की समस्या। बताइए:\n- क्या सिर्फ आपके घर में बिजली गई है या पूरे इलाके में?\n- और क्या आपको पता है क्यों — जैसे area power cut, transformer fault, या bill का मुद्दा?",
    },
    "Water Supply": {
        "hinglish": "Paani ki samasya samajh aayi. Batayein:\n- Kya paani bilkul band hai ya sirf pressure kam hai?\n- Kya sirf aapke ghar mein hai ya aas-paas bhi log pareshan hain?\n- Aur kaun sa paani — peene ka (nal) ya sewer/sewage ka issue hai?",
        "en":       "Water issue noted. Please tell me:\n- Is water completely stopped or just low pressure?\n- Is it only your house or the entire area?\n- Is it drinking water (tap/pipeline) or a sewage issue?",
        "hi":       "पानी की समस्या समझ आई। बताइए:\n- क्या पानी बिल्कुल बंद है या सिर्फ कम आ रहा है?\n- क्या सिर्फ आपके घर में है या पूरे इलाके में?\n- और पीने का पानी (nal) की समस्या है या drainage/sewer की?",
    },
    "Roads & Transportation": {
        "hinglish": "Sadak/transport samasya samajh aayi. Batayein:\n- Kya issue hai — pothole, drainage overflow, footpath, ya traffic ka?\n- Yeh sadak kahan hai — locality/area ka naam bataein\n- Yeh condition kaafi time se hai ya haal mein hui hai?",
        "en":       "Road/transport issue noted. Please tell me:\n- What is the issue — pothole, drainage, footpath, or traffic?\n- Where is this road — name the locality/area\n- Has this been ongoing or happened recently?",
        "hi":       "सड़क/परिवहन की समस्या। बताइए:\n- क्या समस्या है — गड्ढे, drainage, footpath, या traffic?\n- यह सड़क कहाँ है — locality/area का नाम बताइए\n- यह कब से है?",
    },
    "Waste Management": {
        "hinglish": "Safai/waste management samasya. Batayein:\n- Kya issue hai — garbage collection nahi, noise pollution, air pollution, ya kuch aur?\n- Yeh sirf aapki gali/building mein hai ya poore area mein?\n- Yeh kab se ho raha hai?",
        "en":       "Sanitation/waste issue noted. Please tell me:\n- What exactly — garbage not collected, noise pollution, air/smoke, or something else?\n- Is it your street/building or the entire area?\n- Since when?",
        "hi":       "सफाई/कचरे की समस्या। बताइए:\n- क्या समस्या है — कचरा नहीं उठा, noise pollution, हवा/धुआं, या कुछ और?\n- क्या यह सिर्फ आपकी गली में है या पूरे इलाके में?\n- कब से है?",
    },
    "Health & Family Welfare": {
        "hinglish": "Health ki samasya samajh aayi. Batayein:\n- Kya issue hai — doctor nahi hai, medicine nahi mili, hospital ki service kharab hai, ya ambulance nahi mili?\n- Government hospital/health center ka naam/area bataein\n- Yeh kitne time se ho raha hai?",
        "en":       "Health issue noted. Please tell me:\n- What exactly — doctor absent, medicine unavailable, poor hospital service, or ambulance issue?\n- Name of the government hospital/health center and area\n- Since when?",
        "hi":       "स्वास्थ्य की समस्या। बताइए:\n- क्या समस्या है — डॉक्टर नहीं, दवाई नहीं, अस्पताल सेवा खराब, या ambulance नहीं?\n- सरकारी अस्पताल/health center का नाम और area\n- कब से?",
    },
    "Police": {
        "hinglish": "Police se related samasya. Batayein:\n- Kya issue hai — FIR darj nahi ho rahi, harassment, crime/theft hua, ya police verification mein delay?\n- Kya yeh immediate safety emergency hai? (haan/nahi)\n- Kya aap already thane gaye hain?",
        "en":       "Police-related issue. Please tell me:\n- What exactly — FIR not registered, harassment, crime/theft, or verification delay?\n- Is this an immediate safety emergency? (yes/no)\n- Have you already visited the police station?",
        "hi":       "पुलिस से संबंधित समस्या। बताइए:\n- क्या समस्या है — FIR दर्ज नहीं, harassment, crime/चोरी, या verification में देरी?\n- क्या यह तुरंत safety emergency है? (हां/नहीं)\n- क्या आप थाने जा चुके हैं?",
    },
    "Pension & Pensioners Welfare": {
        "hinglish": "Pension ki samasya. Batayein:\n- Kaunsa pension — old age, widow (vidhwa), disability (viklang), ya government employee pension?\n- Kitne mahine/samay se nahi aaya?\n- Kya pehle pension aa raha tha aur achanak band ho gaya, ya kabhi aaya hi nahi?",
        "en":       "Pension issue noted. Please tell me:\n- Which pension — old age, widow, disability, or government employee?\n- How many months/time since it stopped?\n- Was it coming before and suddenly stopped, or never received?",
        "hi":       "पेंशन की समस्या। बताइए:\n- कौन सा pension — वृद्धावस्था, विधवा, विकलांग, या सरकारी कर्मचारी?\n- कितने महीने/समय से नहीं आया?\n- क्या पहले आता था और अचानक बंद हो गया, या कभी मिला ही नहीं?",
    },
    "Public Distribution (PDS)": {
        "hinglish": "Ration ki samasya. Batayein:\n- Kya issue hai — ration card nahi mila, FPS shop nahi khulti, ration quantity kam hai, ya quality kharab hai?\n- Ration card number hai aapke paas?\n- Yeh kab se ho raha hai?",
        "en":       "Ration/PDS issue noted. Please tell me:\n- What exactly — ration card not received, FPS shop not opening, quantity shortage, or quality issue?\n- Do you have your ration card number?\n- Since when?",
        "hi":       "राशन की समस्या। बताइए:\n- क्या समस्या है — ration card नहीं मिला, FPS shop नहीं खुलती, मात्रा कम है, या quality खराब है?\n- ration card number है?\n- कब से है?",
    },
    "Banking (DFS)": {
        "hinglish": "Banking samasya. Batayein:\n- Kya issue hai — ATM kaam nahi kar raha, account freeze/block hua, cyber fraud hua, loan nahi mila, ya KYC issue?\n- Konsa bank hai aur kahan?\n- Yeh issue kitne time se hai?",
        "en":       "Banking issue noted. Please tell me:\n- What exactly — ATM not working, account blocked, cyber fraud, loan issue, or KYC problem?\n- Which bank and where?\n- Since when?",
        "hi":       "बैंकिंग समस्या। बताइए:\n- क्या समस्या है — ATM काम नहीं, account freeze, cyber fraud, loan issue, या KYC?\n- कौन सा bank और कहाँ?\n- कब से है?",
    },
}

# For categories without a specific diagnostic question, use generic
GENERIC_DIAGNOSTIC = {
    "hinglish": "Samasya samajh aayi. Thodi aur detail batayein:\n- Exactly kya problem hai?\n- Yeh kitne time se chal raha hai?\n- Pehle koi action liya tha is par?",
    "en":       "Issue noted. Please provide more detail:\n- What exactly is the problem?\n- Since how long has this been happening?\n- Have you taken any action on this before?",
    "hi":       "समस्या समझ आई। थोड़ी और detail बताइए:\n- बिल्कुल क्या समस्या है?\n- यह कितने समय से चल रहा है?\n- क्या पहले कोई action लिया था?",
}

# Redirect messages for "not a complaint" scenarios
NOT_COMPLAINT_REDIRECT = {
    "bill_not_paid": {
        "hinglish": "Agar supply bill non-payment ke kaaran band ki gayi hai, toh yeh shikayat mein nahi aata. Bill bharne ke baad supply resume ho jaayegi.\n\nKya aapko bill ki amount mein koi gadbadi lag rahi hai ya overcharging ki shikayat deni hai?",
        "en":       "If supply is disconnected due to non-payment, this is not a grievance. Paying the bill will restore supply.\n\nDo you have an issue with the bill amount or overcharging?",
        "hi":       "अगर supply bill न भरने के कारण बंद की गई है, तो यह शिकायत में नहीं आता। Bill भरने के बाद supply resume हो जाएगी।\n\nक्या आपको bill की amount में कोई गड़बड़ी लग रही है या overcharging की शिकायत देनी है?",
    },
}

# ── Multilingual templates ─────────────────────────────────────────────────────

_T = {
    "greeting": {
        "en":       "Hello! I'm Shikayat Saathi, your government complaint assistant. What is your issue?",
        "hi":       "नमस्ते! मैं शिकायत साथी हूँ — सरकारी शिकायत दर्ज करने में आपकी मदद करूँगा। आपकी क्या समस्या है?",
        "hinglish": "Namaste! Main Shikayat Saathi hoon — aapki sarkari shikayat darj karne mein madad karunga. Aapki kya samasya hai?",
    },
    "ask_category": {
        "en":       "Please select the type of complaint:",
        "hi":       "कृपया शिकायत का प्रकार चुनें:",
        "hinglish": "Kripya shikayat ka prakar chunein:",
    },
    "ask_location_gps": {
        "en":       "Got it! Please pin your location on the map below, or type your area/address.",
        "hi":       "समझ गया! नीचे मैप पर अपनी location pin करें, या अपना एरिया/पता टाइप करें।",
        "hinglish": "Theek hai! Neeche map par apni location pin karein, ya apna area/address type karein.",
    },
    "ask_location_text": {
        "en":       "Got it! Please type your area and city (e.g. 'Vijay Nagar, Indore').",
        "hi":       "समझ गया! अपना एरिया और शहर बताएं (जैसे 'विजय नगर, इंदौर')।",
        "hinglish": "Theek hai! Apna area aur shahar batayein (jaise 'Vijay Nagar, Indore').",
    },
    "pipeline_ready": {
        "en":       "All details noted. Your complaint is being processed now...",
        "hi":       "सारी जानकारी मिल गई। आपकी शिकायत अभी process हो रही है...",
        "hinglish": "Saari jankari mil gayi. Aapki shikayat abhi process ho rahi hai...",
    },
    "invalid_option": {
        "en":       "Please enter a number from the list, or describe your issue.",
        "hi":       "सूची में से नंबर चुनें या अपनी समस्या बताएं।",
        "hinglish": "List mein se number chunein ya apni samasya batayein.",
    },
    "ask_scope_prefix": {
        "en":       "Is this issue affecting:",
        "hi":       "यह समस्या किसे प्रभावित कर रही है:",
        "hinglish": "Yeh samasya kitne logon ko affect kar rahi hai:",
    },
    "multi_domain_ask": {
        "en":       "I see you have multiple issues — {domains}. We can only file one complaint at a time.\n\nWhich one would you like to file FIRST?",
        "hi":       "आपने कई समस्याएं बताई हैं — {domains}। हम एक समय में एक शिकायत दर्ज कर सकते हैं।\n\nपहले कौन सी शिकायत दर्ज करनी है?",
        "hinglish": "Aapne kai samasya bataayi hain — {domains}. Hum ek baar mein ek shikayat darj kar sakte hain.\n\nPehle kaunsi shikayat darj karni hai?",
    },
    "multi_domain_reminder": {
        "en":       "✅ Your {filed} complaint has been filed (Ticket: {ticket}).\n\nYou also mentioned a {pending} issue earlier. Please click 'New Complaint' to file that separately.",
        "hi":       "✅ आपकी {filed} शिकायत दर्ज हो गई (Ticket: {ticket})।\n\nआपने {pending} की समस्या भी बताई थी। कृपया उसे अलग से 'New Complaint' से दर्ज करें।",
        "hinglish": "✅ Aapki {filed} shikayat darj ho gayi (Ticket: {ticket}).\n\nAapne {pending} ki samasya bhi bataayi thi. Kripya 'New Complaint' se use alag darj karein.",
    },
}


def _t(key: str, lang: str, **kwargs) -> str:
    tmpl = _T.get(key, {}).get(lang) or _T.get(key, {}).get("hinglish", "")
    return tmpl.format(**kwargs) if kwargs else tmpl


def _numbered_list(options: list) -> str:
    return "\n".join(f"{i+1}. {label}" for i, (_, label) in enumerate(options))


def _extract_duration(text: str) -> Optional[str]:
    """Extract duration phrases from text — e.g. '3 din se', '2 days', '1 hafte se'."""
    patterns = [
        r'\d+\s*(?:din|day|days|hafte|week|weeks|mahine|month|months|ghante|hour|hours)\s*(?:se|from|ago|since)?',
        r'(?:kaafi|bahut|kafi)\s*(?:din|time|samay|dino)\s*(?:se)?',
        r'(?:kal|yesterday|parso)\s*(?:se)?',
        r'(?:1|2|3|4|5|6|7|8|9|10)\s*(?:se)',
    ]
    tl = text.lower()
    for p in patterns:
        m = _re.search(p, tl)
        if m:
            return m.group(0).strip()
    return None


def _parse_number(text: str, options: list) -> Optional[tuple]:
    stripped = text.strip()
    if stripped.isdigit():
        idx = int(stripped) - 1
        if 0 <= idx < len(options):
            return options[idx]
    return None


def _detect_category(text: str) -> Optional[str]:
    tl = text.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if _re.search(r'\b' + _re.escape(kw) + r'\b', tl) if ' ' not in kw else kw in tl:
                return cat
    return None


def _detect_all_categories(text: str) -> list[str]:
    """Return ALL categories detected in text — for multi-domain complaint detection."""
    import re as _re2
    tl = text.lower()
    found = []
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            matched = _re2.search(r'\b' + _re2.escape(kw) + r'\b', tl) if ' ' not in kw else kw in tl
            if matched:
                if cat not in found:
                    found.append(cat)
                break
    return found


def _detect_sub_issue(text: str, category: str) -> Optional[str]:
    tl = text.lower()
    for code, _label in SUB_ISSUES.get(category, []):
        for kw in SUB_ISSUE_KEYWORDS.get(code, []):
            if kw in tl:
                return code
    return None


def _detect_scope(text: str) -> Optional[str]:
    tl = text.lower()
    if any(w in tl for w in ["sirf ghar", "only house", "mera ghar", "meri dukaan", "my house", "apna ghar"]):
        return "HOUSE"
    if any(w in tl for w in ["building", "colony", "society", "block", "apna area"]):
        return "BUILDING"
    if any(w in tl for w in ["poora area", "poore area", "sabki", "sab logon", "entire area",
                              "mohalla", "ward", "locality", "aas paas bhi", "aas-paas bhi"]):
        return "AREA"
    return None


def _detect_not_complaint(text: str, category: str) -> Optional[str]:
    """Detect when user reveals this isn't actually a grievance."""
    tl = text.lower()
    if category == "Electricity":
        if any(w in tl for w in ["bill nahi bhara", "bill pay nahi", "non-payment", "bill nahi diya",
                                  "unpaid bill", "payment nahi ki", "baki hai bill"]):
            return "bill_not_paid"
    return None


class StateMachine:
    """
    Conversation State Machine — Layer 2.

    Flow:
      IDLE → (category detected) → DIAGNOSTIC_Q (open-ended root-cause question)
           → (extract sub_issue + scope + root_cause from answer via LLU)
           → (location needed?) → LOCATION_CAPTURE
           → DONE (pass to Layer 3+4)

    The key improvement: instead of showing numbered chip menus for sub-issues,
    we ask one diagnostic open-ended question per category. LLM extracts the answer.
    This handles edge cases like "bill not paid" naturally.
    """

    def __init__(self, nlu_extract_fn):
        self._nlu = nlu_extract_fn

    async def process(self, session, user_message: str) -> dict:
        lang = session.language_preference or "hinglish"
        state = session.state

        if not hasattr(session, 'slots') or session.slots is None:
            session.slots = {}

        slots = session.slots
        slots.setdefault("raw_inputs", [])
        slots["raw_inputs"].append(user_message)

        if state == "IDLE":
            return await self._idle(session, user_message, lang, slots)
        elif state == "INTENT_DISCOVERY":
            return await self._intent_discovery(session, user_message, lang, slots)
        elif state == "DIAGNOSTIC_Q":
            return await self._diagnostic_answer(session, user_message, lang, slots)
        elif state == "CONTEXT_SCOPE":
            return await self._context_scope(session, user_message, lang, slots)
        elif state == "CLARIFICATION":
            return await self._clarification(session, user_message, lang, slots)
        elif state == "LOCATION_CAPTURE":
            return await self._location_capture(session, user_message, lang, slots)
        elif state == "MULTI_DOMAIN_PICK":
            return await self._multi_domain_pick(session, user_message, lang, slots)
        else:
            session.state = "IDLE"
            return self._mk(session, _t("greeting", lang))

    # ── State handlers ──────────────────────────────────────────────────────────

    async def _idle(self, session, message, lang, slots):
        # ── Multi-domain detection ────────────────────────────────────────────
        all_categories = _detect_all_categories(message)
        if len(all_categories) >= 2:
            # Multiple issues mentioned — ask user to pick one for this complaint
            cat_names = [CATEGORY_NAMES.get(c, {}).get(lang, c) for c in all_categories]
            slots["pending_domains"] = all_categories[1:]  # save the rest for reminder
            domain_str = " / ".join(cat_names)
            # Show only the detected categories as options
            detected_options = [(c, CATEGORY_NAMES.get(c, {}).get("en", c) + " / " + CATEGORY_NAMES.get(c, {}).get("hinglish", c)) for c in all_categories]
            opts = _numbered_list(detected_options)
            reply = f"{_t('multi_domain_ask', lang, domains=domain_str)}\n\n{opts}"
            session.state = "MULTI_DOMAIN_PICK"
            slots["multi_domain_options"] = all_categories
            return self._mk(session, reply)

        category = _detect_category(message)

        if not category:
            try:
                extracted = await self._nlu(message, lang)
                lang_det = extracted.get("language") or lang
                session.language_preference = lang_det
                lang = lang_det
                category = extracted.get("category") or None
                if extracted.get("sub_issue"):
                    slots["sub_issue"] = extracted["sub_issue"]
                if extracted.get("location_text"):
                    slots["location_text"] = extracted["location_text"]
                if extracted.get("duration"):
                    slots["duration"] = extracted["duration"]
            except Exception as e:
                logger.warning("NLU extraction failed: %s", e)

        if category:
            slots["category"] = category
            # Check if initial message already has sub_issue and scope
            sub = _detect_sub_issue(message, category) or slots.get("sub_issue")
            scope = _detect_scope(message) or slots.get("scope")
            if sub: slots["sub_issue"] = sub
            if scope: slots["scope"] = scope
            # Extract duration from initial message so clarification can be skipped
            if not slots.get("duration"):
                dur = _extract_duration(message)
                if dur: slots["duration"] = dur

            # Check "not a complaint" signals in initial message
            nc = _detect_not_complaint(message, category)
            if nc:
                redir = NOT_COMPLAINT_REDIRECT.get(nc, {}).get(lang) or NOT_COMPLAINT_REDIRECT.get(nc, {}).get("hinglish", "")
                slots["redirected"] = nc
                return self._mk(session, redir, state="DIAGNOSTIC_Q")

            # If we already have sub_issue + scope from initial message, skip diagnostic
            if sub and scope:
                return await self._after_diagnostic(session, lang, slots)

            # Ask the diagnostic question
            return self._ask_diagnostic(session, lang, slots, category)
        else:
            # Category unclear — show category menu
            session.state = "INTENT_DISCOVERY"
            opts = _numbered_list(MAIN_CATEGORIES)
            reply = f"{_t('greeting', lang)}\n\n{_t('ask_category', lang)}\n{opts}"
            return self._mk(session, reply)

    def _ask_diagnostic(self, session, lang, slots, category):
        """Ask the category-specific diagnostic question."""
        diag = DIAGNOSTIC_QUESTIONS.get(category, GENERIC_DIAGNOSTIC)
        question = diag.get(lang) or diag.get("hinglish", "")
        return self._mk(session, question, state="DIAGNOSTIC_Q")

    async def _multi_domain_pick(self, session, message, lang, slots):
        """User is picking which of the multi-domain complaints to file first."""
        options = slots.get("multi_domain_options", [])
        detected = [(c, CATEGORY_NAMES.get(c, {}).get("en", c) + " / " + CATEGORY_NAMES.get(c, {}).get("hinglish", c)) for c in options]

        chosen = None

        # Try number selection
        sel = _parse_number(message, detected)
        if sel:
            chosen = sel[0]

        if not chosen:
            # Try keyword detection
            for cat in options:
                kws = CATEGORY_KEYWORDS.get(cat, [])
                if any(kw in message.lower() for kw in kws):
                    chosen = cat
                    break

        if chosen:
            slots["pending_domains"] = [c for c in options if c != chosen]
            slots["category"] = chosen
            # Proceed to diagnostic question for chosen category
            return self._ask_diagnostic(session, lang, slots, chosen)

        # Ask again
        opts = _numbered_list(detected)
        domain_str = " / ".join(CATEGORY_NAMES.get(c, {}).get(lang, c) for c in options)
        reply = f"{_t('multi_domain_ask', lang, domains=domain_str)}\n\n{opts}"
        return self._mk(session, reply, state="MULTI_DOMAIN_PICK")

    async def _intent_discovery(self, session, message, lang, slots):
        sel = _parse_number(message, MAIN_CATEGORIES)
        if sel:
            slots["category"] = sel[0]
            return self._ask_diagnostic(session, lang, slots, sel[0])

        category = _detect_category(message)
        if category:
            slots["category"] = category
            sub = _detect_sub_issue(message, category)
            if sub: slots["sub_issue"] = sub
            return self._ask_diagnostic(session, lang, slots, category)

        try:
            extracted = await self._nlu(message, lang)
            category = extracted.get("category")
            if category:
                slots["category"] = category
                return self._ask_diagnostic(session, lang, slots, category)
        except Exception:
            pass

        opts = _numbered_list(MAIN_CATEGORIES)
        reply = f"{_t('invalid_option', lang)}\n\n{_t('ask_category', lang)}\n{opts}"
        return self._mk(session, reply, state="INTENT_DISCOVERY")

    async def _diagnostic_answer(self, session, message, lang, slots):
        """Process user's answer to the diagnostic question.

        LLM extracts: sub_issue, scope, duration, root_cause, location_text.
        Also detects "not a complaint" signals and re-categorizes if needed.
        """
        category = slots.get("category", "OTHER")

        # Re-categorize if user's answer clearly belongs to a different category.
        # e.g. If category=Roads but answer mentions "gaana", "shor", "music" → Waste Management
        new_category = _detect_category(message)
        if new_category and new_category != category:
            # Only switch if the new detection is confident (has a specific keyword match)
            logger.info("Re-categorizing from %s to %s based on answer: %s", category, new_category, message[:50])
            slots["category"] = new_category
            slots["sub_issue"] = None  # reset sub_issue for new category
            category = new_category
            return self._ask_diagnostic(session, lang, slots, category)

        # Check "not a complaint" in the answer
        nc = _detect_not_complaint(message, category)
        if nc and not slots.get("redirected"):
            redir = NOT_COMPLAINT_REDIRECT.get(nc, {}).get(lang) or NOT_COMPLAINT_REDIRECT.get(nc, {}).get("hinglish", "")
            slots["redirected"] = nc
            # Stay in DIAGNOSTIC_Q so user can respond to the redirect
            return self._mk(session, redir, state="DIAGNOSTIC_Q")

        # Fast extraction from keywords
        sub = slots.get("sub_issue") or _detect_sub_issue(message, category)
        scope = slots.get("scope") or _detect_scope(message)

        # LLM extraction for what keywords miss
        try:
            extracted = await self._nlu(message, lang)
            if not sub and extracted.get("sub_issue"):
                sub = extracted["sub_issue"]
            if not scope and extracted.get("scope"):
                scope = extracted["scope"]
            if extracted.get("duration") and not slots.get("duration"):
                slots["duration"] = extracted["duration"]
            if extracted.get("location_text") and not slots.get("location_text"):
                slots["location_text"] = extracted["location_text"]
        except Exception as e:
            logger.warning("diagnostic LLM extraction failed: %s", e)

        # Accept free-text if meaningful — use as custom description
        if not sub and len(message.split()) >= 3:
            sub = "GENERAL"
            slots["custom_description"] = message

        if sub:
            slots["sub_issue"] = sub
        if scope:
            slots["scope"] = scope

        return await self._after_diagnostic(session, lang, slots)

    async def _after_diagnostic(self, session, lang, slots):
        """After diagnostic answer — decide next step."""
        sub_issue = slots.get("sub_issue", "")

        # Need scope but didn't capture from diagnostic answer?
        if sub_issue in SCOPE_NEEDED and not slots.get("scope"):
            opts = _numbered_list(SCOPE_OPTIONS)
            reply = f"{_t('ask_scope_prefix', lang)}\n\n{opts}"
            return self._mk(session, reply, state="CONTEXT_SCOPE")

        # Ask one clarifying question if configured
        return await self._after_scope(session, lang, slots)

    async def _context_scope(self, session, message, lang, slots):
        sel = _parse_number(message, SCOPE_OPTIONS)
        if sel:
            slots["scope"] = sel[0]
            return await self._after_scope(session, lang, slots)

        ml = message.lower()
        if any(w in ml for w in ["house", "ghar", "sirf", "only", "mera", "apna"]):
            slots["scope"] = "HOUSE"
        elif any(w in ml for w in ["building", "colony", "society", "block"]):
            slots["scope"] = "BUILDING"
        elif any(w in ml for w in ["area", "mohalla", "ward", "locality", "poora", "sabka", "sab"]):
            slots["scope"] = "AREA"

        if slots.get("scope"):
            return await self._after_scope(session, lang, slots)

        opts = _numbered_list(SCOPE_OPTIONS)
        return self._mk(session, f"{_t('ask_scope_prefix', lang)}\n\n{opts}", state="CONTEXT_SCOPE")

    async def _after_scope(self, session, lang, slots):
        category = slots.get("category", "OTHER")
        clarify_qs = CLARIFY_QUESTIONS.get(category, [])
        asked = slots.get("clarify_asked", [])

        for q_key, q_text in clarify_qs:
            if q_key not in asked and not slots.get("duration"):  # skip duration if already captured
                asked.append(q_key)
                slots["clarify_asked"] = asked
                return self._mk(session, q_text, state="CLARIFICATION")

        return await self._ask_location(session, lang, slots)

    async def _clarification(self, session, message, lang, slots):
        slots.setdefault("clarify_answers", [])
        slots["clarify_answers"].append(message)
        # Extract duration from clarification if not already captured
        if not slots.get("duration"):
            slots["duration"] = message
        return await self._ask_location(session, lang, slots)

    async def _ask_location(self, session, lang, slots):
        sub_issue = slots.get("sub_issue", "")
        if sub_issue in NON_LOCATION_ISSUES:
            return self._mk(session, _t("ask_location_text", lang),
                            state="LOCATION_CAPTURE", needs_location_pin=False)
        else:
            description = _build_description(slots)
            session.complaint_buffer = description
            slots["gps_triggered"] = True
            return self._mk(
                session, _t("ask_location_gps", lang),
                state="LOCATION_CAPTURE",
                needs_location_pin=True,
                ready_for_pipeline=True,
                is_new_complaint=True,
            )

    async def _location_capture(self, session, message, lang, slots):
        skip_words = {"skip", "na", "nahi", "no", "n/a", "pata nahi", "nahi pata", "-"}
        if message.strip().lower() not in skip_words:
            slots["location_text"] = message.strip()

        if slots.get("gps_triggered"):
            session.complaint_buffer = _build_description(slots)
            return self._mk(session, _t("pipeline_ready", lang), state="COLLECTING")

        return self._trigger_pipeline(session, lang, slots)

    def _trigger_pipeline(self, session, lang, slots) -> dict:
        description = _build_description(slots)
        session.complaint_buffer = description
        return self._mk(
            session, _t("pipeline_ready", lang),
            state="COLLECTING",
            needs_location_pin=False,
            ready_for_pipeline=True,
            is_new_complaint=True,
        )

    def _mk(self, session, reply, state=None, needs_location_pin=False,
            ready_for_pipeline=False, is_new_complaint=False) -> dict:
        if state:
            session.state = state
        return {
            "reply": reply,
            "state": session.state,
            "needs_location_pin": needs_location_pin,
            "ready_for_pipeline": ready_for_pipeline,
            "is_new_complaint": is_new_complaint,
        }


def _build_description(slots: dict) -> str:
    """Build a clean, human-readable grievance description.

    Example output: "Low water pressure in entire area for 2 days. Location: Vijay Nagar, Indore."
    """
    category = slots.get("category", "")
    sub_issue = slots.get("sub_issue", "")
    scope = slots.get("scope", "")
    location = slots.get("location_text", "")
    duration = slots.get("duration", "")
    custom_desc = slots.get("custom_description", "")
    answers = slots.get("clarify_answers", [])

    # Resolve human-readable sub-issue label
    sub_label = ""
    for code, label in SUB_ISSUES.get(category, []):
        if code == sub_issue:
            sub_label = label
            break

    # Scope in plain English
    scope_phrase = {
        "HOUSE":    "in my house/premises",
        "BUILDING": "in our building/society",
        "AREA":     "in the entire area/colony",
    }.get(scope, "")

    # Build the main sentence
    # e.g. "Low water pressure in entire area/colony for 2 days"
    main = custom_desc or sub_label or category
    sentence_parts = [main]

    if scope_phrase:
        sentence_parts.append(scope_phrase)

    if duration:
        # Clean up duration — remove menu selections (single digits)
        clean_dur = duration.strip()
        if clean_dur and not clean_dur.isdigit():
            sentence_parts.append(f"for {clean_dur}")

    description = " ".join(sentence_parts).strip()
    if description:
        description = description[0].upper() + description[1:]

    # Add location on a new line
    if location and not location.strip().isdigit():
        description += f". Location: {location}"

    # Add clarification answers that aren't already captured as duration
    meaningful_answers = [
        a for a in answers
        if len(a) > 2 and not a.strip().isdigit() and a != duration
    ]
    if meaningful_answers:
        description += ". " + "; ".join(meaningful_answers)

    # Classifier-friendly prefix for Layer 3/4 processing
    clf_prefix = f"[{category}]" if category else ""

    return f"{clf_prefix} {description}".strip()
