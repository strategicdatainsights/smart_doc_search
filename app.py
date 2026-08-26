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
# DOC_SEARCH_CONTENT (document-owned), SBS.ATTACHMENT, MR_CASE
# ==============================================================================

DOC_SEARCH_CONTENT = [
    # --- Original SD / ID docs ---
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
        "DOCUMENT_TITLE": "Accident Investigation Report — Sioux Falls",
        "DOCUMENT_TYPE": "Accident Report",
        "PAGE_COUNT": 4,
        "MIME_TYPE": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "LANGUAGE": "en",
        "HAS_IMAGES": True,
        "HAS_TABLES": False,
        "EXTRACTION_CONFIDENCE": 0.94,
        "KEY_PHRASES": ["accident", "Sioux Falls", "Prairie Plains"],
        "TOPICS": ["Auto", "Accident"],
        "SUMMARY": "Accident near Sioux Falls reported by Jane Smith to Prairie Plains Mutual.",
        "GEO_LOCATION": "Sioux Falls, SD",
        "EVENT_DATE": "2019-09-30",
        "PARTIES_MENTIONED": ["Jane Smith", "Prairie Plains Mutual Insurance Company"],
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
        "DOCUMENT_TITLE": "Formal Dispute — Rapid City Accident",
        "DOCUMENT_TYPE": "Dispute Letter",
        "PAGE_COUNT": 3,
        "MIME_TYPE": "application/pdf",
        "LANGUAGE": "en",
        "HAS_IMAGES": False,
        "HAS_TABLES": False,
        "EXTRACTION_CONFIDENCE": 0.91,
        "KEY_PHRASES": ["formal dispute", "Rapid City", "Black Hills"],
        "TOPICS": ["Auto", "Dispute"],
        "SUMMARY": "Formal dispute filed by claimant regarding Rapid City accident.",
        "GEO_LOCATION": "Rapid City, SD",
        "EVENT_DATE": "2019-12-19",
        "PARTIES_MENTIONED": ["Jane Doe", "Black Hills Mutual Insurance Company"],
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
        "DOCUMENT_TITLE": "Complaint — Vehicle Loss near Pierre",
        "DOCUMENT_TYPE": "Complaint",
        "PAGE_COUNT": 2,
        "MIME_TYPE": "application/pdf",
        "LANGUAGE": "en",
        "HAS_IMAGES": False,
        "HAS_TABLES": False,
        "EXTRACTION_CONFIDENCE": 0.93,
        "KEY_PHRASES": ["complaint", "claim denial", "vehicle loss"],
        "TOPICS": ["Auto", "Complaint"],
        "SUMMARY": "Complaint regarding denial of vehicle loss claim near Pierre.",
        "GEO_LOCATION": "Pierre, SD",
        "EVENT_DATE": "2020-01-02",
        "PARTIES_MENTIONED": [],
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
        "DOCUMENT_TITLE": "Exam — Accident Damage Assessment",
        "DOCUMENT_TYPE": "Exam Report",
        "PAGE_COUNT": 5,
        "MIME_TYPE": "application/pdf",
        "LANGUAGE": "en",
        "HAS_IMAGES": True,
        "HAS_TABLES": True,
        "EXTRACTION_CONFIDENCE": 0.95,
        "KEY_PHRASES": ["total loss", "accident", "Sioux Falls"],
        "TOPICS": ["Auto", "Exam"],
        "SUMMARY": "Exam report detailing total loss assessment after accident near Sioux Falls.",
        "GEO_LOCATION": "Sioux Falls, SD",
        "EVENT_DATE": "2020-01-20",
        "PARTIES_MENTIONED": [],
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
        "DOCUMENT_TITLE": "Exam — Snake River Group Accident Assessment",
        "DOCUMENT_TYPE": "Exam Report",
        "PAGE_COUNT": 6,
        "MIME_TYPE": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "LANGUAGE": "en",
        "HAS_IMAGES": True,
        "HAS_TABLES": True,
        "EXTRACTION_CONFIDENCE": 0.92,
        "KEY_PHRASES": ["third party inspector", "Snake River Group", "Boise"],
        "TOPICS": ["Casualty", "Exam"],
        "SUMMARY": "Exam report from third-party inspector for Snake River Group accident near Boise.",
        "GEO_LOCATION": "Boise, ID",
        "EVENT_DATE": "2020-02-08",
        "PARTIES_MENTIONED": ["Snake River Group LLC"],
    },
    # --- Additional SD / ID docs for richer search ---
    {
        "DOC_ID": "DOC-SD-30001",
        "ATTACHMENT_ID": "ATT-SD-30001",
        "CONTENT_TEXT": "Accident near Sioux Falls involving a commercial van. Adjuster noted inconsistent statements and possible policy lapse.",
        "FILE_PATH": "SD/Market Regulation/ATT-SD-30001/sioux_falls_commercial_van.pdf",
        "BUSINESS_AREA": "Market Regulation",
        "DOC_STATE": "SD",
        "CONTENT_HASH": "sha256:sd30001",
        "IS_CURRENT": True,
        "UPLOAD_DATE": "2022-01-03",
        "LOCKED": False,
        "DOCUMENT_TITLE": "Accident — Commercial Van near Sioux Falls",
        "DOCUMENT_TYPE": "Accident Report",
        "PAGE_COUNT": 4,
        "MIME_TYPE": "application/pdf",
        "LANGUAGE": "en",
        "HAS_IMAGES": True,
        "HAS_TABLES": False,
        "EXTRACTION_CONFIDENCE": 0.94,
        "KEY_PHRASES": ["commercial van", "policy lapse", "Sioux Falls"],
        "TOPICS": ["Auto", "Accident"],
        "SUMMARY": "Accident involving commercial van near Sioux Falls with possible policy lapse.",
        "GEO_LOCATION": "Sioux Falls, SD",
        "EVENT_DATE": "2022-01-01",
        "PARTIES_MENTIONED": [],
    },
    {
        "DOC_ID": "DOC-ID-30010",
        "ATTACHMENT_ID": "ATT-ID-30010",
        "CONTENT_TEXT": "Accident damage assessment from third-party inspector retained by Snake River Group LLC near Boise.",
        "FILE_PATH": "ID/Exams/ATT-ID-30010/snake_river_damage_assessment.pdf",
        "BUSINESS_AREA": "Exams",
        "DOC_STATE": "ID",
        "CONTENT_HASH": "sha256:id30010",
        "IS_CURRENT": True,
        "UPLOAD_DATE": "2022-06-01",
        "LOCKED": False,
        "DOCUMENT_TITLE": "Exam — Snake River Damage Assessment",
        "DOCUMENT_TYPE": "Exam Report",
        "PAGE_COUNT": 7,
        "MIME_TYPE": "application/pdf",
        "LANGUAGE": "en",
        "HAS_IMAGES": True,
        "HAS_TABLES": True,
        "EXTRACTION_CONFIDENCE": 0.93,
        "KEY_PHRASES": ["damage assessment", "Snake River Group", "Boise"],
        "TOPICS": ["Casualty", "Exam"],
        "SUMMARY": "Detailed damage assessment for Snake River Group accident near Boise.",
        "GEO_LOCATION": "Boise, ID",
        "EVENT_DATE": "2022-05-30",
        "PARTIES_MENTIONED": ["Snake River Group LLC"],
    },
]

SBS_ATTACHMENTS = {
    "890786543": {
        "FILE_NAME": "accident_investigation_sd.docx",
        "TRACKING_ID": "12350",
        "ATTACHMENT_TYPE": "Report",
        "UPLOAD_USER": "adjuster.sd@carrier.com",
        "UPLOAD_TIMESTAMP": "2019-10-03T10:15:00Z",
    },
    "890786544": {
        "FILE_NAME": "jane_doe_dispute_sd.pdf",
        "TRACKING_ID": "12351",
        "ATTACHMENT_TYPE": "Letter",
        "UPLOAD_USER": "claimant.sd@consumer.com",
        "UPLOAD_TIMESTAMP": "2019-12-22T09:30:00Z",
    },
    "890786545": {
        "FILE_NAME": "uniformdoc_sd.pdf",
        "TRACKING_ID": "12352",
        "ATTACHMENT_TYPE": "Complaint",
        "UPLOAD_USER": "complaints.sd@doi.gov",
        "UPLOAD_TIMESTAMP": "2020-01-05T14:00:00Z",
    },
    "890786546": {
        "FILE_NAME": "accident_detail_sd.pdf",
        "TRACKING_ID": "12345",
        "ATTACHMENT_TYPE": "Exam Report",
        "UPLOAD_USER": "examiner.sd@doi.gov",
        "UPLOAD_TIMESTAMP": "2020-01-22T11:45:00Z",
    },
    "890786547": {
        "FILE_NAME": "cornwall_motorcycle_club_id.docx",
        "TRACKING_ID": "12355",
        "ATTACHMENT_TYPE": "Exam Report",
        "UPLOAD_USER": "examiner.id@doi.gov",
        "UPLOAD_TIMESTAMP": "2020-02-10T16:20:00Z",
    },
    "ATT-SD-30001": {
        "FILE_NAME": "sioux_falls_commercial_van.pdf",
        "TRACKING_ID": "SD-T30001",
        "ATTACHMENT_TYPE": "Accident Report",
        "UPLOAD_USER": "reg.sd@state.sd.gov",
        "UPLOAD_TIMESTAMP": "2022-01-03T09:00:00Z",
    },
    "ATT-ID-30010": {
        "FILE_NAME": "snake_river_damage_assessment.pdf",
        "TRACKING_ID": "ID-T30010",
        "ATTACHMENT_TYPE": "Exam Report",
        "UPLOAD_USER": "reg.id@state.id.gov",
        "UPLOAD_TIMESTAMP": "2022-06-01T13:30:00Z",
    },
}

SBS_CASES = {
    "12350": {
        "CASE_TYPE": "Complaints",
        "CASE_STATUS": "Open",
        "INVESTIGATOR": "A. Miller",
        "SECONDARY_INVESTIGATOR": None,
        "ENTITY_NAME": "Prairie Plains Mutual Insurance Company",
        "ENTITY_TYPE": "Insurer",
        "CASE_PRIORITY": "Medium",
        "RISK_CATEGORY": "Property",
        "CASE_NOTES": "Initial complaint received; awaiting carrier response.",
        "REGULATOR_COMMENTS": "Monitor for timely response.",
        "FOLLOW_UP_REQUIRED": True,
        "CASE_REGION": "Midwest",
        "CASE_DIVISION": "Complaints",
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
        "SECONDARY_INVESTIGATOR": "C. Davis",
        "ENTITY_NAME": "Black Hills Mutual Insurance Company",
        "ENTITY_TYPE": "Insurer",
        "CASE_PRIORITY": "High",
        "RISK_CATEGORY": "Casualty",
        "CASE_NOTES": "Formal dispute escalated to enforcement; settlement reached.",
        "REGULATOR_COMMENTS": "Ensure corrective action implemented.",
        "FOLLOW_UP_REQUIRED": False,
        "CASE_REGION": "Midwest",
        "CASE_DIVISION": "Enforcement",
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
        "SECONDARY_INVESTIGATOR": None,
        "ENTITY_NAME": "Dakota Plains Insurance Company",
        "ENTITY_TYPE": "Insurer",
        "CASE_PRIORITY": "Low",
        "RISK_CATEGORY": "Auto",
        "CASE_NOTES": "Vehicle loss complaint; documentation requested.",
        "REGULATOR_COMMENTS": "Awaiting carrier documentation.",
        "FOLLOW_UP_REQUIRED": True,
        "CASE_REGION": "Midwest",
        "CASE_DIVISION": "Complaints",
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
        "SECONDARY_INVESTIGATOR": "A. Miller",
        "ENTITY_NAME": "Missouri River Life Underwriters",
        "ENTITY_TYPE": "Insurer",
        "CASE_PRIORITY": "High",
        "RISK_CATEGORY": "Life",
        "CASE_NOTES": "Exam focusing on life claim handling and beneficiary practices.",
        "REGULATOR_COMMENTS": "Preliminary findings indicate documentation gaps.",
        "FOLLOW_UP_REQUIRED": True,
        "CASE_REGION": "Midwest",
        "CASE_DIVISION": "Exams",
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
        "SECONDARY_INVESTIGATOR": None,
        "ENTITY_NAME": "Snake River Group LLC",
        "ENTITY_TYPE": "Insurer",
        "CASE_PRIORITY": "Medium",
        "RISK_CATEGORY": "Casualty",
        "CASE_NOTES": "Exam completed; casualty claim handling reviewed.",
        "REGULATOR_COMMENTS": "No further action required.",
        "FOLLOW_UP_REQUIRED": False,
        "CASE_REGION": "West",
        "CASE_DIVISION": "Exams",
        "CASE_INITIATED": "2020-02-08",
        "CASE_OPENED": "2020-02-10",
        "CASE_CLOSED": "2020-03-01",
        "NAIC_GROUP_NUMBER": "7777",
        "CASE_SUBTYPE": "Market Conduct",
        "LOI": "Casualty",
        "DISPOSITION": "Dismissed",
    },
    "SD-T30001": {
        "CASE_TYPE": "Market Regulation",
        "CASE_STATUS": "Open",
        "INVESTIGATOR": "A. Miller",
        "SECONDARY_INVESTIGATOR": "J. Reynolds",
        "ENTITY_NAME": "Prairie Plains Mutual Insurance Company",
        "ENTITY_TYPE": "Insurer",
        "CASE_PRIORITY": "Medium",
        "RISK_CATEGORY": "Auto",
        "CASE_NOTES": "Commercial van accident; policy lapse under review.",
        "REGULATOR_COMMENTS": "Request underwriting file.",
        "FOLLOW_UP_REQUIRED": True,
        "CASE_REGION": "Midwest",
        "CASE_DIVISION": "Market Regulation",
        "CASE_INITIATED": "2022-01-02",
        "CASE_OPENED": "2022-01-03",
        "CASE_CLOSED": None,
        "NAIC_GROUP_NUMBER": "9083",
        "CASE_SUBTYPE": "Accident",
        "LOI": "Auto",
        "DISPOSITION": None,
    },
    "ID-T30010": {
        "CASE_TYPE": "Market Conduct Exams",
        "CASE_STATUS": "Under Review",
        "INVESTIGATOR": "C. Davis",
        "SECONDARY_INVESTIGATOR": "R. Vance",
        "ENTITY_NAME": "Snake River Group LLC",
        "ENTITY_TYPE": "Insurer",
        "CASE_PRIORITY": "High",
        "RISK_CATEGORY": "Casualty",
        "CASE_NOTES": "Damage assessment and claim handling under exam.",
        "REGULATOR_COMMENTS": "Focus on timeliness and documentation.",
        "FOLLOW_UP_REQUIRED": True,
        "CASE_REGION": "West",
        "CASE_DIVISION": "Exams",
        "CASE_INITIATED": "2022-05-30",
        "CASE_OPENED": "2022-06-01",
        "CASE_CLOSED": None,
        "NAIC_GROUP_NUMBER": "7777",
        "CASE_SUBTYPE": "Market Conduct",
        "LOI": "Casualty",
        "DISPOSITION": None,
    },
}

# ==============================================================================
# FIELD / PAYLOAD CONFIGURATION (DOCUMENT-ONLY FOR CORTEX)
# ==============================================================================

FIELD_MATRIX = {
    "Market Regulation": {
        "base": [
            "DOC_ID",
            "ATTACHMENT_ID",
            "CONTENT_TEXT",
            "BUSINESS_AREA",
            "DOC_STATE",
            "IS_CURRENT",
        ],
    },
    "Complaints": {
        "base": [
            "DOC_ID",
            "ATTACHMENT_ID",
            "CONTENT_TEXT",
            "BUSINESS_AREA",
            "DOC_STATE",
            "IS_CURRENT",
        ],
    },
    "Exams": {
        "base": [
            "DOC_ID",
            "ATTACHMENT_ID",
            "CONTENT_TEXT",
            "BUSINESS_AREA",
            "DOC_STATE",
            "IS_CURRENT",
        ],
    },
}

PII_FIELDS = {"ENTITY_NAME", "INVESTIGATOR"}

# ==============================================================================
# CSS
# ==============================================================================

st.markdown("""
<style>

/* --------------------------------------------------
   Global
-------------------------------------------------- */
html, body, [class*="css"] {
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
}

#MainMenu, footer, header {
    visibility: hidden;
}

.block-container {
    padding-top: 0 !important;
}

/* --------------------------------------------------
   Top Navigation Bar
-------------------------------------------------- */
.sdp-nav {
    background: #3f51b5;
    color: white;
    padding: 10px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 18px;
}

.sdp-nav-title {
    font-size: 18px;
    font-weight: 500;
}

.sdp-nav-persona {
    background: rgba(255, 255, 255, 0.18);
    padding: 5px 12px;
    border-radius: 4px;
    font-size: 12px;
}

/* --------------------------------------------------
   Badges
-------------------------------------------------- */
.badge-full {
    background: #e8f5e9;
    color: #2e7d32;
    padding: 3px 9px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
}

.badge-masked {
    background: #fff3e0;
    color: #e65100;
    padding: 3px 9px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
}

.badge-denied {
    background: #ffebee;
    color: #c62828;
    padding: 3px 9px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
}

/* --------------------------------------------------
   Search Snippet Highlighting
-------------------------------------------------- */
.sdp-snippet {
    font-style: italic;
    color: #555;
    display: block;
    max-width: 520px;
}

.sdp-snippet mark {
    background: #fff59d;
    padding: 0 2px;
    border-radius: 2px;
    font-style: normal;
}

/* --------------------------------------------------
   Accordion Component
-------------------------------------------------- */
.accordion {
    border: 1px solid #ddd;
    border-radius: 6px;
    margin-bottom: 12px;
    background: #fafafa;
}

.accordion-header {
    padding: 10px 14px;
    cursor: pointer;
    font-weight: 600;
    background: #f0f0f0;
    border-radius: 6px;
    user-select: none;
}

.accordion-header:hover {
    background: #e6e6e6;
}

.accordion-content {
    padding: 12px 14px;
    display: none;
    border-top: 1px solid #ddd;
    background: #ffffff;
}

</style>
""", unsafe_allow_html=True)


# ==============================================================================
# BACKEND SIMULATION (SNOWFLAKE-READY)
# ==============================================================================

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
        if word.upper() in {"LLC", "INC", "INSURANCE", "LIFE", "UNDERWRITERS", "COMPANY", "GROUP"}:
            masked.append(word)
        else:
            masked.append(word[:1] + "*" * max(len(word) - 1, 1))
    return " ".join(masked)


def mask_text(text, entity_name=None):
    if not text:
        return text
    if entity_name:
        text = re.sub(re.escape(entity_name), mask_value(entity_name), text)
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
    cortex_filter = {
        "@and": [
            {"@eq": {"DOC_STATE": user["state"]}},
            {"@eq": {"BUSINESS_AREA": selected_ba}},
            {"@eq": {"IS_CURRENT": True}},
        ]
    }
    return {
        "query": query,
        "columns": allowed,
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

        haystack_parts = [
            d["CONTENT_TEXT"],
            d.get("DOCUMENT_TITLE", ""),
            attachment["FILE_NAME"],
            case["ENTITY_NAME"],
            case["INVESTIGATOR"],
            case.get("SECONDARY_INVESTIGATOR") or "",
            case["CASE_TYPE"],
            case["CASE_STATUS"],
            case["CASE_SUBTYPE"],
            case["LOI"],
            case.get("CASE_NOTES") or "",
            case.get("REGULATOR_COMMENTS") or "",
        ]
        haystack = " ".join(haystack_parts).lower()

        if q:
            terms = q.split()
            if not all(term in haystack for term in terms):
                continue

        if filters.get("case_type") and case["CASE_TYPE"] != filters["case_type"]:
            continue
        if filters.get("status") and case["CASE_STATUS"] != filters["status"]:
            continue
        if filters.get("investigator"):
            inv_q = filters["investigator"].lower()
            if inv_q not in case["INVESTIGATOR"].lower() and (
                case.get("SECONDARY_INVESTIGATOR") is None
                or inv_q not in case["SECONDARY_INVESTIGATOR"].lower()
            ):
                continue
        if filters.get("entity"):
            ent_q = filters["entity"].lower()
            if ent_q not in case["ENTITY_NAME"].lower():
                continue
        if filters.get("tracking_id") and attachment["TRACKING_ID"] != filters["tracking_id"]:
            continue
        if filters.get("naic_group") and case["NAIC_GROUP_NUMBER"] != filters["naic_group"]:
            continue
        if filters.get("case_subtype") and case["CASE_SUBTYPE"] != filters["case_subtype"]:
            continue
        if filters.get("loi") and case["LOI"] != filters["loi"]:
            continue

        if user["unmasked_pii"]:
            display_file_name = attachment["FILE_NAME"]
            display_entity = case["ENTITY_NAME"]
            display_investigator = case["INVESTIGATOR"]
            snippet = d["CONTENT_TEXT"]
        else:
            display_file_name = mask_value(attachment["FILE_NAME"])
            display_entity = mask_value(case["ENTITY_NAME"])
            display_investigator = mask_value(case["INVESTIGATOR"])
            snippet = mask_text(d["CONTENT_TEXT"], entity_name=case["ENTITY_NAME"])

        if q:
            for term in q.split():
                snippet = re.sub(
                    re.escape(term),
                    lambda m: f"<mark>{escape(m.group(0))}</mark>",
                    snippet,
                    flags=re.IGNORECASE,
                )

        results.append({
            "DOC_ID": d["DOC_ID"],
            "ATTACHMENT_ID": d["ATTACHMENT_ID"],
            "TRACKING_ID": attachment["TRACKING_ID"],
            "FILE_NAME": display_file_name,
            "DOCUMENT_TITLE": d.get("DOCUMENT_TITLE", attachment["FILE_NAME"]),
            "DOCUMENT_DATE": d["UPLOAD_DATE"],
            "DOCUMENT_TYPE": d.get("DOCUMENT_TYPE", "Document"),
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
        })

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
# ACCORDION HELPER (NEW)
# ==============================================================================

def accordion_section(title, rows, key):
    content_id = f"acc_content_{key}"
    html_rows = "".join([f"<p><strong>{k}:</strong> {v}</p>" for k, v in rows.items()])
    st.markdown(f"""
    <div class="accordion">
        <div class="accordion-header" onclick="
            var c = document.getElementById('{content_id}');
            c.style.display = (c.style.display == 'block' ? 'none' : 'block');
        ">
            {title}
        </div>
        <div class="accordion-content" id="{content_id}">
            {html_rows}
        </div>
    </div>
    """, unsafe_allow_html=True)

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
  <span class="sdp-nav-title">Smart Document Platform — SD / ID</span>
  <span class="sdp-nav-persona">
    {user['username']} · {user['role']} · {user['state']} · {pii_badge} · {download_badge}
  </span>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# RESULTS (WITH ACCORDIONS)
# ==============================================================================

if st.session_state.results is not None:
    results = st.session_state.results
    st.markdown(f"### Search Results `{len(results)}`")

    if not results:
        st.info("No documents match the search and authorization criteria.")
    else:
        for r in results:
            with st.container(border=True):

                # Document summary row
                cols = st.columns([1.3, 1.1, 2.0, 3.5, 1.2])
                cols[0].markdown(f"**DOC_ID**  \n{r['DOC_ID']}")
                cols[1].markdown(f"**Tracking ID**  \n{r['TRACKING_ID']}")
                cols[2].markdown(f"**Document**  \n{r['DOCUMENT_TITLE']}")
                cols[3].markdown(
                    f"**Content**  \n<span class='sdp-snippet'>\"{r['SNIPPET']}\"</span>",
                    unsafe_allow_html=True,
                )

                # Download button
                with cols[4]:
                    if r["CAN_DOWNLOAD"]:
                        if st.button("Download", key=f"dl_{r['DOC_ID']}"):
                            ok, msg = download_document(user, r["_doc"], r["_case"])
                            if ok:
                                st.success(msg)
                            else:
                                st.error(msg)
                    else:
                        st.markdown('<span class="badge-denied">RESTRICTED</span>', unsafe_allow_html=True)

                # Accordion: Document Metadata
                accordion_section(
                    "Document Metadata",
                    {
                        "DOC_ID": r["DOC_ID"],
                        "Document Title": r["DOCUMENT_TITLE"],
                        "Document Type": r["DOCUMENT_TYPE"],
                        "Document Date": r["DOCUMENT_DATE"],
                        "State": r["STATE"],
                        "Business Area": r["BUSINESS_AREA"],
                        "Locked": r["LOCKED"],
                    },
                    key=f"docmeta_{r['DOC_ID']}"
                )

                # Accordion: Attachment Metadata
                accordion_section(
                    "Attachment Metadata",
                    {
                        "Attachment ID": r["ATTACHMENT_ID"],
                        "Tracking ID": r["TRACKING_ID"],
                        "File Name": r["FILE_NAME"],
                    },
                    key=f"attach_{r['DOC_ID']}"
                )

                # Accordion: Case Metadata
                accordion_section(
                    "Case Metadata",
                    {
                        "Case Type": r["CASE_TYPE"],
                        "Case Status": r["CASE_STATUS"],
                        "Investigator": r["INVESTIGATOR_DISPLAY"],
                        "Entity": r["ENTITY_NAME_DISPLAY"],
                        "Line of Insurance": r["LOI_DISPLAY"],
                    },
                    key=f"case_{r['DOC_ID']}"
                )
