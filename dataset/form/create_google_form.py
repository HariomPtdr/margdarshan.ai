"""
create_google_form.py
Programmatically creates the Margdarshan.ai complaint-dataset Google Form
using the Google Forms API v1.

Setup (one-time):
  pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

  Then follow the OAuth2 steps printed when you first run this script.
  A browser window will open asking you to authorise your Google account.
  The created form URL is printed at the end.
"""

import json
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/drive.file",
]
TOKEN_FILE = "token.json"
CREDS_FILE = "credentials.json"          # download from Google Cloud Console


def get_credentials() -> Credentials:
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDS_FILE):
                raise FileNotFoundError(
                    f"\n[ERROR] '{CREDS_FILE}' not found.\n"
                    "Steps to get it:\n"
                    "  1. Go to https://console.cloud.google.com/\n"
                    "  2. Create a project → Enable 'Google Forms API' + 'Google Drive API'\n"
                    "  3. OAuth consent screen → External → add your email as test user\n"
                    "  4. Credentials → Create OAuth 2.0 Client ID (Desktop app)\n"
                    "  5. Download JSON → save as credentials.json in this folder\n"
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


# ---------------------------------------------------------------------------
# Form definition
# ---------------------------------------------------------------------------

FORM_TITLE = "Margdarshan.ai — Real-World Complaint Dataset"

DESCRIPTION = (
    "We are building an AI system (Margdarshan.ai) that automatically routes citizen "
    "complaints to the correct government department. To train it on real experiences, "
    "we need actual complaints people have faced.\n\n"
    "⏱ Takes 3–5 minutes  |  🔒 Completely anonymous — no name or contact needed.\n\n"
    "Example complaints (any language works):\n"
    "- Naali mein kachra bhara hua hai aur paani ruk gaya hai, teen hafte se koi nahi aaya.\n"
    "- The ration shop dealer has not given our family wheat quota for 2 months.\n"
    "- Pothole on NH-48 near Toll Plaza 6 has caused two accidents this week.\n"
    "- Sarkari school mein teen mahine se teacher nahi hai, bacche khaali baithe hain.\n\n"
    "You can submit this form multiple times — each separate complaint is valuable!"
)

# Each entry describes one question.
# type: RADIO | CHECKBOX | DROP_DOWN | TEXT | PARAGRAPH_TEXT | LINEAR_SCALE
QUESTIONS = [
    # ── SECTION 1 header ─────────────────────────────────────────────────
    {
        "kind": "section",
        "title": "Section 1 of 5 — The Complaint",
        "description": "Tell us about a real issue you experienced or observed.",
    },
    {
        "title": "Describe the complaint in your own words",
        "type": "PARAGRAPH_TEXT",
        "required": True,
        "help": (
            "Write in Hindi, English, or Hinglish — whichever feels natural. "
            "At least 2–3 sentences work best.\n"
            "Example: 'Hamare mohalle mein 3 hafte se street light band hai. "
            "Raat ko andhera rehta hai aur darr lagta hai.'"
        ),
    },
    {
        "title": "Which language did you use above?",
        "type": "RADIO",
        "required": True,
        "options": [
            "English",
            "Hindi (हिंदी)",
            "Hinglish (Hindi + English mixed)",
            "Other regional language",
        ],
    },
    {
        "title": "How urgent was / is this complaint?",
        "type": "LINEAR_SCALE",
        "required": True,
        "low": 1,
        "high": 5,
        "low_label": "Not urgent at all",
        "high_label": "Extremely urgent / life-safety risk",
    },
    {
        "title": "Main category of this complaint",
        "type": "DROP_DOWN",
        "required": True,
        "options": [
            "Roads & Potholes",
            "Water Supply / Drainage",
            "Electricity / Street Lights",
            "Garbage / Sanitation",
            "Public Health / Hospital",
            "Ration / PDS / Food Supply",
            "Police / Law & Order",
            "Schools / Education",
            "Land / Property Records",
            "Noise / Pollution",
            "Public Transport",
            "Corruption / Bribery",
            "Pension / Social Welfare",
            "Other (specify in next question)",
        ],
    },
    {
        "title": "If 'Other', please specify the category",
        "type": "TEXT",
        "required": False,
        "help": "Leave blank if you selected a category above.",
    },
    {
        "title": "Which government department should handle this?",
        "type": "DROP_DOWN",
        "required": False,
        "help": "Best guess is fine — or choose 'I'm not sure'.",
        "options": [
            "Municipal Corporation (Nagar Nigam / Nagar Palika)",
            "PWD (Public Works Department)",
            "Police",
            "Electricity Board (DISCOM)",
            "Water Board / Jal Board",
            "State Health Department",
            "Food & Civil Supplies (Ration)",
            "Revenue / Tehsildar Office",
            "Education Department",
            "Transport Department",
            "I'm not sure",
        ],
    },
    {
        "title": "Was this complaint filed anywhere officially?",
        "type": "RADIO",
        "required": True,
        "options": [
            "Yes — on a portal (CPGRAMS, Samadhan, CM Helpline, etc.)",
            "Yes — verbally / in person at an office",
            "Yes — via phone helpline (e.g. 1076, 1800 numbers)",
            "No — I didn't know where to file it",
            "No — I didn't think it would be resolved",
        ],
    },
    {
        "title": "If filed, what was the outcome?",
        "type": "RADIO",
        "required": False,
        "help": "Leave blank if you did not file it.",
        "options": [
            "Resolved completely",
            "Partially resolved",
            "Acknowledged but no action taken",
            "Rejected / closed without resolution",
            "Still pending",
        ],
    },

    # ── SECTION 2 header ─────────────────────────────────────────────────
    {
        "kind": "section",
        "title": "Section 2 of 5 — Location",
        "description": "Location helps us train the routing model.",
    },
    {
        "title": "State where this happened",
        "type": "DROP_DOWN",
        "required": True,
        "options": [
            "Uttar Pradesh", "Delhi", "Maharashtra", "Madhya Pradesh",
            "Rajasthan", "Bihar", "West Bengal", "Tamil Nadu",
            "Karnataka", "Gujarat", "Andhra Pradesh", "Telangana",
            "Odisha", "Kerala", "Jharkhand", "Assam",
            "Punjab", "Chhattisgarh", "Haryana", "Uttarakhand",
            "Himachal Pradesh", "Jammu & Kashmir (UT)", "Ladakh (UT)",
            "Goa", "Tripura", "Meghalaya", "Manipur", "Nagaland",
            "Arunachal Pradesh", "Mizoram", "Sikkim",
            "Chandigarh (UT)", "Puducherry (UT)",
            "Dadra & Nagar Haveli and Daman & Diu (UT)",
            "Andaman & Nicobar Islands (UT)",
            "Lakshadweep (UT)",
        ],
    },
    {
        "title": "City / District / Town",
        "type": "TEXT",
        "required": True,
        "help": "e.g. Lucknow, Indore, South Delhi, Patna Sadar",
    },
    {
        "title": "Area / Locality / Ward (if known)",
        "type": "TEXT",
        "required": False,
        "help": "e.g. Sector 21, Gandhi Nagar, near Bus Stand — helps train our location extractor.",
    },
    {
        "title": "Is this an urban or rural area?",
        "type": "RADIO",
        "required": True,
        "options": [
            "Urban (City / Town)",
            "Semi-urban (Small town / Tehsil)",
            "Rural (Village / Gram Panchayat)",
        ],
    },

    # ── SECTION 3 header ─────────────────────────────────────────────────
    {
        "kind": "section",
        "title": "Section 3 of 5 — Complaint Metadata",
        "description": "Quick context questions (all optional).",
    },
    {
        "title": "Approximately how long has this issue been going on?",
        "type": "RADIO",
        "required": False,
        "options": [
            "Just happened / Very recent (less than 1 week)",
            "1–4 weeks",
            "1–3 months",
            "More than 3 months",
            "Recurring / seasonal problem",
        ],
    },
    {
        "title": "How many people are affected?",
        "type": "RADIO",
        "required": False,
        "options": [
            "Just me / my household",
            "My building / a few neighbours",
            "Entire street / colony / ward",
            "Large area — many thousands of people",
        ],
    },
    {
        "title": "Does this complaint involve any of the following? (Select all that apply)",
        "type": "CHECKBOX",
        "required": False,
        "options": [
            "Risk to human life or safety",
            "Corruption or bribery involved",
            "Involves a government official personally",
            "Affects a vulnerable group (elderly, disabled, children)",
            "Environmental damage",
            "None of the above",
        ],
    },

    # ── SECTION 4 header ─────────────────────────────────────────────────
    {
        "kind": "section",
        "title": "Section 4 of 5 — Help Us Label Better",
        "description": "These questions improve dataset quality.",
    },
    {
        "title": "How confident are you in the department you selected?",
        "type": "LINEAR_SCALE",
        "required": False,
        "low": 1,
        "high": 3,
        "low_label": "Not sure",
        "high_label": "Very confident",
        "help": "If you skipped the department question, leave this blank.",
    },
    {
        "title": "(Optional) Write the same complaint in a different language or style",
        "type": "PARAGRAPH_TEXT",
        "required": False,
        "help": (
            "If you wrote in English above, try Hindi — or vice versa. "
            "Even a more formal / more casual version helps us a lot. "
            "This creates paraphrase pairs for better training."
        ),
    },
    {
        "title": "Any additional context?",
        "type": "PARAGRAPH_TEXT",
        "required": False,
        "help": (
            "Anything else — time of day, failed previous attempts, "
            "why it matters to you, what a resolution would look like."
        ),
    },

    # ── SECTION 5 header ─────────────────────────────────────────────────
    {
        "kind": "section",
        "title": "Section 5 of 5 — About You (Fully Optional)",
        "description": "Completely optional. Will NOT be linked to your complaint.",
    },
    {
        "title": "Your general background / role",
        "type": "RADIO",
        "required": False,
        "options": [
            "Student",
            "Working professional",
            "Government employee",
            "Homemaker",
            "Farmer / Daily wage worker",
            "Prefer not to say",
        ],
    },
    {
        "title": "Age group",
        "type": "RADIO",
        "required": False,
        "options": [
            "Under 18",
            "18–25",
            "26–40",
            "41–60",
            "60+",
        ],
    },
]

# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def _text_item(title: str, required: bool, help_text: str, paragraph: bool) -> dict:
    return {
        "createItem": {
            "item": {
                "title": title,
                "description": help_text,
                "questionItem": {
                    "question": {
                        "required": required,
                        "textQuestion": {"paragraph": paragraph},
                    }
                },
            },
            "location": {"index": 0},
        }
    }


def _choice_item(title: str, required: bool, help_text: str,
                 options: list, ctype: str) -> dict:
    return {
        "createItem": {
            "item": {
                "title": title,
                "description": help_text,
                "questionItem": {
                    "question": {
                        "required": required,
                        "choiceQuestion": {
                            "type": ctype,
                            "options": [{"value": o} for o in options],
                            "shuffle": False,
                        },
                    }
                },
            },
            "location": {"index": 0},
        }
    }


def _scale_item(title: str, required: bool, help_text: str,
                low: int, high: int, low_label: str, high_label: str) -> dict:
    return {
        "createItem": {
            "item": {
                "title": title,
                "description": help_text,
                "questionItem": {
                    "question": {
                        "required": required,
                        "scaleQuestion": {
                            "low": low,
                            "high": high,
                            "lowLabel": low_label,
                            "highLabel": high_label,
                        },
                    }
                },
            },
            "location": {"index": 0},
        }
    }


def _section_item(title: str, description: str) -> dict:
    return {
        "createItem": {
            "item": {
                "title": title,
                "description": description,
                "pageBreakItem": {},
            },
            "location": {"index": 0},
        }
    }


def build_requests(questions: list) -> list:
    """Convert our question defs to Google Forms API batchUpdate requests."""
    requests = []
    for q in questions:
        kind = q.get("kind")
        if kind == "section":
            requests.append(_section_item(q["title"], q.get("description", "")))
            continue

        qtype = q["type"]
        title = q["title"]
        required = q.get("required", False)
        help_text = q.get("help", "")

        if qtype == "PARAGRAPH_TEXT":
            requests.append(_text_item(title, required, help_text, paragraph=True))
        elif qtype == "TEXT":
            requests.append(_text_item(title, required, help_text, paragraph=False))
        elif qtype == "LINEAR_SCALE":
            requests.append(_scale_item(
                title, required, help_text,
                q["low"], q["high"], q["low_label"], q["high_label"],
            ))
        elif qtype in ("RADIO", "CHECKBOX", "DROP_DOWN"):
            api_type = {"RADIO": "RADIO", "CHECKBOX": "CHECKBOX", "DROP_DOWN": "DROP_DOWN"}[qtype]
            requests.append(_choice_item(title, required, help_text, q["options"], api_type))

    # The API appends items — reverse so the final order matches our list
    # (each item is inserted at index 0, so we reverse to get correct order)
    requests.reverse()
    return requests


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    creds = get_credentials()
    service = build("forms", "v1", credentials=creds)

    print("Creating form…")
    form_body = {
        "info": {
            "title": FORM_TITLE,
            "documentTitle": FORM_TITLE,
        }
    }
    form = service.forms().create(body=form_body).execute()
    form_id = form["formId"]
    print(f"  Form ID: {form_id}")

    # Set description via batchUpdate
    print("Setting description and quiz-mode off…")
    service.forms().batchUpdate(
        formId=form_id,
        body={
            "requests": [
                {
                    "updateFormInfo": {
                        "info": {"description": DESCRIPTION},
                        "updateMask": "description",
                    }
                }
            ]
        },
    ).execute()

    # Add all questions
    print(f"Adding {len(QUESTIONS)} questions / sections…")
    requests = build_requests(QUESTIONS)

    # Google Forms API accepts max 200 requests per batchUpdate; chunk just in case
    chunk_size = 50
    for i in range(0, len(requests), chunk_size):
        chunk = requests[i : i + chunk_size]
        service.forms().batchUpdate(
            formId=form_id, body={"requests": chunk}
        ).execute()
        print(f"  …batch {i // chunk_size + 1} done ({len(chunk)} requests)")

    form_url = f"https://docs.google.com/forms/d/{form_id}/edit"
    response_url = f"https://docs.google.com/forms/d/{form_id}/viewform"

    print("\n✅ Form created successfully!")
    print(f"   Edit URL  : {form_url}")
    print(f"   Share URL : {response_url}")
    print(f"\n   Share the Share URL with your network to collect responses.")
    print(f"   Responses sheet: open the form → Responses → Link to Sheets")

    # Save URLs locally
    with open("form_urls.json", "w") as f:
        json.dump({"form_id": form_id, "edit_url": form_url, "share_url": response_url}, f, indent=2)
    print("   URLs saved to form_urls.json")


if __name__ == "__main__":
    main()
