import streamlit as st
import pandas as pd
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
        "NAIC_GROUP_NUMBER": "9083",
        "CASE_SUBTYPE": "Inquiry",
        "LOI": "Property",
    },
    "12351": {
        "CASE_TYPE": "Enforcement",
        "CASE_STATUS": "Closed",
        "INVESTIGATOR": "R. Vance",
        "SECONDARY_INVESTIGATOR": "C. Davis",
        "ENTITY_NAME": "Black Hills Mutual Insurance Company",
        "NAIC_GROUP_NUMBER": "8056",
        "CASE_SUBTYPE": "Investigations",
        "LOI": "Casualty",
    },
    "12352": {
        "CASE_TYPE": "Complaints",
        "CASE_STATUS": "Open",
        "INVESTIGATOR": "A. Miller",
        "SECONDARY_INVESTIGATOR": None,
        "ENTITY_NAME": "Dakota Plains Insurance Company",
        "NAIC_GROUP_NUMBER": "1234",
        "CASE_SUBTYPE": "Inquiry",
        "LOI": "Auto",
    },
    "12345": {
        "CASE_TYPE": "Market Conduct Exams",
        "CASE_STATUS": "Under Review",
        "INVESTIGATOR": "C. Davis",
        "SECONDARY_INVESTIGATOR": "A. Miller",
        "ENTITY_NAME": "Missouri River Life Underwriters",
        "NAIC_GROUP_NUMBER": "5678",
        "CASE_SUBTYPE": "Market Conduct",
        "LOI": "Life",
    },
    "12355": {
        "CASE_TYPE": "Market Conduct Exams",
        "CASE_STATUS": "Closed",
        "INVESTIGATOR": "C. Davis",
        "SECONDARY_INVESTIGATOR": None,
        "ENTITY_NAME": "Snake River Group LLC",
        "NAIC_GROUP_NUMBER": "7777",
        "CASE_SUBTYPE": "Market Conduct",
        "LOI": "Casualty",
    },
}

FIELD_MATRIX = {
    "Market Regulation": {"base": ["DOC_ID", "ATTACHMENT_ID", "CONTENT_TEXT", "BUSINESS_AREA", "DOC_STATE", "IS_CURRENT"]},
    "Complaints": {"base": ["DOC_ID", "ATTACHMENT_ID", "CONTENT_TEXT", "BUSINESS_AREA", "DOC_STATE", "IS_CURRENT"]},
    "Exams": {"base": ["DOC_ID", "ATTACHMENT_ID", "CONTENT_TEXT", "BUSINESS_AREA", "DOC_STATE", "IS_CURRENT"]},
}

# ==============================================================================
# CSS STYLING & ACCORDION SYSTEM
# ==============================================================================

st.markdown("""
<style>
html, body, [class*="css"] { font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0 !important; max-width: 95% !important; }

.sdp-nav {
    background: #3f51b5;
    color: white;
    padding: 12px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
    border-radius: 0 0 6px 6px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.sdp-nav-title { font-size: 20px; font-weight: 600; letter-spacing: 0.3px; }
.sdp-nav-persona {
    background: rgba(255, 255, 255, 0.18);
    padding: 6px 14px;
    border-radius: 4px;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 8px;
}
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
.badge-locked {
    background: #ede7f6;
    color: #512da8;
    padding: 3px 9px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
}

.result-card {
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 16px;
    margin-bottom: 12px;
}
.meta-section { margin-bottom: 12px; }
.meta-section h4 { margin: 0 0 6px 0; font-size: 13px; font-weight: 600; color: #333; }
.meta-row { font-size: 13px; margin-bottom: 4px; color: #444; }
.meta-label { font-weight: 600; color: #222; }

mark {
    background: #fff59d;
    padding: 0 2px;
    border-radius: 2px;
}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# BACKEND SIMULATION & MASKING
# ==============================================================================

def get_download_url(user, doc):
    """Generates an authorized backend download URL or returns None if restricted."""
    if not user["can_download"] or doc.get("LOCKED", False):
        return None
    return f"https://your-api-gateway.state.gov/api/v1/download/{doc['DOC_ID']}"

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
    text = re.sub(r"\b(?:\d{3}-\d{2}-\d{4})\b", "***-**-****", text)
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
        ]
        haystack = " ".join(haystack_parts).lower()

        if q:
            terms = q.split()
            if not all(term in haystack for term in terms):
                continue

        # Filters
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

        # Masking
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

        # Highlighting
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

# ==============================================================================
# MAIN APPLICATION & INITIALIZATION
# ==============================================================================

if "selected_user_key" not in st.session_state:
    st.session_state.selected_user_key = list(USERS.keys())[0]
if "search_results" not in st.session_state:
    st.session_state.search_results = None
if "current_payload" not in st.session_state:
    st.session_state.current_payload = None

# Sidebar Context Control
st.sidebar.title("Security Governance")
selected_user_key = st.sidebar.selectbox(
    "Active Persona",
    options=list(USERS.keys()),
    index=list(USERS.keys()).index(st.session_state.selected_user_key),
)
st.session_state.selected_user_key = selected_user_key
current_user = USERS[selected_user_key]

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Role:** `{current_user['role']}`")
st.sidebar.markdown(f"**State Jurisdiction:** `{current_user['state']}`")
st.sidebar.markdown(f"**Allowed Areas:** {', '.join(current_user['business_areas'])}")
st.sidebar.markdown(f"**PII Access:** {'Unmasked' if current_user['unmasked_pii'] else 'Masked'}")
st.sidebar.markdown(f"**Download Permission:** {current_user['can_download']}")

pii_badge = '<span class="badge-full">UNMASKED PII</span>' if current_user["unmasked_pii"] else '<span class="badge-masked">MASKED PII</span>'
download_badge = '<span class="badge-full">DOWNLOAD ENABLED</span>' if current_user["can_download"] else '<span class="badge-denied">DOWNLOAD DENIED</span>'

# Header Navigation
st.markdown(
    f"""
    <div class="sdp-nav">
        <div class="sdp-nav-title">📄 Smart Document Platform — SD / ID</div>
        <div class="sdp-nav-persona">
            <span>{current_user['username']}</span> · <span>{current_user['role']}</span> · <span>{current_user['state']}</span> · {pii_badge} {download_badge}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.title("Document Search & Governance Engine")

# Search Filters Section
top_row1, top_row2 = st.columns([1, 2])
with top_row1:
    selected_ba = st.selectbox(
        "Business Area",
        options=current_user["business_areas"],
        help="Select business area entitlement context.",
    )
with top_row2:
    search_query = st.text_input(
        "Search Term",
        placeholder="Enter keywords (e.g., accident, Sioux Falls, dispute)...",
    )

with st.expander("Advanced Metadata Filters", expanded=True):
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        f_case_type = st.text_input("Case Type Filter")
        f_status = st.text_input("Case Status Filter")
        f_tracking = st.text_input("Tracking ID")
    with f_col2:
        f_investigator = st.text_input("Investigator")
        f_entity = st.text_input("Entity Name")
        f_naic = st.text_input("NAIC Group Number")
    with f_col3:
        f_subtype = st.text_input("Case Subtype")
        f_loi = st.text_input("Line of Insurance (LOI)")

filters = {
    "case_type": f_case_type or None,
    "status": f_status or None,
    "investigator": f_investigator or None,
    "entity": f_entity or None,
    "tracking_id": f_tracking or None,
    "naic_group": f_naic or None,
    "case_subtype": f_subtype or None,
    "loi": f_loi or None,
}

if st.button("Execute Search", type="primary"):
    st.session_state.search_results = run_search(current_user, search_query, selected_ba, filters)
    st.session_state.current_payload = build_search_payload(current_user, search_query, selected_ba, filters)

# ==============================================================================
# SEARCH RESULTS RENDERING
# ==============================================================================

if st.session_state.search_results is not None:
    results = st.session_state.search_results
    st.subheader(f"Search Results ({len(results)} matches found)")

    if not results:
        st.info("No documents match your search criteria or entitlement boundary.")
    else:
        # 1. Summary Data Table
        df_data = []
        for r in results:
            url = get_download_url(current_user, r["_doc"])
            if not current_user["can_download"]:
                status = "🚫 Restricted"
            else:
                status = "✅ Allowed"

            df_data.append({
                "DOC_ID": r["DOC_ID"],
                "Title": r["DOCUMENT_TITLE"],
                "Type": r["DOCUMENT_TYPE"],
                "Upload Date": r["DOCUMENT_DATE"],
                "Business Area": r["BUSINESS_AREA"],
                "State": r["STATE"],
                "Investigator": r["INVESTIGATOR_DISPLAY"],
                "Entity": r["ENTITY_NAME_DISPLAY"],
                "Access Status": status,
                "Download Link": url,
            })

        df = pd.DataFrame(df_data)

        st.dataframe(
            df,
            column_config={
                "Access Status": st.column_config.TextColumn(
                    "Access",
                    help="Authorization and audit lock state",
                    width="small",
                ),
                "Download Link": st.column_config.LinkColumn(
                    "Action",
                    help="Authorized direct document download",
                    validate="^https://",
                    display_text="Download File",
                ),
            },
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # 2. Detailed Document Accordion List
        for r in results:
            doc_id = r["DOC_ID"]
            title = r["DOCUMENT_TITLE"]
            dtype = r["DOCUMENT_TYPE"]
            date = r["DOCUMENT_DATE"]
            ba = r["BUSINESS_AREA"]
            state = r["STATE"]
            
            if not current_user["can_download"]:
                acc_badge = '<span class="badge-denied">RESTRICTED</span>'
            else:
                acc_badge = '<span class="badge-full">ACCESSIBLE</span>'

            header_label = f"{title}  |  {doc_id} · {dtype} · {date} · {ba} · {state}"
            
            with st.expander(header_label, expanded=False):
                col_info, col_snip = st.columns([1, 1])
                with col_info:
                    st.markdown(
                        f"""
                        <div class="meta-section">
                            <div class="meta-row"><span class="meta-label">Title:</span> {escape(title)}</div>
                            <div class="meta-row"><span class="meta-label">Type:</span> {escape(dtype)}</div>
                            <div class="meta-row"><span class="meta-label">Upload Date:</span> {escape(date)}</div>
                            <div class="meta-row"><span class="meta-label">Business Area:</span> {escape(ba)}</div>
                            <div class="meta-row"><span class="meta-label">State:</span> {escape(state)}</div>
                            <div class="meta-row"><span class="meta-label">Investigator:</span> {escape(r['INVESTIGATOR_DISPLAY'])}</div>
                            <div class="meta-row"><span class="meta-label">Entity:</span> {escape(r['ENTITY_NAME_DISPLAY'])}</div>
                            <div class="meta-row"><span class="meta-label">Status:</span> {acc_badge}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with col_snip:
                    st.markdown("**Snippet Context**")
                    st.markdown(
                        f"""<div style="background:#f9f9f9; padding:12px; border-radius:4px; border-left:3px solid #3f51b5; font-style:italic;">{r['SNIPPET']}</div>""",
                        unsafe_allow_html=True
                    )

# ==============================================================================
# TECHNICAL & GOVERNANCE INSPECTOR PANELS
# ==============================================================================

with st.expander("🛠 Governance / Integration Inspector", expanded=False):
    col_g1, col_g2, col_g3 = st.columns(3)

    with col_g1:
        st.markdown("### Backend Payload")
        if st.session_state.current_payload:
            st.json(st.session_state.current_payload)
        else:
            st.info("Run a search to view the generated payload.")

    with col_g2:
        st.markdown("### Authorization Trace")
        st.json({
            "authenticated_user": current_user["username"],
            "role": current_user["role"],
            "jurisdiction": current_user["jurisdiction"],
            "enforced_state": current_user["state"],
            "entitled_business_areas": current_user["business_areas"],
            "pii_representation": "FULL" if current_user["unmasked_pii"] else "MASKED",
            "raw_download": current_user["can_download"],
            "authorization_boundary": "Spring Boot",
            "cortex_search_is_authorization_boundary": False,
        })

    with col_g3:
        st.markdown("### Document Relationship")
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

with st.expander("🧪 Security Test Scenarios", expanded=False):
    st.markdown("""
### Persona-Based Security Demonstrations

1. **SD Regulator** — full metadata, full PII, download enabled  
2. **SD Analyst** — masked PII, Exams only  
3. **ID Analyst** — masked PII, Exams only, download disabled  
4. **State Isolation** — DOC_STATE must match authenticated user  
5. **Business-Area Isolation** — only entitled business areas  
6. **PII Masking** — entity, investigator, filenames masked  
7. **Raw Access Control** — download independently authorized  
8. **Payload Control** — backend selects fields, UI cannot override
""")

with st.expander("📐 Architecture / Data Flow", expanded=False):
    st.markdown("""
### End-to-End Pipeline

`S3 → DOC_SEARCH_CONTENT → Spring Boot Authorization → Cortex Search → SBS.ATTACHMENT / MR_CASE Join → UI`

### Key Architecture Notes

- **DOC_SEARCH_CONTENT** — parsed text + extraction confidence  
- **SBS.ATTACHMENT** — upload metadata  
- **MR_CASE** — case metadata  
- **Authorization Boundary** — Spring Boot enforces entitlement + masking  
- **Cortex Search** — text search only, no authorization  
- **UI** — displays permitted representation only
""")

st.markdown("<br><hr><center><small>Smart Document Platform — Prototype Build</small></center>", unsafe_allow_html=True)
