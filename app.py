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
# DOCUMENT-PIPELINE DATA + SIMULATED SBS DATA (SD / ID)
# ==============================================================================

DOCUMENTS = [
    {
        "DOC_ID": "DOC-10001",
        "VERSION_ID": "DOC-10001-V1",
        "ATTACHMENT_ID": "890786543",
        "TRACKING_ID": "12350",
        "FILE_PATH": "SD/Market Regulation/890786543/accident_investigation_sd.docx",
        "FILE_NAME": "accident_investigation_sd.docx",
        "STATE": "SD",
        "BUSINESS_AREA": "Market Regulation",
        "DOCUMENT_TITLE": "South Dakota Accident Investigation Report",
        "DOCUMENT_DATE": "2019-10-03",
        "DOCUMENT_TYPE": "Investigation Report",
        "CHUNK_TEXT": (
            "Accident appears to have occurred on Monday evening near Sioux Falls "
            "at the intersection of Main and 10th Street. Jane Smith reported the "
            "incident to Prairie Plains Mutual Insurance Company."
        ),
        "PII": {
            "PERSON_NAME": "Jane Smith",
            "COMPANY_NAME": "Prairie Plains Mutual Insurance Company",
        },
        "LOCKED": False,
        "UPLOAD_DATE": "2019-10-03",
        "SBS": {
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
    },
    {
        "DOC_ID": "DOC-10002",
        "VERSION_ID": "DOC-10002-V1",
        "ATTACHMENT_ID": "890786544",
        "TRACKING_ID": "12351",
        "FILE_PATH": "SD/Market Regulation/890786544/jane_doe_dispute_sd.pdf",
        "FILE_NAME": "jane_doe_dispute_sd.pdf",
        "STATE": "SD",
        "BUSINESS_AREA": "Market Regulation",
        "DOCUMENT_TITLE": "Formal Dispute Correspondence – SD",
        "DOCUMENT_DATE": "2019-12-22",
        "DOCUMENT_TYPE": "Correspondence",
        "CHUNK_TEXT": (
            "The claimant filed a formal dispute concerning the accident "
            "that occurred on December 19th near Rapid City. Jane Doe contacted "
            "Black Hills Mutual Insurance Company."
        ),
        "PII": {
            "PERSON_NAME": "Jane Doe",
            "COMPANY_NAME": "Black Hills Mutual Insurance Company",
        },
        "LOCKED": True,
        "UPLOAD_DATE": "2019-12-22",
        "SBS": {
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
    },
    {
        "DOC_ID": "DOC-10003",
        "VERSION_ID": "DOC-10003-V1",
        "ATTACHMENT_ID": "890786545",
        "TRACKING_ID": "12352",
        "FILE_PATH": "SD/Complaints/890786545/uniformdoc_sd.pdf",
        "FILE_NAME": "uniformdoc_sd.pdf",
        "STATE": "SD",
        "BUSINESS_AREA": "Complaints",
        "DOCUMENT_TITLE": "Claim Denial Complaint – SD",
        "DOCUMENT_DATE": "2020-01-05",
        "DOCUMENT_TYPE": "Complaint",
        "CHUNK_TEXT": (
            "The policyholder submitted a formal complaint regarding claim denial "
            "for a vehicle loss near Pierre. The complaint was assigned for review."
        ),
        "PII": {
            "PERSON_NAME": "Robert Jones",
            "COMPANY_NAME": "Dakota Plains Insurance Company",
        },
        "LOCKED": False,
        "UPLOAD_DATE": "2020-01-05",
        "SBS": {
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
    },
    {
        "DOC_ID": "DOC-10004",
        "VERSION_ID": "DOC-10004-V1",
        "ATTACHMENT_ID": "890786546",
        "TRACKING_ID": "12345",
        "FILE_PATH": "SD/Exams/890786546/accident_detail_sd.pdf",
        "FILE_NAME": "accident_detail_sd.pdf",
        "STATE": "SD",
        "BUSINESS_AREA": "Exams",
        "DOCUMENT_TITLE": "Vehicle Damage Assessment – SD",
        "DOCUMENT_DATE": "2020-01-22",
        "DOCUMENT_TYPE": "Assessment",
        "CHUNK_TEXT": (
            "Details of damage sustained by vehicle after accident near Sioux Falls. "
            "Total loss assessment filed by the adjuster."
        ),
        "PII": {
            "PERSON_NAME": "Michael Davis",
            "COMPANY_NAME": "Missouri River Life Underwriters",
        },
        "LOCKED": False,
        "UPLOAD_DATE": "2020-01-22",
        "SBS": {
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
    },
    {
        "DOC_ID": "DOC-10005",
        "VERSION_ID": "DOC-10005-V1",
        "ATTACHMENT_ID": "890786547",
        "TRACKING_ID": "12355",
        "FILE_PATH": "ID/Exams/890786547/cornwall_motorcycle_club_id.docx",
        "FILE_NAME": "cornwall_motorcycle_club_id.docx",
        "STATE": "ID",
        "BUSINESS_AREA": "Exams",
        "DOCUMENT_TITLE": "Motorcycle Club Examination – ID",
        "DOCUMENT_DATE": "2020-02-10",
        "DOCUMENT_TYPE": "Examination Report",
        "CHUNK_TEXT": (
            "Details of accident damage assessment from third party inspector "
            "retained by Snake River Group LLC near Boise, Idaho."
        ),
        "PII": {
            "PERSON_NAME": "Indiana Jones",
            "COMPANY_NAME": "Snake River Group LLC",
        },
        "LOCKED": False,
        "UPLOAD_DATE": "2020-02-10",
        "SBS": {
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
    },
]

VERSIONS = {
    "DOC-10001": [
        {"VERSION_ID": "DOC-10001-V1", "HASH": "sha256:aaa111", "IS_CURRENT": True}
    ],
    "DOC-10002": [
        {"VERSION_ID": "DOC-10002-V1", "HASH": "sha256:bbb222", "IS_CURRENT": True}
    ],
    "DOC-10003": [
        {"VERSION_ID": "DOC-10003-V1", "HASH": "sha256:ccc333", "IS_CURRENT": True}
    ],
    "DOC-10004": [
        {"VERSION_ID": "DOC-10004-V1", "HASH": "sha256:ddd444", "IS_CURRENT": True}
    ],
    "DOC-10005": [
        {"VERSION_ID": "DOC-10005-V1", "HASH": "sha256:eee555", "IS_CURRENT": True}
    ],
}

# ==============================================================================
# FIELD / PAYLOAD CONFIGURATION
# ==============================================================================

FIELD_MATRIX = {
    "Market Regulation": {
        "base": ["DOC_ID", "TRACKING_ID", "DOCUMENT_TITLE", "DOCUMENT_TYPE",
                 "DOCUMENT_DATE", "CASE_TYPE", "CASE_STATUS", "INVESTIGATOR",
                 "ENTITY_NAME", "LOI", "DISPOSITION"],
    },
    "Complaints": {
        "base": ["DOC_ID", "TRACKING_ID", "DOCUMENT_TITLE", "DOCUMENT_TYPE",
                 "DOCUMENT_DATE", "CASE_TYPE", "CASE_STATUS", "INVESTIGATOR",
                 "ENTITY_NAME", "CASE_SUBTYPE", "LOI"],
    },
    "Exams": {
        "base": ["DOC_ID", "TRACKING_ID", "DOCUMENT_TITLE", "DOCUMENT_TYPE",
                 "DOCUMENT_DATE", "CASE_TYPE", "CASE_STATUS", "INVESTIGATOR",
                 "ENTITY_NAME", "CASE_SUBTYPE", "LOI"],
    },
}

PII_FIELDS = {"ENTITY_NAME", "INVESTIGATOR", "PERSON_NAME", "COMPANY_NAME"}

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

.sdp-table-wrap {
    background:white;
    border:1px solid #e0e0e0;
    border-radius:8px;
    overflow:hidden;
}

.sdp-table {
    width:100%;
    border-collapse:collapse;
    font-size:13px;
}

.sdp-table th {
    padding:11px 14px;
    text-align:left;
    font-weight:500;
    color:#555;
    background:#fafafa;
    border-bottom:2px solid #e0e0e0;
}

.sdp-table td {
    padding:11px 14px;
    border-bottom:1px solid #f0f0f0;
    vertical-align:top;
}

.sdp-table tr:last-child td {
    border-bottom:none;
}

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
# BACKEND SIMULATION
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


def mask_text(text, doc):
    if not text:
        return text

    for sensitive in doc.get("PII", {}).values():
        text = text.replace(sensitive, mask_value(sensitive))

    text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "***-**-****", text)
    text = re.sub(r"\b[\w.+-]+@[\w.-]+\.\w+\b", "[EMAIL MASKED]", text)
    text = re.sub(r"\b(?:\d{3}[-.\s]){2}\d{4}\b", "[PHONE MASKED]", text)
    return text


def authorized_documents(user, selected_ba):
    return [
        d for d in DOCUMENTS
        if d["STATE"] == user["state"]
        and d["BUSINESS_AREA"] == selected_ba
        and selected_ba in user["business_areas"]
    ]


def build_search_payload(user, query, selected_ba, filters):
    allowed = FIELD_MATRIX[selected_ba]["base"]

    if user["unmasked_pii"]:
        columns = allowed
    else:
        columns = [
            "DOC_ID", "TRACKING_ID", "DOCUMENT_TITLE", "DOCUMENT_TYPE",
            "DOCUMENT_DATE", "CASE_TYPE", "CASE_STATUS",
            "INVESTIGATOR_MASKED", "ENTITY_NAME_MASKED",
            "CASE_SUBTYPE", "LOI", "CONTENT_TEXT_MASKED"
        ]

    cortex_filter = {
        "@and": [
            {"@eq": {"STATE": user["state"]}},
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

    if filters["case_type"]:
        docs = [d for d in docs if d["SBS"]["CASE_TYPE"] == filters["case_type"]]
    if filters["status"]:
        docs = [d for d in docs if d["SBS"]["CASE_STATUS"] == filters["status"]]
    if filters["investigator"]:
        needle = filters["investigator"].lower()
        docs = [d for d in docs if needle in d["SBS"]["INVESTIGATOR"].lower()]
    if filters["entity"]:
        needle = filters["entity"].lower()
        docs = [d for d in docs if needle in d["SBS"]["ENTITY_NAME"].lower()]
    if filters["tracking_id"]:
        docs = [d for d in docs if filters["tracking_id"] in d["TRACKING_ID"]]
    if filters["file_type"]:
        docs = [d for d in docs if d["FILE_NAME"].lower().endswith(filters["file_type"].lower())]

    results = []
    q = query.strip().lower()

    for d in docs:
        search_text = d["CHUNK_TEXT"] if user["unmasked_pii"] else mask_text(d["CHUNK_TEXT"], d)
        search_file = d["FILE_NAME"] if user["unmasked_pii"] else mask_text(d["FILE_NAME"], d)

        if q:
            terms = q.split()
            if not all(term in (search_text + " " + search_file).lower() for term in terms):
                continue

        result = {
            "DOC_ID": d["DOC_ID"],
            "ATTACHMENT_ID": d["ATTACHMENT_ID"],
            "TRACKING_ID": d["TRACKING_ID"],
            "FILE_NAME": d["FILE_NAME"] if user["unmasked_pii"] else mask_text(d["FILE_NAME"], d),
            "DOCUMENT_TITLE": d["DOCUMENT_TITLE"],
            "DOCUMENT_DATE": d["DOCUMENT_DATE"],
            "DOCUMENT_TYPE": d["DOCUMENT_TYPE"],
            "STATE": d["STATE"],
            "BUSINESS_AREA": d["BUSINESS_AREA"],
            "SNIPPET": search_text,
            "CASE_TYPE": d["SBS"]["CASE_TYPE"],
            "CASE_STATUS": d["SBS"]["CASE_STATUS"],
            "INVESTIGATOR": (
                d["SBS"]["INVESTIGATOR"]
                if user["unmasked_pii"]
                else mask_value(d["SBS"]["INVESTIGATOR"])
            ),
            "ENTITY_NAME": (
                d["SBS"]["ENTITY_NAME"]
                if user["unmasked_pii"]
                else mask_value(d["SBS"]["ENTITY_NAME"])
            ),
            "CASE_INITIATED": d["SBS"]["CASE_INITIATED"],
            "LOI": d["SBS"]["LOI"],
            "LOCKED": d["LOCKED"],
            "CAN_DOWNLOAD": user["can_download"],
            "_source": d,
        }

        investigator_display = (
            d["SBS"]["INVESTIGATOR"]
            if user["unmasked_pii"]
            else mask_value(d["SBS"]["INVESTIGATOR"])
        )
        result["INVESTIGATOR_DISPLAY"] = investigator_display

        entity_display = (
            d["SBS"]["ENTITY_NAME"]
            if user["unmasked_pii"]
            else mask_value(d["SBS"]["ENTITY_NAME"])
        )
        result["ENTITY_NAME_DISPLAY"] = entity_display

        loi_display = (
            d["SBS"]["LOI"]
            if user["unmasked_pii"]
            else mask_value(d["SBS"]["LOI"])
        )
        result["LOI_DISPLAY"] = loi_display

        if q:
            for term in q.split():
                result["SNIPPET"] = re.sub(
                    re.escape(term),
                    lambda m: f"<mark>{escape(m.group(0))}</mark>",
                    result["SNIPPET"],
                    flags=re.IGNORECASE,
                )

        results.append(result)

    return results


def download_document(user, doc):
    CONFIDENTIAL_CASE_TYPES = {
        "Enforcement",
        "Market Conduct Exams",
        "Investigations",
        "Multi-State",
        "Securities",
        "PBM",
        "Fraud",
    }
    case_type = doc["SBS"]["CASE_TYPE"]

    if user["role"] != "STATE_REGULATOR" and case_type in CONFIDENTIAL_CASE_TYPES:
        return False, "Download denied: confidential case type requires regulator access."

    if not user["can_download"]:
        return False, "Download denied by authorization policy."
    if doc["STATE"] != user["state"]:
        return False, "Download denied: jurisdiction mismatch."
    if doc["BUSINESS_AREA"] not in user["business_areas"]:
        return False, "Download denied: business-area entitlement."
    return True, f"Authorized download: {doc['FILE_NAME']}"

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

# Top bar + legend (client-style)
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

`S3 → Document ID / version → Parse → CONTENT_TEXT → metadata → chunking → governance/search-safe projection → Spring Boot authorization → Cortex Search → Spring Boot response → UI`

**Structured relationship**

`DOC_ID / ATTACHMENT_ID / TRACKING_ID` connect the document pipeline to simulated SBS case metadata.

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

# Case Details (expander, restyled via CSS)
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

# Entity
with st.expander("Entity", expanded=False):
    st.markdown('<div class="sdp-card-body">', unsafe_allow_html=True)
    entity = st.text_input("Entity Name", placeholder="Search by person or company name")
    st.markdown('<span class="sdp-hint">Handles partial names, company names, or combinations.</span>', unsafe_allow_html=True)
    naic_group = st.text_input("NAIC Group Number", placeholder="e.g. 9083")
    st.markdown('</div>', unsafe_allow_html=True)

# Dates (placeholder, matching client sections)
with st.expander("Dates", expanded=False):
    st.markdown('<div class="sdp-card-body">', unsafe_allow_html=True)
    d1, d2 = st.columns(2)
    with d1:
        start_date = st.date_input("Start Date", value=None)
    with d2:
        end_date = st.date_input("End Date", value=None)
    st.markdown('</div>', unsafe_allow_html=True)

# Document
with st.expander("Document", expanded=False):
    st.markdown('<div class="sdp-card-body">', unsafe_allow_html=True)
    doc_name = st.text_input("Document Name", placeholder="e.g., accident report, policy letter")
    st.markdown('<span class="sdp-hint">Smart search over document names.</span>', unsafe_allow_html=True)
    file_type = st.selectbox("File Type", ["", ".pdf", ".docx"])
    st.markdown('</div>', unsafe_allow_html=True)

# Additional Details (optional filters)
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
            "document_type": None,
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
                            ok, msg = download_document(user, r["_source"])
                            if ok:
                                st.success(msg)
                            else:
                                st.error(msg)
                    else:
                        st.markdown('<span class="badge-denied">RESTRICTED</span>', unsafe_allow_html=True)

        with st.expander("Result Metadata", expanded=False):
            m1, m2, m3 = st.columns(3)
            m1.markdown(f"**Document Type**  \n{r['DOCUMENT_TYPE']}")
            m1.markdown(f"**Document Date**  \n{r['DOCUMENT_DATE']}")
            m1.markdown(f"**State**  \n{r['STATE']}")
            m2.markdown(f"**Business Area**  \n{r['BUSINESS_AREA']}")
            m2.markdown(f"**Case Type**  \n{r['CASE_TYPE']}")
            m2.markdown(f"**Status**  \n{r['CASE_STATUS']}")
            m3.markdown(f"**Investigator**  \n{r['INVESTIGATOR_DISPLAY']}")
            m3.markdown(f"**Entity**  \n{r['ENTITY_NAME_DISPLAY']}")
            m3.markdown(f"**LOI**  \n{r['LOI_DISPLAY']}")

# ==============================================================================
# GOVERNANCE / PAYLOAD INSPECTOR
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
                "VERSION_ID": "DOC-10004-V1",
                "ATTACHMENT_ID": "890786546",
                "FILE_PATH": "SD/Exams/890786546/accident_detail_sd.pdf",
            },
            "relationship": {
                "ATTACHMENT_ID": "→ SBS ATTACHMENT",
                "TRACKING_ID": "→ MR_CASE.TRACKING_ID",
                "structured_case_metadata": "→ replicated SBS EDL",
            },
            "search_content": {
                "CONTENT_TEXT": "→ parsed document",
                "CHUNK_TEXT": "→ semantic chunks",
            },
            "governance": {
                "STATE": "→ entitlement / jurisdiction",
                "BUSINESS_AREA": "→ entitlement",
                "PII": "→ full or search-safe representation",
            },
        })

# ==============================================================================
# DEMO / TEST PANEL
# ==============================================================================

with st.expander("🧪 Security Test Scenarios", expanded=False):
    st.markdown("""
Use the persona switcher and search to demonstrate:

1. **SD regulator** — sees full permitted metadata and can download.
2. **SD analyst** — sees masked PII and only SD Exams.
3. **ID analyst** — sees only ID Exams and cannot download SD documents.
4. **State isolation** — backend always applies the authenticated State.
5. **Business-area isolation** — backend rejects areas outside entitlement.
6. **PII masking** — document content, entity, investigator, and filenames use the permitted representation.
7. **Raw access** — download is independently authorized by the backend.
8. **Payload control** — the backend, not the UI, selects response fields.
""")
