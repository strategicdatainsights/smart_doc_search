import math
import re
from html import escape
import pandas as pd
import streamlit as st

# ==============================================================================
# PAGE CONFIG & CUSTOM CSS
# ==============================================================================
st.set_page_config(
    page_title="Smart Document Platform — SD / ID",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .sdp-nav {
        background-color: #1E3A8A;
        padding: 12px 20px;
        border-radius: 6px;
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    .sdp-nav-title {
        font-size: 1.2rem;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .sdp-nav-persona {
        font-size: 0.9rem;
        font-weight: 500;
    }
    .badge-full {
        background-color: #10B981;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-masked {
        background-color: #F59E0B;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-denied {
        background-color: #EF4444;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .meta-section {
        background-color: #F8FAFC;
        padding: 14px;
        border-radius: 6px;
        border: 1px solid #E2E8F0;
    }
    .meta-row {
        margin-bottom: 4px;
        font-size: 0.88rem;
    }
    .meta-label {
        font-weight: 600;
        color: #475569;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# MOCK DATASETS & FIELD MATRIX (50 RECORD GENERATOR)
# ==============================================================================
USERS = {
    "reg_sd_user": {
        "username": "reg_sd_user@state.gov",
        "role": "STATE_REGULATOR",
        "state": "SD",
        "business_areas": ["Market Regulation", "Company Licensing"],
        "unmasked_pii": False,
        "can_download": True,
    },
    "reg_id_user": {
        "username": "reg_id_user@state.gov",
        "role": "STATE_REGULATOR",
        "state": "ID",
        "business_areas": ["Market Regulation"],
        "unmasked_pii": False,
        "can_download": True,
    },
    "fraud_investigator": {
        "username": "investigator@state.gov",
        "role": "INVESTIGATOR",
        "state": "SD",
        "business_areas": ["Fraud Investigation", "Market Regulation"],
        "unmasked_pii": True,
        "can_download": True,
    },
    "analyst_no_download": {
        "username": "analyst@state.gov",
        "role": "ANALYST",
        "state": "SD",
        "business_areas": ["Market Regulation"],
        "unmasked_pii": False,
        "can_download": False,
    },
}

FIELD_MATRIX = {
    "Market Regulation": {
        "base": ["DOC_ID", "DOCUMENT_TITLE", "DOCUMENT_TYPE", "UPLOAD_DATE", "BUSINESS_AREA", "DOC_STATE"]
    },
    "Company Licensing": {
        "base": ["DOC_ID", "DOCUMENT_TITLE", "DOCUMENT_TYPE", "UPLOAD_DATE", "BUSINESS_AREA", "DOC_STATE"]
    },
    "Fraud Investigation": {
        "base": ["DOC_ID", "DOCUMENT_TITLE", "DOCUMENT_TYPE", "UPLOAD_DATE", "BUSINESS_AREA", "DOC_STATE"]
    },
}

# --- 50 RECORD DYNAMIC GENERATOR ---
SBS_ATTACHMENTS = {}
SBS_CASES = {}
DOC_SEARCH_CONTENT = []

entities = [
    "Prairie Plains Mutual Insurance Company", "Black Hills Mutual Insurance Company",
    "Dakota National Life", "Rushmore Casualty Co.", "Sioux Falls Title & Escrow",
    "Idaho Timber Mutual", "Boise Valley Risk Partners", "Gem State Indemnity"
]
investigators = ["A. Miller", "R. Vance", "J. Doe", "C. Smith", "K. Johnson", "M. Davis"]
doc_types = ["Accident Report", "Dispute Letter", "License Renewal Application", "Audit Assessment", "Fraud Referral"]
business_areas = ["Market Regulation", "Company Licensing", "Fraud Investigation"]
case_types = ["Enforcement", "Dispute", "Compliance Review", "Fraud Investigation"]
statuses = ["Open", "Under Review", "Closed", "Pending Hearing"]
subtypes = ["Auto Claim", "Policy Dispute", "Financial Audit", "Agent Conduct"]
lines_of_insurance = ["Property & Casualty", "Life & Health", "Commercial Liability", "Workers Comp"]

for i in range(1, 51):
    doc_id = f"DOC-{10000 + i}"
    att_id = f"ATT-{1000 + i}"
    trk_id = f"TRK-{9000 + i}"
    state = "SD" if i % 2 != 0 else "ID"
    ba = business_areas[i % len(business_areas)]
    entity = entities[i % len(entities)]
    investigator = investigators[i % len(investigators)]
    doc_type = doc_types[i % len(doc_types)]
    
    SBS_ATTACHMENTS[att_id] = {
        "FILE_NAME": f"{doc_type.replace(' ', '_')}_Record_{i}.pdf",
        "TRACKING_ID": trk_id
    }
    
    SBS_CASES[trk_id] = {
        "ENTITY_NAME": entity,
        "INVESTIGATOR": investigator,
        "SECONDARY_INVESTIGATOR": "J. Doe" if i % 3 == 0 else None,
        "CASE_TYPE": case_types[i % len(case_types)],
        "CASE_STATUS": statuses[i % len(statuses)],
        "CASE_SUBTYPE": subtypes[i % len(subtypes)],
        "LOI": lines_of_insurance[i % len(lines_of_insurance)],
        "NAIC_GROUP_NUMBER": str(10000 + (i * 123)),
    }
    
    DOC_SEARCH_CONTENT.append({
        "DOC_ID": doc_id,
        "ATTACHMENT_ID": att_id,
        "DOCUMENT_TITLE": f"{doc_type} — Record #{i} ({entity})",
        "DOCUMENT_TYPE": doc_type,
        "UPLOAD_DATE": f"2024-10-{(i % 28) + 1:02d}",
        "BUSINESS_AREA": ba,
        "DOC_STATE": state,
        "IS_CURRENT": True,
        "CONTENT_TEXT": f"{doc_type} generated for {entity} operating in state jurisdiction {state}. Assigned primary investigator {investigator}. Review case details under tracking ID {trk_id}.",
    })

# ==============================================================================
# BACKEND SIMULATION & MASKING
# ==============================================================================

def get_download_url(user, doc):
    """Generates an authorized backend download URL for the document record."""
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

# Context Controls (Persona & State Jurisdiction)
c_persona, c_state = st.columns([1, 1])
with c_persona:
    selected_user_key = st.selectbox(
        "Active Persona",
        options=list(USERS.keys()),
        index=list(USERS.keys()).index(st.session_state.selected_user_key),
    )
    st.session_state.selected_user_key = selected_user_key
    base_user = USERS[selected_user_key]

available_states = sorted(list({u["state"] for u in USERS.values()}))

with c_state:
    selected_state = st.selectbox(
        "State Jurisdiction",
        options=available_states,
        index=available_states.index(base_user["state"]) if base_user["state"] in available_states else 0,
    )

# Active User Context with Dynamic State Override
current_user = {
    **base_user,
    "state": selected_state,
}

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
            
            # Binary entitlement status matching wireframe
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
                    help="Authorization state",
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

        # 3. Backend Search Payload Inspector
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("🔍 View Backend Search Payload (Governance & Cortex AI Debug)", expanded=False):
            st.json(st.session_state.current_payload)
