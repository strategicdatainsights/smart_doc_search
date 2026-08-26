import streamlit as st
import re
from html import escape
from datetime import date

st.set_page_config(
    page_title="Smart Document Platform — SD / ID",
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
        "ldap_roles": ["SBS_FRAUD_PR"],
    },
    "Analyst — SD (Exams Only, Masked)": {
        "username": "analyst.sd@state.sd.gov",
        "role": "FINANCIAL_ANALYST",
        "state": "SD",
        "jurisdiction": "SD",
        "business_areas": ["Exams"],
        "can_download": True,
        "unmasked_pii": False,
        "ldap_roles": [],
    },
    "Analyst — ID (Exams Only, No Download)": {
        "username": "analyst.id@state.id.gov",
        "role": "FINANCIAL_ANALYST",
        "state": "ID",
        "jurisdiction": "ID",
        "business_areas": ["Exams"],
        "can_download": False,
        "unmasked_pii": False,
        "ldap_roles": [],
    },
}

# ==============================================================================
# MOCK DATA: DOC_SEARCH_CONTENT, SBS_ATTACHMENTS, SBS_CASES
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
        "DOC_TITLE": "Accident Investigation Report — Sioux Falls",
        "DOC_TYPE": "Accident Report",
        "DOC_DATE": "2019-10-03",
        "HAS_PII": True,
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
        "DOC_TITLE": "Formal Dispute — Rapid City Accident",
        "DOC_TYPE": "Dispute Letter",
        "DOC_DATE": "2019-12-22",
        "HAS_PII": True,
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
        "DOC_TITLE": "Complaint — Vehicle Loss near Pierre",
        "DOC_TYPE": "Complaint",
        "DOC_DATE": "2020-01-05",
        "HAS_PII": True,
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
        "DOC_TITLE": "Exam — Accident Damage Assessment",
        "DOC_TYPE": "Exam Report",
        "DOC_DATE": "2020-01-22",
        "HAS_PII": True,
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
        "DOC_TITLE": "Exam — Snake River Group Accident Assessment",
        "DOC_TYPE": "Exam Report",
        "DOC_DATE": "2020-02-10",
        "HAS_PII": True,
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
}

SBS_CASES = {
    "12350": {
        "CASE_TYPE": "Complaints",
        "CASE_STATUS": "Open",
        "INVESTIGATOR": "A. Miller",
        "SECONDARY_INVESTIGATOR": None,
        "ENTITY_NAME": "Prairie Plains Mutual Insurance Company",
        "CASE_SUBTYPE": "Inquiry",
        "LOI": "Property",
        "LOI_LIST": ["Property"],
        "CASE_INITIATED": "2019-09-28",
        "CASE_OPENED": "2019-10-01",
        "CASE_CLOSED": None,
    },
    "12351": {
        "CASE_TYPE": "Enforcement",
        "CASE_STATUS": "Closed",
        "INVESTIGATOR": "R. Vance",
        "SECONDARY_INVESTIGATOR": "C. Davis",
        "ENTITY_NAME": "Black Hills Mutual Insurance Company",
        "CASE_SUBTYPE": "Investigations",
        "LOI": "Casualty",
        "LOI_LIST": ["Casualty", "Enforcement LOB"],
        "CASE_INITIATED": "2019-12-18",
        "CASE_OPENED": "2019-12-20",
        "CASE_CLOSED": "2020-01-15",
    },
    "12352": {
        "CASE_TYPE": "Complaints",
        "CASE_STATUS": "Open",
        "INVESTIGATOR": "A. Miller",
        "SECONDARY_INVESTIGATOR": None,
        "ENTITY_NAME": "Dakota Plains Insurance Company",
        "CASE_SUBTYPE": "Inquiry",
        "LOI": "Auto",
        "LOI_LIST": ["Auto Physical Damage"],
        "CASE_INITIATED": "2020-01-03",
        "CASE_OPENED": "2020-01-05",
        "CASE_CLOSED": None,
    },
    "12345": {
        "CASE_TYPE": "Market Conduct Exams",
        "CASE_STATUS": "Under Review",
        "INVESTIGATOR": "C. Davis",
        "SECONDARY_INVESTIGATOR": "A. Miller",
        "ENTITY_NAME": "Missouri River Life Underwriters",
        "CASE_SUBTYPE": "Market Conduct",
        "LOI": "Life",
        "LOI_LIST": ["Life", "Beneficiary Practices"],
        "CASE_INITIATED": "2020-01-20",
        "CASE_OPENED": "2020-01-22",
        "CASE_CLOSED": None,
    },
    "12355": {
        "CASE_TYPE": "Market Conduct Exams",
        "CASE_STATUS": "Closed",
        "INVESTIGATOR": "C. Davis",
        "SECONDARY_INVESTIGATOR": None,
        "ENTITY_NAME": "Snake River Group LLC",
        "CASE_SUBTYPE": "Market Conduct",
        "LOI": "Casualty",
        "LOI_LIST": ["Casualty", "Exam Coverage"],
        "CASE_INITIATED": "2020-02-08",
        "CASE_OPENED": "2020-02-10",
        "CASE_CLOSED": "2020-03-01",
    },
}

# ==============================================================================
# IDENTITY RESOLUTION MOCK
# ==============================================================================

IDENTITY_CACHE = {
    "reg.sd@state.sd.gov": "Sarah Daniels",
    "analyst.sd@state.sd.gov": "Sam Driver",
    "analyst.id@state.id.gov": "Ian Dalton",
    "adjuster.sd@carrier.com": "Alex Adjuster",
    "examiner.sd@doi.gov": "Evelyn Reed",
    "examiner.id@doi.gov": "Evan Rivers",
    "complaints.sd@doi.gov": "Cora Complaints",
    "claimant.sd@consumer.com": "Chris Claimant",
}

def resolve_identity(raw_email):
    if not raw_email:
        return raw_email
    return IDENTITY_CACHE.get(raw_email.lower(), raw_email)

# ==============================================================================
# CSS
# ==============================================================================

st.markdown("""
<style>
html, body, [class*="css"] { font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0 !important; }
.sdp-nav {
    background:#3f51b5;
    color:white;
    padding:10px 20px;
    display:flex;
    align-items:center;
    justify-content:space-between;
    margin-bottom:18px;
}
.sdp-nav-title { font-size:18px;font-weight:500; }
.sdp-nav-persona {
    background:rgba(255,255,255,.18);
    padding:5px 12px;
    border-radius:4px;
    font-size:12px;
}
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
.filter-chip {
    display:inline-block;
    background:#e3f2fd;
    color:#1e88e5;
    padding:3px 8px;
    border-radius:12px;
    font-size:11px;
    margin-right:6px;
    margin-bottom:4px;
}
.results-table {
    width:100%;
    border-collapse:collapse;
    font-size:13px;
}
.results-table th, .results-table td {
    border-bottom:1px solid #eee;
    padding:6px 8px;
    text-align:left;
}
.results-table th {
    background:#f5f5f5;
    font-weight:600;
}
.results-table tr:hover {
    background:#fafafa;
}
.tracking-link {
    color:#1e88e5;
    text-decoration:underline;
    cursor:pointer;
}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# SECURITY / AUTH HELPERS
# ==============================================================================

DUAL_AUTH_CASE_SUBTYPES = {"Investigations", "Prosecutions"}
REQUIRED_LDAP_ROLE = "SBS_FRAUD_PR"

def has_dual_auth(user, case):
    subtype = case.get("CASE_SUBTYPE")
    requires_dual = subtype in DUAL_AUTH_CASE_SUBTYPES
    has_fraud_role = REQUIRED_LDAP_ROLE in user.get("ldap_roles", [])
    if not requires_dual:
        return True
    return has_fraud_role

def mask_value(value):
    if not value:
        return value
    if "@" in value:
        return "[EMAIL MASKED]"
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
    return text

def authorized_documents(user, selected_ba):
    docs = [
        d for d in DOC_SEARCH_CONTENT
        if d["DOC_STATE"] == user["state"]
        and d["BUSINESS_AREA"] == selected_ba
        and selected_ba in user["business_areas"]
        and d["IS_CURRENT"]
    ]
    filtered = []
    for d in docs:
        attachment = SBS_ATTACHMENTS.get(d["ATTACHMENT_ID"])
        if not attachment:
            continue
        case = SBS_CASES.get(attachment["TRACKING_ID"])
        if not case:
            continue
        if not has_dual_auth(user, case):
            continue
        filtered.append(d)
    return filtered

def build_search_payload(user, query, selected_ba, filters):
    columns = [
        "DOC_ID",
        "TRACKING_ID",
        "FILE_NAME",
        "DOC_TITLE",
        "DOC_TYPE",
        "DOC_DATE",
        "BUSINESS_AREA",
        "DOC_STATE",
        "CONTENT_TEXT",
    ]
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
    }

def run_search(user, query, selected_ba, filters, date_filters):
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

        # Basic date filtering (string dates, simple comparison)
        def within_range(field_name, drange):
            if not drange or not drange[0] or not drange[1]:
                return True
            val = case.get(field_name) if field_name != "UPLOAD_DATE" else d.get("UPLOAD_DATE")
            if not val:
                return False
            try:
                v = date.fromisoformat(val)
                return drange[0] <= v <= drange[1]
            except Exception:
                return True

        if not within_range("CASE_INITIATED", date_filters.get("case_initiated")):
            continue
        if not within_range("CASE_OPENED", date_filters.get("case_opened")):
            continue
        if not within_range("CASE_CLOSED", date_filters.get("case_closed")):
            continue
        if not within_range("UPLOAD_DATE", date_filters.get("file_upload")):
            continue

        haystack_parts = [
            d["CONTENT_TEXT"],
            d.get("DOC_TITLE", ""),
            attachment["FILE_NAME"],
            case["ENTITY_NAME"],
            case["INVESTIGATOR"],
            case.get("SECONDARY_INVESTIGATOR") or "",
            case["CASE_TYPE"],
            case["CASE_STATUS"],
            case["CASE_SUBTYPE"],
            case["LOI"],
            " ".join(case.get("LOI_LIST", [])),
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
        if filters.get("case_subtype") and case["CASE_SUBTYPE"] != filters["case_subtype"]:
            continue
        if filters.get("loi"):
            loi_q = filters["loi"].lower()
            loi_list = case.get("LOI_LIST", [])
            if not any(loi_q in item.lower() for item in loi_list):
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

        semantic_score = 0.85 + 0.05 * min(len(q.split()), 3)
        uploaded_raw = attachment["UPLOAD_USER"]
        uploaded_resolved = resolve_identity(uploaded_raw)

        results.append({
            "DOC_ID": d["DOC_ID"],
            "ATTACHMENT_ID": d["ATTACHMENT_ID"],
            "TRACKING_ID": attachment["TRACKING_ID"],
            "FILE_NAME": display_file_name,
            "DOC_TITLE": d.get("DOC_TITLE", attachment["FILE_NAME"]),
            "DOC_TYPE": d.get("DOC_TYPE", "Document"),
            "DOC_DATE": d.get("DOC_DATE", d.get("UPLOAD_DATE")),
            "UPLOAD_DATE": d.get("UPLOAD_DATE"),
            "STATE": d["DOC_STATE"],
            "BUSINESS_AREA": d["BUSINESS_AREA"],
            "SNIPPET": snippet,
            "CASE_TYPE": case["CASE_TYPE"],
            "CASE_STATUS": case["CASE_STATUS"],
            "CASE_SUBTYPE": case["CASE_SUBTYPE"],
            "INVESTIGATOR_DISPLAY": display_investigator,
            "ENTITY_NAME_DISPLAY": display_entity,
            "LOI_DISPLAY": case["LOI"],
            "LOI_LIST": case.get("LOI_LIST", []),
            "ATTACHMENT_TYPE": attachment.get("ATTACHMENT_TYPE", "N/A"),
            "CAN_DOWNLOAD": user["can_download"],
            "SEMANTIC_SCORE": semantic_score,
            "UPLOADED_BY_RAW": uploaded_raw,
            "UPLOADED_BY_RESOLVED": uploaded_resolved,
            "_doc": d,
            "_attachment": attachment,
            "_case": case,
        })

    results.sort(key=lambda r: r["SEMANTIC_SCORE"], reverse=True)
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
if "visible_columns" not in st.session_state:
    st.session_state.visible_columns = [
        "ATTACHMENT_ID",
        "TRACKING_ID",
        "FILE_NAME",
        "SNIPPET",
        "UPLOAD_DATE",
        "UPLOADED_BY_RESOLVED",
    ]

user = USERS[st.session_state.selected_user]

# ==============================================================================
# HEADER + MODE TOGGLE
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

top_left, top_right = st.columns([4, 3])
with top_left:
    st.caption("Prototype: DOC_SEARCH_CONTENT → Spring Boot auth → Cortex Search → SBS join → UI")
with top_right:
    selected = st.selectbox("Persona", list(USERS), index=list(USERS).index(st.session_state.selected_user))
    mode = st.radio("Mode", ["Client Demo", "Technical Review"], horizontal=True)
    if selected != st.session_state.selected_user:
        st.session_state.selected_user = selected
        st.session_state.results = None
        st.session_state.payload = None
        st.rerun()

# ==============================================================================
# SEARCH UI
# ==============================================================================

st.markdown("### Search Criteria")

business_area = st.selectbox(
    "Business Area",
    user["business_areas"],
)

with st.form(key="search_form"):
    query = st.text_area(
        "Search Document Contents (semantic)",
        placeholder="Search within document text, titles, case notes, investigators, entities...",
        height=100,
    )

    with st.expander("Case Filters", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            case_type = st.selectbox("Case Type", ["", "Complaints", "Enforcement", "Market Regulation", "Market Conduct Exams"])
            status = st.selectbox("Status", ["", "Open", "Closed", "Under Review", "Pending"])
            case_subtype = st.text_input("Case Sub-Type", placeholder="e.g., Inquiry, Market Conduct")
            loi = st.text_input("Line of Insurance (LOI)", placeholder="e.g., Auto, Property, Life")
        with c2:
            tracking_id = st.text_input("Tracking ID", placeholder="e.g., 12350")
            investigator = st.text_input("Investigator", placeholder="Primary or secondary investigator")
            entity = st.text_input("Entity Name", placeholder="Insurer or company name")
            naic_group = st.text_input("NAIC Group Number", placeholder="e.g., 9083")

    with st.expander("Document Filters", expanded=False):
        d1, d2 = st.columns(2)
        with d1:
            doc_name = st.text_input("Document Title / Name", placeholder="e.g., Accident Investigation Report")
            file_type = st.selectbox("File Type", ["", ".pdf", ".docx"])
            attachment_type = st.selectbox("Attachment Type", ["", "Report", "Letter", "Complaint", "Exam Report"])
        with d2:
            topics = st.text_input("Topics / Key Phrases", placeholder="e.g., accident, casualty, exam")
            geo = st.text_input("Location Keyword", placeholder="e.g., Sioux Falls, Boise")

    with st.expander("Dates", expanded=False):
        dc1, dc2 = st.columns(2)
        with dc1:
            case_initiated_from = st.date_input("Case Initiated From", value=None)
            case_initiated_to = st.date_input("Case Initiated To", value=None)
            case_opened_from = st.date_input("Case Opened From", value=None)
            case_opened_to = st.date_input("Case Opened To", value=None)
        with dc2:
            case_closed_from = st.date_input("Case Closed From", value=None)
            case_closed_to = st.date_input("Case Closed To", value=None)
            file_upload_from = st.date_input("File Upload From", value=None)
            file_upload_to = st.date_input("File Upload To", value=None)

    with st.expander("Additional Details", expanded=False):
        ad1, ad2 = st.columns(2)
        with ad1:
            state_keywords = st.multiselect("State Keyword", ["Sioux Falls", "Rapid City", "Pierre", "Boise"])
        with ad2:
            reason = st.selectbox("Reason", ["", "Accident", "Complaint", "Exam", "Dispute"])

    btn_cols = st.columns([1, 1, 6])
    with btn_cols[0]:
        search_clicked = st.form_submit_button("🔍 Search", type="primary")
    with btn_cols[1]:
        reset_clicked = st.form_submit_button("Reset")

if reset_clicked:
    st.session_state.results = None
    st.session_state.payload = None
    st.rerun()

date_filters = {
    "case_initiated": (case_initiated_from, case_initiated_to) if case_initiated_from and case_initiated_to else None,
    "case_opened": (case_opened_from, case_opened_to) if case_opened_from and case_opened_to else None,
    "case_closed": (case_closed_from, case_closed_to) if case_closed_from and case_closed_to else None,
    "file_upload": (file_upload_from, file_upload_to) if file_upload_from and file_upload_to else None,
}

if search_clicked:
    if not query.strip() or len(query.strip()) < 3:
        st.error("Search Document Contents is required and must contain at least 3 characters.")
    else:
        filters = {
            "case_type": case_type or None,
            "status": status or None,
            "investigator": investigator or None,
            "entity": entity or None,
            "tracking_id": tracking_id or None,
            "naic_group": naic_group or None,
            "case_subtype": case_subtype or None,
            "loi": loi or None,
            "doc_name": doc_name or None,
            "file_type": file_type or None,
            "topics": topics or None,
            "geo": geo or None,
            "attachment_type": attachment_type or None,
            "state_keywords": state_keywords or None,
            "reason": reason or None,
        }
        st.session_state.results = run_search(user, query, business_area, filters, date_filters)
        st.session_state.payload = build_search_payload(user, query, business_area, filters)

# ==============================================================================
# ACTIVE FILTER CHIPS
# ==============================================================================

if st.session_state.results is not None:
    filters = []
    if case_type:
        filters.append(f"Case Type: {case_type}")
    if status:
        filters.append(f"Status: {status}")
    if case_subtype:
        filters.append(f"Sub-Type: {case_subtype}")
    if loi:
        filters.append(f"LOI: {loi}")
    if tracking_id:
        filters.append(f"Tracking ID: {tracking_id}")
    if investigator:
        filters.append(f"Investigator: {investigator}")
    if entity:
        filters.append(f"Entity: {entity}")
    if naic_group:
        filters.append(f"NAIC Group: {naic_group}")
    if doc_name:
        filters.append(f"Doc Name: {doc_name}")
    if file_type:
        filters.append(f"File Type: {file_type}")
    if topics:
        filters.append(f"Topics: {topics}")
    if geo:
        filters.append(f"Geo: {geo}")
    if attachment_type:
        filters.append(f"Attachment Type: {attachment_type}")
    if state_keywords:
        filters.append(f"State Keywords: {', '.join(state_keywords)}")
    if reason:
        filters.append(f"Reason: {reason}")
    if any(date_filters.values()):
        filters.append("Date Filters: Active")

    if filters:
        st.markdown("#### Active Filters")
        chips_html = "".join([f"<span class='filter-chip'>{escape(f)}</span>" for f in filters])
        st.markdown(chips_html, unsafe_allow_html=True)

# ==============================================================================
# RESULTS TABLE
# ==============================================================================

if st.session_state.results is not None:
    results = st.session_state.results
    st.markdown(f"### Search Results `{len(results)}`")
    if not results:
        st.info("No documents match the search and authorization criteria.")
    else:
        all_columns = [
            "ATTACHMENT_ID",
            "TRACKING_ID",
            "FILE_NAME",
            "DOC_TITLE",
            "DOC_TYPE",
            "DOC_DATE",
            "UPLOAD_DATE",
            "BUSINESS_AREA",
            "STATE",
            "CASE_TYPE",
            "CASE_STATUS",
            "CASE_SUBTYPE",
            "LOI_DISPLAY",
            "LOI_LIST",
            "UPLOADED_BY_RESOLVED",
            "INVESTIGATOR_DISPLAY",
            "ENTITY_NAME_DISPLAY",
            "ATTACHMENT_TYPE",
            "SEMANTIC_SCORE",
        ]
        st.markdown("#### Column Picker")
        valid_options = [c for c in all_columns if c not in ["ATTACHMENT_ID", "TRACKING_ID"]]

        # sanitize defaults so Streamlit doesn't crash
        default_cols = [c for c in st.session_state.visible_columns if c in valid_options]
        
        st.session_state.visible_columns = st.multiselect(
            "Visible Columns (Attachment ID and Tracking ID are always shown)",
            options=valid_options,
            default=default_cols,
        )


        table_html = "<table class='results-table'><thead><tr>"
        table_html += "<th>Attachment ID</th><th>Tracking ID</th>"
        for col in st.session_state.visible_columns:
            table_html += f"<th>{escape(col.replace('_', ' '))}</th>"
        table_html += "</tr></thead><tbody>"

        for r in results:
            table_html += "<tr>"
            table_html += f"<td>{escape(r['ATTACHMENT_ID'])}</td>"
            table_html += (
                f"<td><span class='tracking-link' title='Opens Case Summary in V2'>"
                f"{escape(r['TRACKING_ID'])}</span></td>"
            )
            for col in st.session_state.visible_columns:
                val = r.get(col)
                if col == "SNIPPET":
                    cell = f"<span class='sdp-snippet'>“{r['SNIPPET']}”</span>"
                elif col == "LOI_LIST" and isinstance(val, list):
                    cell = ", ".join(val)
                elif col == "SEMANTIC_SCORE":
                    cell = f"{r['SEMANTIC_SCORE']:.2f}"
                else:
                    cell = escape(str(val)) if val is not None else "N/A"
                table_html += f"<td>{cell}</td>"
            table_html += "</tr>"

        table_html += "</tbody></table>"
        st.markdown(table_html, unsafe_allow_html=True)

        st.markdown("#### Actions")
        for r in results:
            cols = st.columns([3, 1])
            with cols[0]:
                st.caption(f"{r['DOC_ID']} · {r['FILE_NAME']}")
            with cols[1]:
                if r["CAN_DOWNLOAD"]:
                    if st.button("⬇ Download", key=f"dl_{r['DOC_ID']}"):
                        ok, msg = download_document(user, r["_doc"], r["_case"])
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)
                else:
                    st.markdown('<span class="badge-denied">RESTRICTED</span>', unsafe_allow_html=True)

# ==============================================================================
# GOVERNANCE / INSPECTOR (TECHNICAL MODE ONLY)
# ==============================================================================

if mode == "Technical Review":
    with st.expander("🛠 Governance / Integration Inspector", expanded=False):
        tab1, tab2, tab3 = st.tabs(["Backend Payload", "Authorization Trace", "Document Relationship"])

        with tab1:
            st.caption("Payload Spring Boot constructs for Cortex Search.")
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
                "dual_auth_case_subtypes": list(DUAL_AUTH_CASE_SUBTYPES),
                "ldap_roles": user.get("ldap_roles", []),
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
                    "LOI_LIST": "→ aggregated across LOI/LOB tables",
                },
            })
