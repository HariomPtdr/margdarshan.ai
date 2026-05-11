"""Decision tree data for Layer 2 — completeness checking and progressive questioning.

Layer 2's job: detect whether a complaint is complete enough to send to Layer 4.
Categories here map 1:1 to the 25 MuRIL classifier departments so keywords
used for conversation completeness checking are consistent with final classification.

NOT a classifier — just a completeness checker that guides the conversation.
"""

# 25 departments matching MuRIL training labels (what classifier predicts)
MAIN_CATEGORIES = [
    ("Electricity",                    "Electricity / Bijli / Power"),
    ("Water Supply",                   "Water Supply / Paani"),
    ("Roads & Transportation",         "Roads / Sadak / Potholes / Transport"),
    ("Waste Management",               "Garbage / Kachra / Sanitation / Safai"),
    ("Health & Family Welfare",        "Health / Hospital / Doctor"),
    ("Police",                         "Police / Safety / FIR"),
    ("Education (Higher / School)",    "Education / School / Scholarship"),
    ("Housing & Urban Affairs",        "Housing / Urban / Property"),
    ("Agriculture & Farmers Welfare",  "Agriculture / Farming / Kisan"),
    ("Banking (DFS)",                  "Banking / ATM / Account"),
    ("Aadhaar (UIDAI)",               "Aadhaar / UIDAI / ID card"),
    ("Income Tax (CBDT)",              "Income Tax / ITR / Refund"),
    ("GST (CBIC)",                     "GST / Tax / GSTIN"),
    ("EPFO",                           "EPF / PF / Provident Fund / ESI"),
    ("Insurance (DFS)",                "Insurance / Claim / LIC / PMJJBY"),
    ("Passport (MEA)",                 "Passport / Visa / MEA"),
    ("Pension & Pensioners Welfare",   "Pension / Old age / Widow / Disability"),
    ("Petroleum & LPG",                "LPG / Gas cylinder / Petrol / Ujjwala"),
    ("Postal",                         "Post office / Speed post / Money order"),
    ("Public Distribution (PDS)",      "Ration / PDS / FPS / Anaj"),
    ("Public Safety & Encroachment",   "Encroachment / Safety / Nuisance"),
    ("RTO / State Transport",          "RTO / Driving licence / Vehicle registration"),
    ("Railways",                       "Railway / Train / IRCTC / PNR"),
    ("Telecom",                        "Telecom / Mobile / Internet / SIM / Broadband"),
    ("OTHER",                          "Other government complaint"),
]

# Sub-issues per category — shown as chips when user needs to narrow down
SUB_ISSUES = {
    "Electricity": [
        ("POWER_OUTAGE",    "No electricity / Power cut"),
        ("VOLTAGE",         "Voltage fluctuation / Low voltage"),
        ("TRANSFORMER",     "Transformer issue / fault"),
        ("STREET_LIGHT",    "Street light not working"),
        ("METER",           "Meter / Wrong billing / Overcharging"),
        ("NEW_CONNECTION",  "New electricity connection"),
    ],
    "Water Supply": [
        ("NO_WATER",        "No water supply"),
        ("LOW_PRESSURE",    "Low water pressure"),
        ("DIRTY_WATER",     "Dirty / smelly / contaminated water"),
        ("PIPELINE_LEAK",   "Pipeline burst / leakage"),
        ("NEW_CONNECTION",  "New water connection"),
    ],
    "Roads & Transportation": [
        ("POTHOLE",         "Pothole / bad road condition"),
        ("DRAINAGE",        "Drainage / sewage overflow on road"),
        ("FOOTPATH",        "Footpath / pedestrian issue"),
        ("TRAFFIC",         "Traffic signal / management issue"),
        ("ROAD_LIGHT",      "Street light / road lighting"),
    ],
    "Waste Management": [
        ("GARBAGE_COLLECTION", "Garbage not being collected"),
        ("GARBAGE_DUMPING",    "Illegal garbage dumping / littering"),
        ("NOISE_POLLUTION",    "Noise pollution (loudspeaker / construction)"),
        ("AIR_POLLUTION",      "Air / smoke / dust pollution"),
        ("PUBLIC_TOILET",      "Public toilet not working / dirty"),
        ("MOSQUITO_PEST",      "Mosquito / pest control"),
        ("STRAY_ANIMALS",      "Stray animals problem"),
    ],
    "Health & Family Welfare": [
        ("HOSPITAL_SERVICE", "Hospital service poor / unavailable"),
        ("AMBULANCE",        "Ambulance not available"),
        ("MEDICINE",         "Medicine not available"),
        ("DOCTOR_ABSENT",    "Doctor / staff absent"),
        ("VACCINATION",      "Vaccination / immunization issue"),
        ("PMJAY",            "Ayushman card / health insurance"),
    ],
    "Police": [
        ("FIR",          "FIR not being registered"),
        ("SAFETY",       "Safety concern / threat / emergency"),
        ("HARASSMENT",   "Police harassment / misconduct"),
        ("CRIME",        "Crime / theft / robbery"),
        ("VERIFICATION", "Police verification delay"),
    ],
    "Education (Higher / School)": [
        ("TEACHER_ABSENT", "Teacher absent / school closed"),
        ("FACILITY",       "School facility / building issue"),
        ("SCHOLARSHIP",    "Scholarship not received"),
        ("ADMISSION",      "Admission issue"),
        ("MIDDAY_MEAL",    "Mid-day meal not provided"),
    ],
    "Housing & Urban Affairs": [
        ("PMAY",          "PMAY / Housing scheme"),
        ("PROPERTY_TAX",  "Property tax issue"),
        ("BUILDING_PLAN", "Building plan approval"),
        ("TRADE_LICENCE", "Trade licence issue"),
        ("ENCROACHMENT",  "Encroachment / illegal construction"),
    ],
    "Agriculture & Farmers Welfare": [
        ("PM_KISAN",      "PM-Kisan payment not received"),
        ("CROP_INSURANCE","PMFBY crop insurance"),
        ("MANDI",         "Mandi / procurement issue"),
        ("KCC_LOAN",      "KCC / farm loan issue"),
        ("SOIL_CARD",     "Soil health card"),
    ],
    "Banking (DFS)": [
        ("ATM",           "ATM failure / not working"),
        ("ACCOUNT",       "Account frozen / issue"),
        ("FRAUD",         "Cyber fraud / unauthorized debit"),
        ("LOAN",          "Loan disbursement issue"),
        ("KYC",           "KYC update problem"),
    ],
    "Aadhaar (UIDAI)": [
        ("LINKING",       "Aadhaar linking / seeding"),
        ("UPDATE",        "Name / DOB / address correction"),
        ("BIOMETRIC",     "Biometric lock / update"),
        ("ENROLLMENT",    "New enrollment / center issue"),
    ],
    "Income Tax (CBDT)": [
        ("REFUND",        "ITR refund delay"),
        ("TDS",           "TDS mismatch"),
        ("DEMAND",        "Wrong tax demand"),
        ("FILING",        "ITR filing issue"),
    ],
    "GST (CBIC)": [
        ("REFUND",        "GST refund delay"),
        ("FILING",        "Filing error / registration"),
        ("ITC",           "Input tax credit denial"),
    ],
    "EPFO": [
        ("UAN",           "UAN activation / update"),
        ("WITHDRAWAL",    "PF withdrawal delay"),
        ("EMPLOYER",      "Employer default"),
        ("PENSION_EPS",   "EPS-95 pension issue"),
    ],
    "Insurance (DFS)": [
        ("CLAIM",         "Claim rejection / delay"),
        ("PMJJBY",        "PMJJBY / PMSBY claim"),
        ("PREMIUM",       "Premium refund"),
        ("POLICY",        "Policy surrender"),
    ],
    "Passport (MEA)": [
        ("DELAY",         "Passport not received / delayed"),
        ("LOST",          "Lost passport"),
        ("TATKAL",        "Tatkal issue"),
        ("POLICE_VERIFY", "Police verification delay"),
    ],
    "Pension & Pensioners Welfare": [
        ("OLD_AGE",       "Old age pension not received"),
        ("WIDOW",         "Widow pension issue"),
        ("DISABILITY",    "Disability pension"),
        ("SPARSH",        "SPARSH migration issue"),
        ("ARREARS",       "Pension arrears"),
    ],
    "Petroleum & LPG": [
        ("CYLINDER",      "LPG cylinder not delivered"),
        ("REFILL",        "Refill delay"),
        ("UJJWALA",       "Ujjwala Yojana issue"),
        ("PRICE",         "Price / overcharging"),
        ("DISTRIBUTOR",   "Distributor service issue"),
    ],
    "Postal": [
        ("DELAY",         "Speed post / parcel delay"),
        ("LOST",          "Lost parcel / letter"),
        ("MONEY_ORDER",   "Money order issue"),
        ("REGISTERED",    "Registered letter issue"),
    ],
    "Public Distribution (PDS)": [
        ("RATION_CARD",   "Ration card issue / not received"),
        ("FPS",           "Fair price shop not open"),
        ("QUOTA",         "Quota denial / shortage"),
        ("QUALITY",       "Poor quality ration"),
        ("NFSA",          "NFSA eligibility issue"),
    ],
    "Public Safety & Encroachment": [
        ("NOISE_POLLUTION",  "Noise pollution (loudspeaker / music / construction)"),
        ("PUBLIC_NUISANCE",  "Public nuisance / disturbance"),
        ("ROAD_ENCROACH",    "Road / footpath encroachment"),
        ("LAND_ENCROACH",    "Land encroachment"),
        ("FIRE_SAFETY",      "Fire safety violation"),
    ],
    "RTO / State Transport": [
        ("DRIVING_LICENCE","Driving licence issue"),
        ("VEHICLE_REG",   "Vehicle registration"),
        ("PERMIT",        "Permit / fitness certificate"),
        ("POLLUTION",     "Pollution certificate"),
        ("PUBLIC_TRANSPORT","Public bus / transport service"),
    ],
    "Railways": [
        ("TRAIN_DELAY",   "Train delay / cancellation"),
        ("TICKET_REFUND", "Ticket refund issue"),
        ("CLEANLINESS",   "Coach cleanliness / facility"),
        ("RPF",           "RPF complaint"),
        ("TATKAL",        "Tatkal booking issue"),
    ],
    "Telecom": [
        ("NO_SIGNAL",     "No network / poor signal"),
        ("BROADBAND",     "Broadband / internet outage"),
        ("MNP",           "Mobile number portability"),
        ("SIM",           "SIM activation / issue"),
        ("SPAM",          "Spam calls / messages"),
    ],
    "OTHER": [
        ("CORRUPTION",    "Corruption / bribery"),
        ("HUMAN_RIGHTS",  "Human rights issue"),
        ("WELFARE_SCHEME","Government scheme not received"),
        ("GENERAL",       "Other government complaint"),
    ],
}

# Sub-issues that need scope clarification (house / building / area)
SCOPE_NEEDED = {
    "POWER_OUTAGE", "NO_WATER", "VOLTAGE", "DIRTY_WATER",
    "GARBAGE_COLLECTION", "POTHOLE", "PIPELINE_LEAK", "LOW_PRESSURE",
    "STREET_LIGHT", "ROAD_LIGHT", "NOISE_POLLUTION",
}

SCOPE_OPTIONS = [
    ("HOUSE",    "Only in my house / shop"),
    ("BUILDING", "Entire building / block / society"),
    ("AREA",     "Entire area / colony / ward"),
]

# Sub-issues where GPS location is not critical
NON_LOCATION_ISSUES = {
    "OLD_AGE", "WIDOW", "DISABILITY", "PENSION_EPS", "SPARSH", "ARREARS",
    "RATION_CARD", "FPS", "QUOTA", "NFSA",
    "LINKING", "UPDATE", "BIOMETRIC",
    "REFUND", "TDS", "DEMAND", "FILING",
    "UAN", "WITHDRAWAL", "EMPLOYER",
    "DRIVING_LICENCE", "VEHICLE_REG",
    "TRAIN_DELAY", "TICKET_REFUND",
    "CLAIM", "PREMIUM",
    "DELAY", "LOST", "TATKAL",
    "NEW_CONNECTION", "METER",
    "ATM", "ACCOUNT", "LOAN", "KYC",
}

# ONE clarifying question per category before pipeline
CLARIFY_QUESTIONS = {
    "Electricity":                   [("DURATION", "How long has this issue been going on? (hours/days/weeks)")],
    "Water Supply":                  [("DURATION", "Since how many days is this water issue occurring?")],
    "Roads & Transportation":        [("DURATION", "Since how long has this road condition persisted?")],
    "Waste Management":              [("DURATION", "Since how long has this issue been occurring?")],
    "Health & Family Welfare":       [("FACILITY", "Is this a government hospital / health center?")],
    "Police":                        [("URGENT",   "Is this an immediate safety emergency? (yes/no)")],
    "Education (Higher / School)":   [("DURATION", "Since how long is this issue going on?")],
    "Housing & Urban Affairs":       [("DURATION", "Since how long is this issue pending?")],
    "Agriculture & Farmers Welfare": [("DURATION", "Since how long is this issue pending?")],
    "Banking (DFS)":                 [("DURATION", "Since how many days is this bank issue pending?")],
    "Aadhaar (UIDAI)":              [("DURATION", "Since how long is your Aadhaar issue pending?")],
    "Income Tax (CBDT)":             [("DURATION", "For which assessment year is this issue?")],
    "GST (CBIC)":                    [("DURATION", "Since how long is this GST issue pending?")],
    "EPFO":                          [("DURATION", "Since how long is this PF issue pending?")],
    "Insurance (DFS)":               [("DURATION", "Since how long has this insurance claim been pending?")],
    "Passport (MEA)":                [("DURATION", "Since when did you apply for the passport?")],
    "Pension & Pensioners Welfare":  [("DURATION", "Since how many months is the pension not received?")],
    "Petroleum & LPG":               [("DURATION", "Since how long is this LPG issue occurring?")],
    "Postal":                        [("DURATION", "Since how many days has this postal issue occurred?")],
    "Public Distribution (PDS)":     [("DURATION", "Since how long is this ration issue occurring?")],
    "Public Safety & Encroachment":  [("DURATION", "Since how long has this issue been going on?")],
    "RTO / State Transport":         [("DURATION", "Since when is this RTO issue pending?")],
    "Railways":                      [("DURATION", "When did this railway issue occur?")],
    "Telecom":                       [("DURATION", "Since how long is this network/telecom issue occurring?")],
    "OTHER":                         [("DURATION", "Since how long are you facing this issue?")],
}

# Keywords for fast (no-LLM) category detection — aligned with MuRIL departments
CATEGORY_KEYWORDS = {
    "Electricity": [
        "bijli", "light", "current", "power", "batti", "electricity",
        "transformer", "meter", "voltage", "inverter", "load shedding",
        "electric", "wiring", "pole", "batti gul",
    ],
    "Water Supply": [
        "paani", "water", "nal", "supply", "pipeline", "bore", "nali",
        "nalka", "boring", "tanker", "pani", "jal", "peyjal",
    ],
    "Roads & Transportation": [
        "sadak", "road", "pothole", "gadda", "bridge", "nala", "footpath",
        "pul", "rasta", "sarak", "highway", "drainage",
    ],
    "Waste Management": [
        "kachra", "garbage", "dustbin", "sweeper", "safai", "jhadu",
        "mosquito", "machhar", "pest", "sewage", "drain",
        "dhuan", "smoke", "dust", "dhool", "gandagi", "stray",
    ],
    "Public Safety & Encroachment": [
        "encroachment", "kabza", "fire safety", "unauthorized construction", "illegal",
        "shor", "noise", "awaaz", "nuisance", "pradushan", "pollution",
        "gaana", "music", "loudspeaker", "dj", "dhol", "baraat",
        "shorgul", "disturbance", "halla",
    ],
    "Health & Family Welfare": [
        "hospital", "doctor", "medicine", "dawai", "nurse", "ambulance",
        "health", "swasthya", "clinic", "dispensary", "pmjay", "ayushman",
        "vaccination", "dispensery", "medical",
    ],
    "Police": [
        "police", "fir", "thana", "chor", "harass", "safety",
        "crime", "daroga", "theft", "chori", "rapat", "complaint darj",
    ],
    "Education (Higher / School)": [
        "school", "teacher", "scholarship", "admission", "vidyalaya",
        "shiksha", "pathshala", "hostel", "midday", "siksha",
        "college", "university", "padhai",
    ],
    "Housing & Urban Affairs": [
        "makaan", "housing", "flat", "pmay", "property", "urban",
        "building plan", "trade licence", "construction",
    ],
    "Agriculture & Farmers Welfare": [
        "kisan", "farmer", "fasal", "crop", "kheti", "agriculture",
        "mandi", "pm kisan", "pmfby", "kcc", "soil",
    ],
    "Banking (DFS)": [
        "bank", "atm", "account", "passbook", "cheque", "loan",
        "banking", "ifsc", "kyc", "fd", "savings",
    ],
    "Aadhaar (UIDAI)": [
        "aadhaar", "adhar", "uidai", "biometric", "aadhar card",
        "enrollment", "e-aadhaar",
    ],
    "Income Tax (CBDT)": [
        "income tax", "itr", "refund", "tds", "pan card", "cbdt",
        "tax demand", "form 26as",
    ],
    "GST (CBIC)": [
        "gst", "gstin", "cbic", "input tax", "itc", "invoice",
        "e-way bill",
    ],
    "EPFO": [
        "epf", "pf", "provident fund", "uan", "epfo", "esic",
        "eps-95", "eps",
    ],
    "Insurance (DFS)": [
        "insurance", "claim", "lic", "pmjjby", "pmsby", "policy",
        "bima", "insured",
    ],
    "Passport (MEA)": [
        "passport", "visa", "mea", "tatkal passport", "ecr",
        "travel document",
    ],
    "Pension & Pensioners Welfare": [
        "pension", "bhatta", "old age", "widow pension", "disability pension",
        "sparsh", "pensioner", "retirement",
    ],
    "Petroleum & LPG": [
        "lpg", "gas cylinder", "ujjwala", "petrol", "cylinder",
        "gas agency", "refill",
    ],
    "Postal": [
        "post office", "speed post", "parcel", "money order", "dak",
        "postal", "registered letter", "india post",
    ],
    "Public Distribution (PDS)": [
        "ration", "pds", "fps", "fair price shop", "anaj", "wheat",
        "rice", "gehu", "chawal", "ration card", "nfsa",
    ],
    "Public Safety & Encroachment": [
        "encroachment", "kabza", "public nuisance", "fire safety",
        "unauthorized construction", "illegal",
    ],
    "RTO / State Transport": [
        "rto", "driving licence", "dl", "rc", "vehicle registration",
        "permit", "fitness", "pollution certificate", "challan",
    ],
    "Railways": [
        "railway", "train", "irctc", "pnr", "ticket", "station",
        "rail", "coach", "reservation", "rpf",
    ],
    "Telecom": [
        "mobile", "network", "sim", "internet", "broadband", "trai",
        "telecom", "jio", "airtel", "vi", "bsnl", "signal", "4g", "5g",
    ],
    "OTHER": [
        "corruption", "rishwat", "bribery", "human rights",
        "scheme", "yojana", "welfare",
    ],
}

# Sub-issue keywords for fast detection within a category
SUB_ISSUE_KEYWORDS = {
    "POWER_OUTAGE":  ["nahi aa rahi", "band hai", "cut", "gul", "nahi hai", "nahi ata", "kati hai", "no power", "power cut"],
    "VOLTAGE":       ["fluctuation", "low voltage", "high voltage", "jhadka", "voltage", "spark"],
    "TRANSFORMER":   ["transformer", "blast", "fault", "khrab", "phata", "jal gaya"],
    "STREET_LIGHT":  ["street light", "lamp", "khamba", "pole light", "sadak ki light"],
    "METER":         ["bill", "overcharge", "meter", "reading", "galat bill", "zyada bill"],
    "NO_WATER":      ["nahi aa raha", "nahi aata", "supply nahi", "band hai", "no supply", "aata nahi"],
    "DIRTY_WATER":   ["ganda", "dirty", "smell", "boo", "gandla", "contaminated", "color", "rang"],
    "LOW_PRESSURE":  ["pressure", "kam aata", "thoda", "bahut dhire"],
    "PIPELINE_LEAK": ["leak", "phut gaya", "burst", "toot gaya", "tutna"],
    "POTHOLE":       ["gadda", "pothole", "kharab sadak", "tooti sadak"],
    "DRAINAGE":      ["nala", "sewer", "naali", "overflow", "jam", "choke"],
    "FIR":           ["fir", "darj nahi", "register nahi", "likhte nahi"],
    "OLD_AGE":       ["old age pension", "budhapa pension", "vridha pension"],
    "WIDOW":         ["widow pension", "vidhwa pension"],
    "DISABILITY":    ["disability pension", "viklang"],
    "RATION_CARD":   ["ration card", "nahi mila", "card nahi"],
    "GARBAGE_COLLECTION": ["garbage nahi", "kachra nahi", "collect nahi", "nahi utha", "safai nahi"],
    "NOISE_POLLUTION":    ["noise", "shor", "awaaz", "loud", "loudspeaker", "dj", "dhol"],
    "AIR_POLLUTION":      ["pollution", "pradushan", "dhuan", "smoke", "dust", "dhool"],
    "TRAIN_DELAY":   ["train late", "delay", "cancelled", "nahi aaya"],
    "LPG":           ["cylinder nahi", "gas nahi", "refill nahi"],
    "PASSPORT":      ["passport nahi", "delay", "nahi mila"],
}

CATEGORY_NAMES = {
    "Electricity":                   {"en": "Electricity",       "hi": "बिजली",          "hinglish": "Bijli"},
    "Water Supply":                  {"en": "Water Supply",      "hi": "पानी",            "hinglish": "Paani"},
    "Roads & Transportation":        {"en": "Roads",             "hi": "सड़क",            "hinglish": "Sadak"},
    "Waste Management":              {"en": "Waste/Sanitation",  "hi": "सफाई/कचरा",      "hinglish": "Safai"},
    "Health & Family Welfare":       {"en": "Health",            "hi": "स्वास्थ्य",      "hinglish": "Health"},
    "Police":                        {"en": "Police",            "hi": "पुलिस",           "hinglish": "Police"},
    "Education (Higher / School)":   {"en": "Education",         "hi": "शिक्षा",          "hinglish": "Shiksha"},
    "Housing & Urban Affairs":       {"en": "Housing",           "hi": "आवास",            "hinglish": "Housing"},
    "Agriculture & Farmers Welfare": {"en": "Agriculture",       "hi": "कृषि",            "hinglish": "Kheti"},
    "Banking (DFS)":                 {"en": "Banking",           "hi": "बैंकिंग",         "hinglish": "Banking"},
    "Aadhaar (UIDAI)":              {"en": "Aadhaar",           "hi": "आधार",            "hinglish": "Aadhaar"},
    "Income Tax (CBDT)":             {"en": "Income Tax",        "hi": "आयकर",            "hinglish": "Income Tax"},
    "GST (CBIC)":                    {"en": "GST",               "hi": "जीएसटी",          "hinglish": "GST"},
    "EPFO":                          {"en": "EPFO/PF",           "hi": "ईपीएफओ",         "hinglish": "PF/EPFO"},
    "Insurance (DFS)":               {"en": "Insurance",         "hi": "बीमा",            "hinglish": "Insurance"},
    "Passport (MEA)":                {"en": "Passport",          "hi": "पासपोर्ट",        "hinglish": "Passport"},
    "Pension & Pensioners Welfare":  {"en": "Pension",           "hi": "पेंशन",           "hinglish": "Pension"},
    "Petroleum & LPG":               {"en": "Petroleum/LPG",     "hi": "एलपीजी/पेट्रोल", "hinglish": "LPG/Gas"},
    "Postal":                        {"en": "Postal",            "hi": "डाक",             "hinglish": "Post"},
    "Public Distribution (PDS)":     {"en": "Ration/PDS",        "hi": "राशन",            "hinglish": "Ration"},
    "Public Safety & Encroachment":  {"en": "Public Safety",     "hi": "सार्वजनिक सुरक्षा","hinglish": "Safety"},
    "RTO / State Transport":         {"en": "RTO/Transport",     "hi": "आरटीओ",           "hinglish": "RTO"},
    "Railways":                      {"en": "Railways",          "hi": "रेलवे",           "hinglish": "Railway"},
    "Telecom":                       {"en": "Telecom",           "hi": "दूरसंचार",        "hinglish": "Telecom"},
    "OTHER":                         {"en": "Other",             "hi": "अन्य",            "hinglish": "Anya"},
}
