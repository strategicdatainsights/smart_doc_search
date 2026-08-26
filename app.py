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
    .sdp-nav-title { font-size: 1.2rem; font-weight: 700; letter-spacing: 0.5px; }
    .sdp-nav-persona { font-size: 0.9rem; font-weight: 500; }
    .badge-full { background-color: #10B981; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
    .badge-masked { background-color: #F59E0B; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
    .badge-denied { background-color: #EF4444; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
    .meta-section { background-color: #F8FAFC; padding: 14px; border-radius: 6px; border: 1px solid #E2E8F0; }
    .meta-row { margin-bottom: 4px; font-size: 0.88rem; }
    .meta-label { font-weight: 600; color: #475569; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# PERSONA DEFINITIONS & HARDCODED ENTITLEMENT BOUNDARIES
# ==============================================================================
PERSONA_PROFILES = {
    "Market Conduct Examiner": {
        "username": "reg_examiner@state.gov",
        "default_state": "SD",
        "business_area": "Market Regulation",
        "can_download": True,
        "unmasked_pii": True,
        "role_name": "Market Conduct Examiner",
    },
    "Fraud Unit Investigator": {
        "username": "fraud_investigator@state.gov",
        "default_state": "SD",
        "business_area": "Fraud Investigation",
        "can_download": True,
        "unmasked_pii": True,
        "role_name": "Fraud Unit Investigator",
    },
    "Licensing Specialist": {
        "username": "licensing_spec@state.gov",
        "default_state": "ID",
        "business_area": "Company Licensing",
        "can_download": False,
        "unmasked_pii": True,
    },
    "General Compliance Analyst": {
        "username": "analyst@state.gov",
        "default_state": "SD",
        "business_area": "Market Regulation",
        "can_download": False,
        "unmasked_pii": False,
    },
}

FIELD_MATRIX = {
    "Market Regulation": ["DOC_ID", "DOCUMENT_TITLE", "DOCUMENT_TYPE", "UPLOAD_DATE", "BUSINESS_AREA", "DOC_STATE"],
    "Company Licensing": ["DOC_ID", "DOCUMENT_TITLE", "DOCUMENT_TYPE", "UPLOAD_DATE", "BUSINESS_AREA", "DOC_STATE"],
    "Fraud Investigation": ["DOC_ID", "DOCUMENT_TITLE", "DOCUMENT_TYPE", "UPLOAD_DATE", "BUSINESS_AREA", "DOC_STATE"],
}

# Dynamic Synthetic Document Dataset Generator
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
        "CASE_TYPE": "Enforcement" if i % 2 == 0 else "Compliance Review",
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
        "CONTENT_TEXT": f"{doc_type} generated for {entity} operating in state jurisdiction {state}. Assigned investigator {investigator}. Case tracking ID {trk_id}.",
    })

# ==============================================================================
# MASKING & SEARCH SERVICES
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
    text = re.sub(r"\b(?:\d{3}-\d{2}-\d{4})\b", "***-**-****", text)
    return text

def build_search_payload(user_context, query):
    allowed_cols = FIELD_MATRIX[user_context["business_area"]]
    cortex_filter = {
        "@and": [
            {"@eq": {"DOC_STATE": user_context["state"]}},
            {"@eq": {"BUSINESS_AREA": user_context["business_area"]}},
            {"@eq": {"IS_CURRENT": True}},
        ]
    }
    return {
        "query": query,
        "columns": allowed_cols,
        "filter": cortex_filter,
        "limit": 10,
        "persona_context": user_context["persona_name"],
        "entitlement_business_area": user_context["business_area"],
        "pii_policy": "UNMASKED" if user_context["unmasked_pii"] else "MASKED",
        "download_policy": "ENABLED" if user_context["can_download"] else "RESTRICTED",
    }

def run_search(user_context, query):
    q = query.strip().lower()
    results = []

    for d in DOC_SEARCH_CONTENT:
        # Strict isolation: State override + Persona Business Area
        if d["DOC_STATE"] != user_context["state"] or d["BUSINESS_AREA"] != user_context["business_area"]:
            continue

        attachment = SBS_ATTACHMENTS.get(d["ATTACHMENT_ID"])
        if not attachment:
            continue
        case = SBS_CASES.get(attachment["TRACKING_ID"])
        if not case:
            continue

        haystack = f"{d['CONTENT_TEXT']} {d['DOCUMENT_TITLE']} {attachment['FILE_NAME']} {case['ENTITY_NAME']} {case['INVESTIGATOR']}".lower()

        if q and not all(term in haystack for term in q.split()):
            continue

        # Enforce Persona PII Masking
        if user_context["unmasked_pii"]:
            display_entity = case["ENTITY_NAME"]
            display_investigator = case["INVESTIGATOR"]
            snippet = d["CONTENT_TEXT"]
        else:
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
            "DOCUMENT_TITLE": d["DOCUMENT_TITLE"],
            "DOCUMENT_TYPE": d["DOCUMENT_TYPE"],
            "DOCUMENT_DATE": d["UPLOAD_DATE"],
            "BUSINESS_AREA": d["BUSINESS_AREA"],
            "STATE": d["DOC_STATE"],
            "SNIPPET": snippet,
            "INVESTIGATOR_DISPLAY": display_investigator,
            "ENTITY_NAME_DISPLAY": display_entity,
            "CAN_DOWNLOAD": user_context["can_download"],
            "_doc": d,
        })

    return results

# ==============================================================================
# STATE & SESSION INITIALIZATION
# ==============================================================================
if "search_results" not in st.session_state:
    st.session_state.search_results = None
if "current_payload" not in st.session_state:
    st.session_state.current_payload = None

# Track persistent state override independently from Persona selection
if "selected_state" not in st.session_state:
    st.session_state.selected_state = "SD"

# ==============================================================================
# MAIN APPLICATION & CONTROLS
# ==============================================================================

# 1. Persona Choice Drive Identity; Independent State Dropdown Allows Override
col_persona, col_state = st.columns([2, 1])

with col_persona:
    selected_persona_name = st.selectbox(
        "User Persona",
        options=list(PERSONA_PROFILES.keys()),
        index=0
    )

persona_config = PERSONA_PROFILES[selected_persona_name]

with col_state:
    # State override maintains independent control
    selected_state = st.selectbox(
        "State Override",
        options=["SD", "ID"],
        index=0 if st.session_state.selected_state == "SD" else 1,
    )
    st.session_state.selected_state = selected_state

# Construct Resolved Operational Context
user_context = {
    "persona_name": selected_persona_name,
    "username": persona_config["username"],
    "state": selected_state,
    "business_area": persona_config["business_area"],
    "can_download": persona_config["can_download"],
    "unmasked_pii": persona_config["unmasked_pii"],
}

# UI Navigation Header
pii_badge = '<span class="badge-full">UNMASKED PII</span>' if user_context["unmasked_pii"] else '<span class="badge-masked">MASKED PII</span>'
download_badge = '<span class="badge-full">DOWNLOAD ALLOWED</span>' if user_context["can_download"] else '<span class="badge-denied">DOWNLOAD RESTRICTED</span>'

st.markdown(
    f"""
    <div class="sdp-nav">
        <div class="sdp-nav-title">📄 Smart Document Platform — SD / ID</div>
        <div class="sdp-nav-persona">
            <span>{user_context['username']}</span> · <span>Persona: <b>{user_context['persona_name']}</b></span> · <span>Business Area: <b>{user_context['business_area']}</b></span> · <span>Jurisdiction: <b>{user_context['state']}</b></span> · {pii_badge} {download_badge}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.title("Document Search & Governance Engine")

# Search Interface: Business Area is automatically locked to Persona Entitlement
search_col, button_col = st.columns([3, 1])

with search_col:
    search_query = st.text_input(
        f"Search within '{user_context['business_area']}' ({user_context['state']} Jurisdiction)",
        placeholder="Enter keywords (e.g., accident, Mutual, dispute)...",
    )

with button_col:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    execute_click = st.button("Execute Search", type="primary", use_container_width=True)

if execute_click:
    st.session_state.search_results = run_search(user_context, search_query)
    st.session_state.current_payload = build_search_payload(user_context, search_query)

# ==============================================================================
# SEARCH RESULTS RENDERING
# ==============================================================================
if st.session_state.search_results is not None:
    results = st.session_state.search_results
    st.subheader(f"Search Results ({len(results)} matches found)")

    if not results:
        st.info(f"No documents match your search query under the '{user_context['business_area']}' boundary in state {user_context['state']}.")
    else:
        # Table Summary View
        df_data = []
        for r in results:
            df_data.append({
                "DOC_ID": r["DOC_ID"],
                "Title": r["DOCUMENT_TITLE"],
                "Type": r["DOCUMENT_TYPE"],
                "Upload Date": r["DOCUMENT_DATE"],
                "Business Area": r["BUSINESS_AREA"],
                "State": r["STATE"],
                "Investigator": r["INVESTIGATOR_DISPLAY"],
                "Entity": r["ENTITY_NAME_DISPLAY"],
                "Access": "✅ Allowed" if r["CAN_DOWNLOAD"] else "🚫 Restricted",
                "Action": f"https://your-api-gateway.state.gov/api/v1/download/{r['DOC_ID']}" if r["CAN_DOWNLOAD"] else None,
            })
            
        st.dataframe(
            pd.DataFrame(df_data),
            column_config={
                "Access": st.column_config.TextColumn("Access", width="small"),
                "Action": st.column_config.LinkColumn(
                    "Action",
                    help="Authorized direct document download link",
                    display_text="Download File",
                ),
            },
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Document Accordion View
        for r in results:
            header_label = f"{r['DOCUMENT_TITLE']}  |  {r['DOC_ID']} · {r['DOCUMENT_TYPE']} · {r['DOCUMENT_DATE']} · {r['BUSINESS_AREA']} · {r['STATE']}"
            with st.expander(header_label, expanded=False):
                col_info, col_snip = st.columns([1, 1])
                with col_info:
                    st.markdown(
                        f"""
                        <div class="meta-section">
                            <div class="meta-row"><span class="meta-label">Title:</span> {escape(r['DOCUMENT_TITLE'])}</div>
                            <div class="meta-row"><span class="meta-label">Type:</span> {escape(r['DOCUMENT_TYPE'])}</div>
                            <div class="meta-row"><span class="meta-label">Upload Date:</span> {escape(r['DOCUMENT_DATE'])}</div>
                            <div class="meta-row"><span class="meta-label">Business Area:</span> {escape(r['BUSINESS_AREA'])}</div>
                            <div class="meta-row"><span class="meta-label">State:</span> {escape(r['STATE'])}</div>
                            <div class="meta-row"><span class="meta-label">Investigator:</span> {escape(r['INVESTIGATOR_DISPLAY'])}</div>
                            <div class="meta-row"><span class="meta-label">Entity:</span> {escape(r['ENTITY_NAME_DISPLAY'])}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with col_snip:
                    st.markdown("**Snippet Context**")
                    st.markdown(
                        f"""<div style="background:#f9f9f9; padding:12px; border-radius:4px; border-left:3px solid #1E3A8A; font-style:italic;">{r['SNIPPET']}</div>""",
                        unsafe_allow_html=True
                    )

# ==============================================================================
# SYSTEM ARCHITECTURE & GOVERNANCE ACCORDIONS
# ==============================================================================
st.markdown("<br>", unsafe_allow_html=True)

with st.expander("🛠 Governance / Integration Inspector", expanded=False):
    if st.session_state.current_payload:
        st.json(st.session_state.current_payload)
    else:
        st.info("Execute a search query to generate active Cortex payloads and inspect entitlement parameters.")

with st.expander("🧪 Security Test Scenarios", expanded=False):
    st.markdown("""
    - **Persona Entitlement Locks**: Select **Fraud Unit Investigator** to lock queries to *Fraud Investigation* with unmasked PII. Switch to **General Compliance Analyst** to see *Market Regulation* boundaries with masked PII.
    - **State Cross-Jurisdiction**: Toggle the **State Override** dropdown between **SD** and **ID** independently without resetting the active Persona profile.
    - **Audit Traceability**: Observe the full username signature in the navigation header (e.g., `fraud_investigator@state.gov`).
    """)

with st.expander("📐 Architecture / Data Flow", expanded=False):
    st.markdown("""
    1. **Persona Authentication**: User persona locks down entitlement boundaries (`Business Area`, PII masking policy, download capabilities).
    2. **State Override Layer**: Allows inspectors and analysts to dynamically execute cross-jurisdictional queries without altering core rights.
    3. **Snowflake Cortex Engine**: Restricts data retrieval using combined filters: `DOC_STATE` + `BUSINESS_AREA`.
    """)
