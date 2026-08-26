import streamlit as st
import re
from html import escape

st.set_page_config(
    page_title="Smart Document Platform",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==============================================================================
# MOCK SECURITY / GOVERNANCE CONFIGURATION (South Dakota / Idaho)
# ==============================================================================

USERS = {
    "Regulator — SD (Full Access)": {
        "username": "reg.sd@state.sd.gov",
        "role": "STATE_REGULATOR",
        "state": "SD",
        "jurisdiction": "SD",
        "business_areas": ["Market Regulation", "Complaints", "Exams"],
        "can_download": True,
        "unmasked_pii": True,
    },
    "Analyst — SD (Exams Only, Masked)": {
        "username": "analyst.sd@state.sd.gov",
        "role": "FINANCIAL_ANALYST",
        "state": "SD",
        "jurisdiction": "SD",
        "business_areas": ["Exams"],
        "can_download": True,
        "unmasked_pii": False,
    },
    "Analyst — ID (Exams Only, No Download)": {
        "username": "analyst.id@state.id.gov",
        "role": "FINANCIAL_ANALYST",
        "state": "ID",
        "jurisdiction": "ID",
        "business_areas": ["Exams"],
        "can_download": False,
        "unmasked_pii": False,
    },
}

# ==============================================================================
# SNOWFLAKE-READY MOCK TABLES
# DOC_SEARCH_CONTENT, SBS.ATTACHMENT, MR_CASE
# ==============================================================================

DOC_SEARCH_CONTENT = [
    {
        "DOC_ID": "DOC-10001",
        "ATTACHMENT_ID": "890786543",
        "CONTENT_TEXT": (
            "Accident appears to have occurred on Monday evening near Sioux Falls "
            "at the intersection of Main and 10th Street. Jane Smith reported the "
            "incident to Prairie Plains Mutual Insurance Company."
        ),
        "FILE_PATH": "SD/Market Regulation/890786543/accident_investigation_sd.docx",
        "BUSINESS_AREA": "Market Regulation",
        "DOC_STATE": "SD",
        "CONTENT_HASH": "sha256:aaa111",
        "IS_CURRENT": True,
        "UPLOAD_DATE": "2019-10-03",
        "LOCKED": False,
    },
    {
        "DOC_ID": "DOC-10002",
        "ATTACHMENT_ID": "890786544",
        "CONTENT_TEXT": (
            "The claimant filed a formal dispute concerning the accident "
            "that occurred on December 19th near Rapid City. Jane Doe contacted "
            "Black Hills Mutual Insurance Company."
        ),
        "FILE_PATH": "SD/Market Regulation/890786544/jane_doe_dispute_sd.pdf",
        "BUSINESS_AREA": "Market Regulation",
        "DOC_STATE": "SD",
        "CONTENT_HASH": "sha256:bbb222",
        "IS_CURRENT": True,
        "UPLOAD_DATE": "2019-12-22",
        "LOCKED": True,
    },
    {
        "DOC_ID": "DOC-10003",
        "ATTACHMENT_ID": "890786545",
        "CONTENT_TEXT": (
            "The policyholder submitted a formal complaint regarding claim denial "
            "for a vehicle loss near Pierre. The complaint was assigned for review."
        ),
        "FILE_PATH": "SD/Complaints/890786545/uniformdoc_sd.pdf",
        "BUSINESS_AREA": "Complaints",
        "DOC_STATE": "SD",
        "CONTENT_HASH": "sha256:ccc333",
        "IS_CURRENT": True,
        "UPLOAD_DATE": "2020-01-05",
        "LOCKED": False,
    },
    {
        "DOC_ID": "DOC-10004",
        "ATTACHMENT_ID": "890786546",
        "CONTENT_TEXT": (
            "Details of damage sustained by vehicle after accident near Sioux Falls. "
            "Total loss assessment filed by the adjuster."
        ),
        "FILE_PATH": "SD/Exams/890786546/accident_detail_sd.pdf",
        "BUSINESS_AREA": "Exams",
        "DOC_STATE": "SD",
        "CONTENT_HASH": "sha256:ddd444",
        "IS_CURRENT": True,
        "UPLOAD_DATE": "2020-01-22",
        "LOCKED": False,
    },
    {
        "DOC_ID": "DOC-10005",
        "ATTACHMENT_ID": "890786547",
        "CONTENT_TEXT": (
            "Details of accident damage assessment from third party inspector "
            "retained by Snake River Group LLC near Boise, Idaho."
        ),
        "FILE_PATH": "ID/Exams/890786547/cornwall_motorcycle_club_id.docx",
        "BUSINESS_AREA": "Exams",
        "DOC_STATE": "ID",
        "CONTENT_HASH": "sha256:eee555",
        "IS_CURRENT": True,
        "UPLOAD_DATE": "2020-02-10",
        "LOCKED": False,
    },
    {
        "DOC_ID": "DOC-20001",
        "ATTACHMENT_ID": "900001111",
        "CONTENT_TEXT": "Accident occurred near Providence involving a delivery van. Witness reported heavy damage and possible policy lapse.",
        "FILE_PATH": "RI/Market Regulation/900001111/providence_delivery_accident.pdf",
        "BUSINESS_AREA": "Market Regulation",
        "DOC_STATE": "RI",
        "CONTENT_HASH": "sha256:20001aaa",
        "IS_CURRENT": True,
        "UPLOAD_DATE": "2021-03-14",
        "LOCKED": False,
    },
    {
        "DOC_ID": "DOC-20002",
        "ATTACHMENT_ID": "900001112",
        "CONTENT_TEXT": "Formal complaint filed by policyholder regarding denied roof damage claim after severe storm in Warwick.",
        "FILE_PATH": "RI/Complaints/900001112/roof_damage_complaint.docx",
        "BUSINESS_AREA": "Complaints",
        "DOC_STATE": "RI",
        "CONTENT_HASH": "sha256:20002bbb",
        "IS_CURRENT": True,
        "UPLOAD_DATE": "2021-04-02",
        "LOCKED": False,
    },
    {
        "DOC_ID": "DOC-20003",
        "ATTACHMENT_ID": "900001113",
        "CONTENT_TEXT": "Market Conduct Exam findings related to casualty claims processing delays at Ocean State Mutual.",
        "FILE_PATH": "RI/Exams/900001113/ocean_state_exam_findings.pdf",
        "BUSINESS_AREA": "Exams",
        "DOC_STATE": "RI",
        "CONTENT_HASH": "sha256:20003ccc",
        "IS_CURRENT": True,
        "UPLOAD_DATE": "2021-05-10",
        "LOCKED": False,
    },
    {
        "DOC_ID": "DOC-20004",
        "ATTACHMENT_ID": "900001114",
        "CONTENT_TEXT": "Accident report from Newport involving a rental vehicle. Adjuster noted inconsistencies in claimant statements.",
        "FILE_PATH": "RI/Market Regulation/900001114/newport_rental_accident.pdf",
        "BUSINESS_AREA": "Market Regulation",
        "DOC_STATE": "RI",
        "CONTENT_HASH": "sha256:20004ddd",
        "IS_CURRENT": True,
        "UPLOAD_DATE": "2021-06-01",
        "LOCKED": False,
    },
    {
        "DOC_ID": "DOC-20005",
        "ATTACHMENT_ID": "900001115",
        "CONTENT_TEXT": "Complaint alleging unfair claims handling by Narragansett Bay Insurance Company.",
        "FILE_PATH": "RI/Complaints/900001115/unfair_claims_handling.pdf",
        "BUSINESS_AREA": "Complaints",
        "DOC_STATE": "RI",
        "CONTENT_HASH": "sha256:20005eee",
        "IS_CURRENT": True,
        "UPLOAD_DATE": "2021-06-18",
        "LOCKED": False,
    },
    {
        "DOC_ID": "DOC-20006",
        "ATTACHMENT_ID": "900001116",
        "CONTENT_TEXT": "Exam report detailing life insurance underwriting irregularities at Atlantic Life Group.",
        "FILE_PATH": "RI/Exams/900001116/atlantic_life_exam.pdf",
        "BUSINESS_AREA": "Exams",
        "DOC_STATE": "RI",
        "CONTENT_HASH": "sha256:20006fff",
        "IS_CURRENT": True,
        "UPLOAD_DATE": "2021-07-03",
        "LOCKED": False,
    },
    {
        "DOC_ID": "DOC-20007",
        "ATTACHMENT_ID": "900001117",
        "CONTENT_TEXT": "Accident investigation involving commercial fleet vehicle near Cranston. Inspector noted brake failure.",
        "FILE_PATH": "RI/Market Regulation/900001117/cranston_fleet_accident.docx",
        "BUSINESS_AREA": "Market Regulation",
        "DOC_STATE": "RI",
        "CONTENT_HASH": "sha256:20007ggg",
        "IS_CURRENT": True,
        "UPLOAD_DATE": "2021-07-22",
        "LOCKED": False,
    },
    {
        "DOC_ID": "DOC-20008",
        "ATTACHMENT_ID": "900001118",
        "CONTENT_TEXT": "Policyholder complaint regarding delayed payout for fire damage claim in Pawtucket.",
        "FILE_PATH": "RI/Complaints/900001118/pawtucket_fire_claim.pdf",
        "BUSINESS_AREA": "Complaints",
        "DOC_STATE": "RI",
        "CONTENT_HASH": "sha256:20008hhh",
        "IS_CURRENT": True,
        "UPLOAD_DATE": "2021-08-11",
        "LOCKED": False,
    },
    {
        "DOC_ID": "DOC-20009",
        "ATTACHMENT_ID": "900001119",
        "CONTENT_TEXT": "Exam findings related to auto casualty claim denials at Providence Auto Group.",
        "FILE_PATH": "RI/Exams/900001119/providence_auto_exam.pdf",
        "BUSINESS_AREA": "Exams",
        "DOC_STATE": "RI",
        "CONTENT_HASH": "sha256:20009iii",
        "IS_CURRENT": True,
        "UPLOAD_DATE": "2021-09-01",
        "LOCKED": False,
    },
    {
        "DOC_ID": "DOC-20010",
        "ATTACHMENT_ID": "900001120",
        "CONTENT_TEXT": "Accident report involving cyclist struck by delivery truck near Bristol. Witness statements conflict.",
        "FILE_PATH": "RI/Market Regulation/900001120/bristol_cyclist_accident.pdf",
        "BUSINESS_AREA": "Market Regulation",
        "DOC_STATE": "RI",
        "CONTENT_HASH": "sha256:20010jjj",
        "IS_CURRENT": True,
        "UPLOAD_DATE": "2021-09-20",
        "LOCKED": False,
    }
]

SBS_ATTACHMENTS = {
    "890786543": {
        "FILE_NAME": "accident_investigation_sd.docx",
        "TRACKING_ID": "12350",
    },
    "890786544": {
        "FILE_NAME": "jane_doe_dispute_sd.pdf",
        "TRACKING_ID": "12351",
    },
    "890786545": {
        "FILE_NAME": "uniformdoc_sd.pdf",
        "TRACKING_ID": "12352",
    },
    "890786546": {
        "FILE_NAME": "accident_detail_sd.pdf",
        "TRACKING_ID": "12345",
    },
    "890786547": {
        "FILE_NAME": "cornwall_motorcycle_club_id.docx",
        "TRACKING_ID": "12355",
    },
    "900001111": {"FILE_NAME": "providence_delivery_accident.pdf", "TRACKING_ID": "20001"},
    "900001112": {"FILE_NAME": "roof_damage_complaint.docx", "TRACKING_ID": "20002"},
    "900001113": {"FILE_NAME": "ocean_state_exam_findings.pdf", "TRACKING_ID": "20003"},
    "900001114": {"FILE_NAME": "newport_rental_accident.pdf", "TRACKING_ID": "20004"},
    "900001115": {"FILE_NAME": "unfair_claims_handling.pdf", "TRACKING_ID": "20005"},
    "900001116": {"FILE_NAME": "atlantic_life_exam.pdf", "TRACKING_ID": "20006"},
    "900001117": {"FILE_NAME": "cranston_fleet_accident.docx", "TRACKING_ID": "20007"},
    "900001118": {"FILE_NAME": "pawtucket_fire_claim.pdf", "TRACKING_ID": "20008"},
    "900001119": {"FILE_NAME": "providence_auto_exam.pdf", "TRACKING_ID": "20009"},
    "900001120": {"FILE_NAME": "bristol_cyclist_accident.pdf", "TRACKING_ID": "20010"}
}

SBS_CASES = {
    "12350": {
        "CASE_TYPE": "Complaints",
        "CASE_STATUS": "Open",
        "INVESTIGATOR": "A. Miller",
        "ENTITY_NAME": "Prairie Plains Mutual Insurance Company",
        "CASE_INITIATED": "2019-09-28",
        "CASE_OPENED": "2019-10-01",
        "CASE_CLOSED": None,
        "NAIC_GROUP_NUMBER": "9083",
        "CASE_SUBTYPE": "Inquiry",
        "LOI": "Property",
        "DISPOSITION": None,
    },
    "12351": {
        "CASE_TYPE": "Enforcement",
        "CASE_STATUS": "Closed",
        "INVESTIGATOR": "R. Vance",
        "ENTITY_NAME": "Black Hills Mutual Insurance Company",
        "CASE_INITIATED": "2019-12-18",
        "CASE_OPENED": "2019-12-20",
        "CASE_CLOSED": "2020-01-15",
        "NAIC_GROUP_NUMBER": "8056",
        "CASE_SUBTYPE": "Investigations",
        "LOI": "Casualty",
        "DISPOSITION": "Settled",
    },
    "12352": {
        "CASE_TYPE": "Complaints",
        "CASE_STATUS": "Open",
        "INVESTIGATOR": "A. Miller",
        "ENTITY_NAME": "Dakota Plains Insurance Company",
        "CASE_INITIATED": "2020-01-03",
        "CASE_OPENED": "2020-01-05",
        "CASE_CLOSED": None,
        "NAIC_GROUP_NUMBER": "1234",
        "CASE_SUBTYPE": "Inquiry",
        "LOI": "Auto",
        "DISPOSITION": None,
    },
    "12345": {
        "CASE_TYPE": "Market Conduct Exams",
        "CASE_STATUS": "Under Review",
        "INVESTIGATOR": "C. Davis",
        "ENTITY_NAME": "Missouri River Life Underwriters",
        "CASE_INITIATED": "2020-01-20",
        "CASE_OPENED": "2020-01-22",
        "CASE_CLOSED": None,
        "NAIC_GROUP_NUMBER": "5678",
        "CASE_SUBTYPE": "Market Conduct",
        "LOI": "Life",
        "DISPOSITION": None,
    },
    "12355": {
        "CASE_TYPE": "Market Conduct Exams",
        "CASE_STATUS": "Closed",
        "INVESTIGATOR": "C. Davis",
        "ENTITY_NAME": "Snake River Group LLC",
        "CASE_INITIATED": "2020-02-08",
        "CASE_OPENED": "2020-02-10",
        "CASE_CLOSED": "2020-03-01",
        "NAIC_GROUP_NUMBER": "7777",
        "CASE_SUBTYPE": "Market Conduct",
        "LOI": "Casualty",
        "DISPOSITION": "Dismissed",
    },
        "20001": {
        "CASE_TYPE": "Market Regulation",
        "CASE_STATUS": "Open",
        "INVESTIGATOR": "J. Reynolds",
        "ENTITY_NAME": "Ocean State Delivery Services LLC",
        "CASE_INITIATED": "2021-03-12",
        "CASE_OPENED": "2021-03-14",
        "CASE_CLOSED": None,
        "NAIC_GROUP_NUMBER": "9001",
        "CASE_SUBTYPE": "Accident",
        "LOI": "Auto",
        "DISPOSITION": None
    },
    "20002": {
        "CASE_TYPE": "Complaints",
        "CASE_STATUS": "Pending",
        "INVESTIGATOR": "L. Santos",
        "ENTITY_NAME": "Rhode Island Home Insurance Group",
        "CASE_INITIATED": "2021-04-01",
        "CASE_OPENED": "2021-04-02",
        "CASE_CLOSED": None,
        "NAIC_GROUP_NUMBER": "9002",
        "CASE_SUBTYPE": "Property",
        "LOI": "Homeowners",
        "DISPOSITION": None
    },
    "20003": {
        "CASE_TYPE": "Market Conduct Exams",
        "CASE_STATUS": "Under Review",
        "INVESTIGATOR": "C. Davis",
        "ENTITY_NAME": "Ocean State Mutual Insurance Company",
        "CASE_INITIATED": "2021-05-08",
        "CASE_OPENED": "2021-05-10",
        "CASE_CLOSED": None,
        "NAIC_GROUP_NUMBER": "9003",
        "CASE_SUBTYPE": "Casualty",
        "LOI": "Casualty",
        "DISPOSITION": None
    },
    "20004": {
        "CASE_TYPE": "Market Regulation",
        "CASE_STATUS": "Open",
        "INVESTIGATOR": "A. Miller",
        "ENTITY_NAME": "Newport Rental Car Group",
        "CASE_INITIATED": "2021-05-30",
        "CASE_OPENED": "2021-06-01",
        "CASE_CLOSED": None,
        "NAIC_GROUP_NUMBER": "9004",
        "CASE_SUBTYPE": "Accident",
        "LOI": "Auto",
        "DISPOSITION": None
    },
    "20005": {
        "CASE_TYPE": "Complaints",
        "CASE_STATUS": "Closed",
        "INVESTIGATOR": "R. Vance",
        "ENTITY_NAME": "Narragansett Bay Insurance Company",
        "CASE_INITIATED": "2021-06-15",
        "CASE_OPENED": "2021-06-18",
        "CASE_CLOSED": "2021-07-01",
        "NAIC_GROUP_NUMBER": "9005",
        "CASE_SUBTYPE": "Inquiry",
        "LOI": "Property",
        "DISPOSITION": "Resolved"
    },
    "20006": {
        "CASE_TYPE": "Market Conduct Exams",
        "CASE_STATUS": "Closed",
        "INVESTIGATOR": "C. Davis",
        "ENTITY_NAME": "Atlantic Life Group",
        "CASE_INITIATED": "2021-07-01",
        "CASE_OPENED": "2021-07-03",
        "CASE_CLOSED": "2021-07-20",
        "NAIC_GROUP_NUMBER": "9006",
        "CASE_SUBTYPE": "Life",
        "LOI": "Life",
        "DISPOSITION": "Completed"
    },
    "20007": {
        "CASE_TYPE": "Market Regulation",
        "CASE_STATUS": "Open",
        "INVESTIGATOR": "J. Reynolds",
        "ENTITY_NAME": "Cranston Commercial Fleet Services",
        "CASE_INITIATED": "2021-07-20",
        "CASE_OPENED": "2021-07-22",
        "CASE_CLOSED": None,
        "NAIC_GROUP_NUMBER": "9007",
        "CASE_SUBTYPE": "Accident",
        "LOI": "Auto",
        "DISPOSITION": None
    },
    "20008": {
        "CASE_TYPE": "Complaints",
        "CASE_STATUS": "Pending",
        "INVESTIGATOR": "L. Santos",
        "ENTITY_NAME": "Pawtucket Home & Fire Insurance",
        "CASE_INITIATED": "2021-08-10",
        "CASE_OPENED": "2021-08-11",
        "CASE_CLOSED": None,
        "NAIC_GROUP_NUMBER": "9008",
        "CASE_SUBTYPE": "Property",
        "LOI": "Homeowners",
        "DISPOSITION": None
    },
    "20009": {
        "CASE_TYPE": "Market Conduct Exams",
        "CASE_STATUS": "Under Review",
        "INVESTIGATOR": "C. Davis",
        "ENTITY_NAME": "Providence Auto Group",
        "CASE_INITIATED": "2021-08-30",
        "CASE_OPENED": "2021-09-01",
        "CASE_CLOSED": None,
        "NAIC_GROUP_NUMBER": "9009",
        "CASE_SUBTYPE": "Casualty",
        "LOI": "Auto",
        "DISPOSITION": None
    },
    "20010": {
        "CASE_TYPE": "Market Regulation",
        "CASE_STATUS": "Open",
        "INVESTIGATOR": "A. Miller",
        "ENTITY_NAME": "Bristol Delivery & Logistics",
        "CASE_INITIATED": "2021-09-18",
        "CASE_OPENED": "2021-09-20",
        "CASE_CLOSED": None,
        "NAIC_GROUP_NUMBER": "9010",
        "CASE_SUBTYPE": "Accident",
        "LOI": "Auto",
        "DISPOSITION": None
    }
}

# ==============================================================================
# FIELD / PAYLOAD CONFIGURATION (DOCUMENT-ONLY FOR CORTEX)
# ==============================================================================

FIELD_MATRIX = {
    "Market Regulation": {
        "base": ["DOC_ID", "ATTACHMENT_ID", "CONTENT_TEXT", "BUSINESS_AREA",
                 "DOC_STATE", "IS_CURRENT"],
    },
    "Complaints": {
        "base": ["DOC_ID", "ATTACHMENT_ID", "CONTENT_TEXT", "BUSINESS_AREA",
                 "DOC_STATE", "IS_CURRENT"],
    },
    "Exams": {
        "base": ["DOC_ID", "ATTACHMENT_ID", "CONTENT_TEXT", "BUSINESS_AREA",
                 "DOC_STATE", "IS_CURRENT"],
    },
}

PII_FIELDS = {"ENTITY_NAME", "INVESTIGATOR"}

# ==============================================================================
# CSS
# ==============================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

html, body, [class*="css"] { font-family: 'Roboto', sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0 !important; }

/* TOP HEADER + LEGEND */

.sdp-top-btn {
    border: 1px solid #d0d4e4;
    background: #ffffff;
    color: #3f51b5;
    font-size: 12px;
    padding: 6px 12px;
    border-radius: 4px;
    margin-left: 8px;
    cursor: pointer;
}

.sdp-legend {
    background: #fafafa;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 8px 14px;
    margin-bottom: 16px;
    display: flex;
    gap: 18px;
    align-items: center;
    font-size: 12px;
    color: #555;
}

/* NAV BAR */

.sdp-nav {
    background:#3f51b5;
    color:white;
    padding:10px 20px;
    display:flex;
    align-items:center;
    justify-content:space-between;
    margin-bottom:18px;
}
.sdp-nav-title {
    font-size:18px;
    font-weight:500;
}
.sdp-nav-persona {
    background:rgba(255,255,255,.18);
    padding:5px 12px;
    border-radius:4px;
    font-size:12px;
}

/* CARD HEADERS + BODY */

.sdp-card-header {
    background:#f5f7fb;
    border:1px solid #e0e0e0;
    border-bottom:none;
    border-radius:6px 6px 0 0;
    padding:10px 16px;
}
.sdp-card-header h2 {
    font-size:14px;
    font-weight:600;
    color:#333;
    margin:0;
}

.sdp-card-body {
    background:#ffffff;
    border:1px solid #e0e0e0;
    border-radius:0 0 6px 6px;
    padding:16px 16px 12px 16px;
    margin-bottom:18px;
}

/* FORM LABELS */

.sdp-label {
    font-size:11px;
    font-weight:600;
    color:#444;
    margin-bottom:2px;
    display:block;
}

.sdp-hint {
    font-size:11px;
    color:#999;
    font-style:italic;
}

.req {
    color:#f44336;
    font-weight:700;
}

.smart-badge {
    display:inline-flex;
    font-size:11px;
    color:#7c4dff;
    background:#ede7f6;
    padding:2px 8px;
    border-radius:12px;
    font-weight:600;
    margin-left:6px;
}

/* INPUTS */

.stTextInput, .stTextArea, .stSelectbox {
    font-size:13px !important;
}

/* TABLE */

.sdp-snippet {
    font-style:italic;
    color:#555;
    display:block;
    max-width:520px;
}

.sdp-snippet mark {
    background:#fff59d;
    padding:0 2px;
    border-radius:2px;
    font-style:normal;
}

/* BADGES */

.badge-full {
    background:#e8f5e9;
    color:#2e7d32;
    padding:3px 9px;
    border-radius:12px;
    font-size:11px;
    font-weight:600;
}

.badge-masked {
    background:#fff3e0;
    color:#e65100;
    padding:3px 9px;
    border-radius:12px;
    font-size:11px;
    font-weight:600;
}

.badge-denied {
    background:#ffebee;
    color:#c62828;
    padding:3px 9px;
    border-radius:12px;
    font-size:11px;
    font-weight:600;
}

/* BUTTONS */

div[data-testid="stButton"] > button {
    font-size:13px !important;
    padding:6px 14px !important;
    border-radius:4px !important;
}

/* SECURITY NOTE */

.security-note {
    background:#eef4ff;
    border-left:4px solid #3f51b5;
    padding:12px 16px;
    margin:12px 0;
    font-size:13px;
}

</style>
""", unsafe_allow_html=True)

# ==============================================================================
# BACKEND SIMULATION (SNOWFLAKE-READY)
# ==============================================================================

def mask_value(value):
    if not value:
        return value

    if "@" in value:
        return "[EMAIL MASKED]"

    if re.fullmatch(r"\d{3}-\d{2}-\d{4}", value):
        return "***-**-****"

    words = value.split()
    masked = []
    for word in words:
        if word.upper() in {"LLC", "INC", "INSURANCE", "LIFE", "UNDERWRITERS", "COMPANY"}:
            masked.append(word)
        else:
            masked.append(word[:1] + "*" * max(len(word) - 1, 1))
    return " ".join(masked)


def mask_text(text, entity_name=None):
    if not text:
        return text

    if entity_name:
        text = text.replace(entity_name, mask_value(entity_name))

    text = re.sub(r"\b[\w.+-]+@[\w.-]+\.\w+\b", "[EMAIL MASKED]", text)
    text = re.sub(r"\b(?:\d{3}[-.\s]){2}\d{4}\b", "[PHONE MASKED]", text)
    text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "***-**-****", text)
    return text


def authorized_documents(user, selected_ba):
    return [
        d for d in DOC_SEARCH_CONTENT
        if d["DOC_STATE"] == user["state"]
        and d["BUSINESS_AREA"] == selected_ba
        and selected_ba in user["business_areas"]
        and d["IS_CURRENT"]
    ]


def build_search_payload(user, query, selected_ba, filters):
    allowed = FIELD_MATRIX[selected_ba]["base"]

    columns = allowed  # document-only; SBS join happens after search

    cortex_filter = {
        "@and": [
            {"@eq": {"DOC_STATE": user["state"]}},
            {"@eq": {"BUSINESS_AREA": selected_ba}},
            {"@eq": {"IS_CURRENT": True}},
        ]
    }

    return {
        "query": query,
        "columns": columns,
        "filter": cortex_filter,
        "limit": 10,
        "authorization_boundary": "Spring Boot",
        "raw_document_access": "backend controlled",
    }


def run_search(user, query, selected_ba, filters):
    docs = authorized_documents(user, selected_ba)
    q = query.strip().lower()

    results = []

    for d in docs:
        attachment = SBS_ATTACHMENTS.get(d["ATTACHMENT_ID"])
        if not attachment:
            continue
        case = SBS_CASES.get(attachment["TRACKING_ID"])
        if not case:
            continue

        content_text = d["CONTENT_TEXT"]
        file_name = attachment["FILE_NAME"]
        entity_name = case["ENTITY_NAME"]
        investigator = case["INVESTIGATOR"]

        if q:
            haystack = (content_text + " " + file_name + " " + entity_name + " " + investigator).lower()
            terms = q.split()
            if not all(term in haystack for term in terms):
                continue

        if user["unmasked_pii"]:
            display_file_name = file_name
            display_entity = entity_name
            display_investigator = investigator
            snippet = content_text
        else:
            display_file_name = mask_value(file_name)
            display_entity = mask_value(entity_name)
            display_investigator = mask_value(investigator)
            snippet = mask_text(content_text, entity_name=entity_name)

        if q:
            for term in q.split():
                snippet = re.sub(
                    re.escape(term),
                    lambda m: f"<mark>{escape(m.group(0))}</mark>",
                    snippet,
                    flags=re.IGNORECASE,
                )

        result = {
            "DOC_ID": d["DOC_ID"],
            "ATTACHMENT_ID": d["ATTACHMENT_ID"],
            "TRACKING_ID": attachment["TRACKING_ID"],
            "FILE_NAME": display_file_name,
            "DOCUMENT_TITLE": file_name,  # for demo; real title could be separate
            "DOCUMENT_DATE": d["UPLOAD_DATE"],
            "DOCUMENT_TYPE": "Document",  # placeholder
            "STATE": d["DOC_STATE"],
            "BUSINESS_AREA": d["BUSINESS_AREA"],
            "SNIPPET": snippet,
            "CASE_TYPE": case["CASE_TYPE"],
            "CASE_STATUS": case["CASE_STATUS"],
            "INVESTIGATOR_DISPLAY": display_investigator,
            "ENTITY_NAME_DISPLAY": display_entity,
            "LOI_DISPLAY": case["LOI"],
            "LOCKED": d["LOCKED"],
            "CAN_DOWNLOAD": user["can_download"],
            "_doc": d,
            "_attachment": attachment,
            "_case": case,
        }

        results.append(result)

    return results


def download_document(user, doc_row, case_row):
    CONFIDENTIAL_CASE_TYPES = {
        "Enforcement",
        "Market Conduct Exams",
        "Investigations",
        "Multi-State",
        "Securities",
        "PBM",
        "Fraud",
    }
    case_type = case_row["CASE_TYPE"]

    if user["role"] != "STATE_REGULATOR" and case_type in CONFIDENTIAL_CASE_TYPES:
        return False, "Download denied: confidential case type requires regulator access."

    if not user["can_download"]:
        return False, "Download denied by authorization policy."
    if doc_row["DOC_STATE"] != user["state"]:
        return False, "Download denied: jurisdiction mismatch."
    if doc_row["BUSINESS_AREA"] not in user["business_areas"]:
        return False, "Download denied: business-area entitlement."
    return True, f"Authorized download: {doc_row['DOC_ID']} / {doc_row['FILE_PATH']}"

# ==============================================================================
# SESSION
# ==============================================================================

if "selected_user" not in st.session_state:
    st.session_state.selected_user = list(USERS)[0]
if "results" not in st.session_state:
    st.session_state.results = None
if "payload" not in st.session_state:
    st.session_state.payload = None

user = USERS[st.session_state.selected_user]

# ==============================================================================
# HEADER
# ==============================================================================

pii_badge = '<span class="badge-full">UNMASKED PII</span>' if user["unmasked_pii"] else '<span class="badge-masked">MASKED PII</span>'
download_badge = '<span class="badge-full">DOWNLOAD ENABLED</span>' if user["can_download"] else '<span class="badge-denied">DOWNLOAD DENIED</span>'

st.markdown(f"""
<div class="sdp-nav">
  <span class="sdp-nav-title">Smart Document Platform — Search</span>
  <span class="sdp-nav-persona">
    {user['username']} · {user['role']} · {user['state']} · {pii_badge} · {download_badge}
  </span>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
  <div style="font-size:20px;font-weight:500;color:#333;">
    Smart Document Search
  </div>
  <div>
    <button class="sdp-top-btn">Global Search</button>
    <button class="sdp-top-btn">Column Picker</button>
  </div>
</div>
<div class="sdp-legend">
  <span><span class="req">*</span>&nbsp; Required Field</span>
  <span><span class="smart-badge">✦ Smart</span>&nbsp; AI-powered search</span>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns([3, 3, 1])
with c1:
    st.caption("Desktop prototype — S3 → Parse → Chunk → Governance → Search → UI")
with c3:
    selected = st.selectbox("Persona", list(USERS), index=list(USERS).index(st.session_state.selected_user))
    if selected != st.session_state.selected_user:
        st.session_state.selected_user = selected
        st.session_state.results = None
        st.session_state.payload = None
        st.rerun()

# ==============================================================================
# ARCHITECTURE VIEW
# ==============================================================================

with st.expander("Architecture / Data Flow", expanded=False):
    st.markdown("""
**Prototype flow**

`S3 → DOC_SEARCH_CONTENT (DOC_ID, ATTACHMENT_ID, CONTENT_TEXT, FILE_PATH, BUSINESS_AREA, DOC_STATE, IS_CURRENT) → Spring Boot authorization → Cortex Search → SBS.ATTACHMENT / MR_CASE join → UI`

**Structured relationship**

`DOC_ID` is the unique document identifier.  
`ATTACHMENT_ID` is the bridge to SBS.  
`TRACKING_ID` and case metadata are resolved from SBS, not stored in the document table.

**Security rule**

The UI does not choose authorization, masking, State, or raw-document access. Spring Boot is simulated as the authorization boundary.
""")

# ==============================================================================
# SEARCH UI
# ==============================================================================

st.markdown('<div class="sdp-card-header"><h2>Search Criteria</h2></div>', unsafe_allow_html=True)
st.markdown('<div class="sdp-card-body">', unsafe_allow_html=True)

st.markdown('<span class="sdp-label">Business Area <span class="req">*</span></span>', unsafe_allow_html=True)
business_area = st.selectbox(
    "Business Area",
    user["business_areas"],
    label_visibility="collapsed",
)

st.markdown('<span class="sdp-label">Search Document Contents <span class="req">*</span> <span class="smart-badge">✦ Smart</span></span>', unsafe_allow_html=True)
query = st.text_area(
    "Search Document Contents",
    placeholder="Search within the text of all attached documents...",
    height=90,
    label_visibility="collapsed",
)
st.markdown('<span class="sdp-hint">Search within the text of all attached documents.</span>', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

with st.expander("Case Details", expanded=True):
    st.markdown('<div class="sdp-card-body">', unsafe_allow_html=True)
    a, b = st.columns(2)
    with a:
        case_type = st.selectbox("Case Type", ["", "Complaints", "Enforcement", "Market Conduct Exams"])
    with b:
        tracking_id = st.text_input("Tracking ID", placeholder="e.g. 999")
    a, b = st.columns(2)
    with a:
        investigator = st.text_input("Investigator", placeholder="Search by Investigator name")
        st.markdown('<span class="sdp-hint">Searches Primary and Secondary investigators.</span>', unsafe_allow_html=True)
    with b:
        status = st.selectbox("Status", ["", "Open", "Closed", "Under Review", "Pending"])
    st.markdown('</div>', unsafe_allow_html=True)

with st.expander("Entity", expanded=False):
    st.markdown('<div class="sdp-card-body">', unsafe_allow_html=True)
    entity = st.text_input("Entity Name", placeholder="Search by person or company name")
    st.markdown('<span class="sdp-hint">Handles partial names, company names, or combinations.</span>', unsafe_allow_html=True)
    naic_group = st.text_input("NAIC Group Number", placeholder="e.g. 9083")
    st.markdown('</div>', unsafe_allow_html=True)

with st.expander("Dates", expanded=False):
    st.markdown('<div class="sdp-card-body">', unsafe_allow_html=True)
    d1, d2 = st.columns(2)
    with d1:
        start_date = st.date_input("Start Date", value=None)
    with d2:
        end_date = st.date_input("End Date", value=None)
    st.markdown('</div>', unsafe_allow_html=True)

with st.expander("Document", expanded=False):
    st.markdown('<div class="sdp-card-body">', unsafe_allow_html=True)
    doc_name = st.text_input("Document Name", placeholder="e.g., accident report, policy letter")
    st.markdown('<span class="sdp-hint">Smart search over document names.</span>', unsafe_allow_html=True)
    file_type = st.selectbox("File Type", ["", ".pdf", ".docx"])
    st.markdown('</div>', unsafe_allow_html=True)

with st.expander("Additional Details", expanded=False):
    st.markdown('<div class="sdp-card-body">', unsafe_allow_html=True)
    ad1, ad2, ad3 = st.columns(3)
    with ad1:
        case_subtype = st.text_input("Case Sub-Type", placeholder="e.g., Inquiry, Market Conduct")
    with ad2:
        state_keyword = st.text_input("State Keyword", placeholder="e.g., hazardous waste")
    with ad3:
        reason = st.text_input("Reason", placeholder="Reason or narrative keyword")
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# EXECUTE
# ==============================================================================

btn_cols = st.columns([1, 1, 6])
with btn_cols[0]:
    search_clicked = st.button("🔍 Search", type="primary")
with btn_cols[1]:
    reset_clicked = st.button("Reset")

if search_clicked:
    if not query.strip() or len(query.strip()) < 3:
        st.error("Search Document Contents is required and must contain at least 3 characters.")
    else:
        filters = {
            "case_type": case_type,
            "status": status,
            "investigator": investigator,
            "entity": entity,
            "tracking_id": tracking_id,
            "file_type": file_type,
        }

        st.session_state.results = run_search(user, query, business_area, filters)
        st.session_state.payload = build_search_payload(user, query, business_area, filters)

if reset_clicked:
    st.session_state.results = None
    st.session_state.payload = None
    st.rerun()

# ==============================================================================
# RESULTS
# ==============================================================================

if st.session_state.results is not None:
    results = st.session_state.results

    st.markdown(f"### Search Results `{len(results)}`")
    if not results:
        st.info("No documents match the search and authorization criteria.")
    else:
        for r in results:
            with st.container(border=True):
                cols = st.columns([1.3, 1.1, 2.0, 3.5, 1.2])
                cols[0].markdown(f"**DOC_ID**  \n{r['DOC_ID']}")
                cols[1].markdown(f"**Tracking ID**  \n{r['TRACKING_ID']}")
                cols[2].markdown(f"**Document**  \n{r['FILE_NAME']}")
                cols[3].markdown(
                    f"**Content**  \n<span class='sdp-snippet'>“{r['SNIPPET']}”</span>",
                    unsafe_allow_html=True,
                )
                with cols[4]:
                    if r["CAN_DOWNLOAD"]:
                        if st.button("⬇ Download", key=f"dl_{r['DOC_ID']}"):
                            ok, msg = download_document(user, r["_doc"], r["_case"])
                            if ok:
                                st.success(msg)
                            else:
                                st.error(msg)
                    else:
                        st.markdown('<span class="badge-denied">RESTRICTED</span>', unsafe_allow_html=True)

        with st.expander("Result Metadata", expanded=False):
            m1, m2, m3 = st.columns(3)
            m1.markdown(f"**Document Type**  \n{results[0]['DOCUMENT_TYPE']}")
            m1.markdown(f"**Document Date**  \n{results[0]['DOCUMENT_DATE']}")
            m1.markdown(f"**State**  \n{results[0]['STATE']}")
            m2.markdown(f"**Business Area**  \n{results[0]['BUSINESS_AREA']}")
            m2.markdown(f"**Case Type**  \n{results[0]['CASE_TYPE']}")
            m2.markdown(f"**Status**  \n{results[0]['CASE_STATUS']}")
            m3.markdown(f"**Investigator**  \n{results[0]['INVESTIGATOR_DISPLAY']}")
            m3.markdown(f"**Entity**  \n{results[0]['ENTITY_NAME_DISPLAY']}")
            m3.markdown(f"**LOI**  \n{results[0]['LOI_DISPLAY']}")

# ==============================================================================
# GOVERNANCE / INTEGRATION INSPECTOR
# ==============================================================================

with st.expander("🛠 Governance / Integration Inspector", expanded=False):
    tab1, tab2, tab3 = st.tabs(["Backend Payload", "Authorization Trace", "Document Relationship"])

    with tab1:
        st.caption("This is the payload Spring Boot constructs. The browser does not choose authorization fields.")
        if st.session_state.payload:
            st.json(st.session_state.payload)
        else:
            st.info("Run a search to view the generated payload.")

    with tab2:
        st.json({
            "authenticated_user": user["username"],
            "role": user["role"],
            "jurisdiction": user["jurisdiction"],
            "enforced_state": user["state"],
            "entitled_business_areas": user["business_areas"],
            "pii_representation": "FULL" if user["unmasked_pii"] else "MASKED",
            "raw_download": user["can_download"],
            "authorization_boundary": "Spring Boot",
            "cortex_search_is_authorization_boundary": False,
        })

    with tab3:
        st.json({
            "document": {
                "DOC_ID": "DOC-10004",
                "ATTACHMENT_ID": "890786546",
                "FILE_PATH": "SD/Exams/890786546/accident_detail_sd.pdf",
            },
            "relationship": {
                "ATTACHMENT_ID": "→ SBS.ATTACHMENT.ATTACHMENT_ID",
                "TRACKING_ID": "→ MR_CASE.TRACKING_ID",
                "structured_case_metadata": "→ SBS case tables",
            },
            "search_content": {
                "CONTENT_TEXT": "→ parsed document text",
            },
            "governance": {
                "DOC_STATE": "→ entitlement / jurisdiction",
                "BUSINESS_AREA": "→ entitlement",
                "PII": "→ full or search-safe representation via SBS join",
            },
        })

# ==============================================================================
# SECURITY TEST SCENARIOS
# ==============================================================================

with st.expander("🧪 Security Test Scenarios", expanded=False):
    st.markdown("""
Use the persona switcher and search to demonstrate:

1. **SD regulator** — sees full permitted metadata and can download.
2. **SD analyst** — sees masked PII and only SD Exams.
3. **ID analyst** — sees only ID Exams and cannot download SD documents.
4. **State isolation** — backend always applies the authenticated DOC_STATE.
5. **Business-area isolation** — backend rejects areas outside entitlement.
6. **PII masking** — entity, investigator, and filenames use the permitted representation.
7. **Raw access** — download is independently authorized by the backend.
8. **Payload control** — the backend, not the UI, selects response fields and joins SBS metadata.
""")
