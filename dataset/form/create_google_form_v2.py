"""
create_google_form_v2.py  —  Margdarshan.ai dataset form (single page, focused fields)
Run:  source venv/bin/activate && python create_google_form_v2.py
"""

import json, os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES     = ["https://www.googleapis.com/auth/forms.body",
              "https://www.googleapis.com/auth/drive.file"]
TOKEN_FILE = "token.json"
CREDS_FILE = "credentials.json"

# ── Auth ──────────────────────────────────────────────────────────────────────
def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds

# ── Data ──────────────────────────────────────────────────────────────────────
FORM_TITLE = "Margdarshan.ai — Complaint Dataset"

DESCRIPTION = (
    "Help us build an AI that routes citizen complaints automatically. "
    "Share a real complaint you faced or observed — in Hindi, English, or Hinglish.\n"
    "Takes ~2 minutes. Fully anonymous.\n\n"
    "Examples:\n"
    "- Mere ghar mein pichhle 3 din se paani nahi aa raha, municipality se koi response nahi.\n"
    "- My Aadhaar linking with ration card has been pending for 4 months.\n"
    "- Train was 6 hours late and no announcement was made at the station."
)

DEPARTMENTS = [
    "Aadhaar (UIDAI)", "Agriculture & Farmers Welfare", "Banking (DFS)",
    "Consumer Affairs", "Education (Higher / School)", "Electricity", "EPFO",
    "GST (CBIC)", "Health & Family Welfare", "Housing & Urban Affairs",
    "Income Tax (CBDT)", "Insurance (DFS)", "Passport (MEA)",
    "Pension & Pensioners Welfare", "Petroleum & LPG", "Police", "Postal",
    "Public Distribution (PDS)", "Public Safety & Encroachment", "Railways",
    "Roads & Transportation", "RTO / State Transport", "Telecom",
    "Waste Management", "Water Supply",
]

SUB_CATEGORIES = [
    "Aadhaar Linking", "Aadhaar Seeding", "Account Frozen", "Account Reactivation",
    "Account Transfer", "Address Change", "Ambulance Delay", "Animal & Organic Waste",
    "Arrears Payment", "ATM Failure", "Ayushman PMJAY", "Bill Discrepancy",
    "Bill Dispute", "Biometric Lock", "Birth Certificate", "Broadband Outage",
    "Building Plan Approval", "Cancellation", "CGHS Reimbursement", "Challan Dispute",
    "Coach Cleanliness", "Counterfeit Product", "Cyber Fraud", "Cylinder Defect",
    "Disability Pension", "Distributor Service", "DOB Correction", "Domestic Issue",
    "Drainage & Sewage", "Driving Licence", "E-commerce Refund", "Employer Default",
    "Examination Result", "Fair Price Shop", "Family Pension", "Filing Issue",
    "FIR Registration", "Fire Safety", "Footpaths & Pedestrian Infrastructure",
    "Form 26AS Discrepancy", "Garbage Collection", "Garbage Dumping & Black Spots",
    "Health Insurance", "Hospital Service", "Input Tax Credit", "KCC Loan",
    "KYC Update", "Lake & Public Space Encroachment", "Land & Property Encroachment",
    "Learner's Licence", "LIC Claim", "Loan Disbursement", "Lost Card",
    "Lost Document", "Lost Parcel", "Lost Passport", "Mandi Procurement",
    "Medical Negligence", "Meter Reading", "Mid-day Meal", "Misleading Ad",
    "Mobile Linking", "Mobile Number Portability", "Money Order",
    "Mosquito & Pest Control", "Name Correction", "New Connection", "New Issue Delay",
    "NFSA Eligibility", "No Water Supply", "Notice Dispute", "Pension Credit",
    "Pension Disbursal", "Pension EPS-95", "Permit", "Pipeline Burst",
    "PM SVANidhi", "PM-Kisan Payment", "PMAY Application", "PMFBY Crop Insurance",
    "PMJJBY Claim", "PMSBY Claim", "Police Verification", "Policy Surrender",
    "Pollution Certificate", "Power Outage", "PPO Correction", "Premium Refund",
    "Property Tax", "Public Nuisance", "Public Toilets", "Public Transport Services",
    "Quality Complaint", "Quota Denial", "Ration Card Issue", "Refill Delay",
    "Refund Delay", "Registered Letter", "Registration", "Renewal", "Reservation",
    "Road Damage & Potholes", "RPF Complaint", "Scholarship Delay", "School Admission",
    "Section 89 Relief", "Service Deficiency", "Sewage Overflow", "SIM Activation",
    "Soil Health Card", "Spam Calls", "SPARSH Migration", "Speed Post Delay",
    "Stray Animals", "Streetlights", "Streetlights & Public Lighting", "Subsidy",
    "Surveillance & Policing", "Tanker Service", "Tatkal", "Tatkal Issue",
    "TDS Mismatch", "Teacher Absence", "Ticket Refund", "Tower Coverage",
    "Trade Licence", "Traffic Management & Violations", "Train Delay",
    "Transformer Fault", "UAN Activation", "Ujjwala Yojana",
    "Unauthorized Construction", "Unauthorized Debit", "University Marksheet",
    "Update Failure", "Vaccination", "Vehicle Registration", "Warranty Denied",
    "Water Quality & Metering", "Weights & Measures", "Withdrawal Delay",
    "Wrong Tax Demand",
]

STATES = [
    "Uttar Pradesh", "Maharashtra", "Bihar", "West Bengal", "Madhya Pradesh",
    "Rajasthan", "Delhi", "Karnataka", "Tamil Nadu", "Gujarat", "Andhra Pradesh",
    "Telangana", "Odisha", "Kerala", "Jharkhand", "Assam", "Punjab",
    "Chhattisgarh", "Haryana", "Uttarakhand", "Himachal Pradesh",
    "Jammu & Kashmir (UT)", "Ladakh (UT)", "Goa", "Tripura", "Meghalaya",
    "Manipur", "Nagaland", "Arunachal Pradesh", "Mizoram", "Sikkim",
    "Chandigarh (UT)", "Puducherry (UT)", "Andaman & Nicobar Islands (UT)",
    "Dadra & Nagar Haveli and Daman & Diu (UT)", "Lakshadweep (UT)",
]

# Questions in final form order
QUESTIONS = [
    {
        "title": "Complaint Text",
        "type": "PARAGRAPH",
        "required": True,
        "help": "Describe the issue in Hindi, English, or Hinglish. At least 2 sentences.",
    },
    {
        "title": "Language",
        "type": "RADIO",
        "required": True,
        "help": "Language used in the complaint text above.",
        "options": ["English", "Hindi", "Hinglish"],
    },
    {
        "title": "Department",
        "type": "DROP_DOWN",
        "required": True,
        "help": "Which government department does this complaint belong to?",
        "options": DEPARTMENTS,
    },
    {
        "title": "Sub-Category",
        "type": "DROP_DOWN",
        "required": True,
        "help": "Select the closest matching sub-category.",
        "options": SUB_CATEGORIES,
    },
    {
        "title": "State",
        "type": "DROP_DOWN",
        "required": True,
        "help": "State or UT where this issue occurred.",
        "options": STATES,
    },
    {
        "title": "City / District",
        "type": "TEXT",
        "required": True,
        "help": "e.g. Lucknow, Bhopal, South Delhi",
    },
    {
        "title": "Priority",
        "type": "RADIO",
        "required": True,
        "help": "How urgent is this complaint?",
        "options": ["High", "Mid", "Low"],
    },
    {
        "title": "Sentiment",
        "type": "RADIO",
        "required": True,
        "help": "What is the emotional tone of the complaint?",
        "options": ["Neutral", "Frustrated", "Distressed"],
    },
]

# ── Request builders ──────────────────────────────────────────────────────────
def _make_item(title, help_text, required, question_body):
    return {
        "createItem": {
            "item": {
                "title": title,
                "description": help_text,
                "questionItem": {"question": {"required": required, **question_body}},
            },
            "location": {"index": 0},
        }
    }

def build_requests(questions):
    reqs = []
    for q in questions:
        t, h, r = q["title"], q.get("help", ""), q["required"]
        qtype = q["type"]
        if qtype == "PARAGRAPH":
            body = {"textQuestion": {"paragraph": True}}
        elif qtype == "TEXT":
            body = {"textQuestion": {"paragraph": False}}
        elif qtype == "RADIO":
            body = {"choiceQuestion": {"type": "RADIO",
                                       "options": [{"value": o} for o in q["options"]],
                                       "shuffle": False}}
        elif qtype == "DROP_DOWN":
            body = {"choiceQuestion": {"type": "DROP_DOWN",
                                       "options": [{"value": o} for o in q["options"]],
                                       "shuffle": False}}
        reqs.append(_make_item(t, h, r, body))
    reqs.reverse()   # insert-at-0 trick keeps original order
    return reqs

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    creds   = get_credentials()
    service = build("forms", "v1", credentials=creds)

    print("Creating form…")
    form = service.forms().create(body={
        "info": {"title": FORM_TITLE, "documentTitle": FORM_TITLE}
    }).execute()
    fid = form["formId"]
    print(f"  Form ID: {fid}")

    print("Setting description…")
    service.forms().batchUpdate(formId=fid, body={"requests": [{
        "updateFormInfo": {
            "info": {"description": DESCRIPTION},
            "updateMask": "description",
        }
    }]}).execute()

    print(f"Adding {len(QUESTIONS)} questions…")
    service.forms().batchUpdate(
        formId=fid, body={"requests": build_requests(QUESTIONS)}
    ).execute()
    print("  done.")

    edit_url  = f"https://docs.google.com/forms/d/{fid}/edit"
    share_url = f"https://docs.google.com/forms/d/{fid}/viewform"

    print(f"\n✅ Form created!")
    print(f"   Edit  : {edit_url}")
    print(f"   Share : {share_url}")

    with open("form_urls_v2.json", "w") as f:
        json.dump({"form_id": fid, "edit_url": edit_url, "share_url": share_url}, f, indent=2)
    print("   Saved to form_urls_v2.json")

if __name__ == "__main__":
    main()
