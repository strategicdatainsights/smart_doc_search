import streamlit as st

# ==============================================================================
# PAGE CONFIG
# ==============================================================================
st.set_page_config(
    page_title="Smart Document Platform — Search",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==============================================================================
# CSS — no external icon fonts, no Material Icons
# ==============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Roboto', sans-serif !important;
}

/* Hide default streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0 !important; }

/* ── Nav bar ── */
.sdp-nav {
    background: #3f51b5;
    color: white;
    padding: 14px 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    margin-bottom: 24px;
}
.sdp-nav-title { font-size: 18px; font-weight: 500; }
.sdp-nav-persona {
    background: rgba(255,255,255,0.18);
    border-radius: 4px;
    padding: 5px 12px;
    font-size: 12px;
}

/* ── Legend ── */
.sdp-legend {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 12px 20px;
    margin-bottom: 20px;
    display: flex;
    gap: 28px;
    align-items: center;
    font-size: 13px;
    color: #444;
}
.req { color: #f44336; font-weight: 700; }
.smart-badge {
    display: inline-flex;
    align-items: center;
    font-size: 11px;
    color: #7c4dff;
    background: #ede7f6;
    padding: 2px 8px;
    border-radius: 12px;
    font-weight: 600;
    margin-left: 6px;
    vertical-align: middle;
}

/* ── Cards ── */
.sdp-card-header {
    background: white;
    border: 1px solid #e0e0e0;
    border-bottom: none;
    border-radius: 8px 8px 0 0;
    padding: 14px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.sdp-card-header h2 {
    font-size: 17px;
    font-weight: 500;
    color: #3f51b5;
    margin: 0;
}
.sdp-card-body {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 0 0 8px 8px;
    padding: 20px;
    margin-bottom: 24px;
}

/* ── Form labels ── */
.sdp-label {
    font-size: 12px;
    font-weight: 500;
    color: #555;
    margin-bottom: 3px;
    display: block;
}
.sdp-hint {
    font-size: 11px;
    color: #999;
    font-style: italic;
    margin-top: 3px;
}
.sdp-divider {
    border: none;
    border-top: 1px solid #e0e0e0;
    margin: 16px 0;
}

/* ── Chips ── */
.sdp-chips {
    background: #f9f9f9;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 10px 16px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
    margin-bottom: 14px;
}
.sdp-chip-label { font-size: 12px; color: #666; font-weight: 500; }
.sdp-chip {
    background: #e8eaf6;
    color: #3f51b5;
    padding: 4px 12px;
    border-radius: 16px;
    font-size: 12px;
    font-weight: 500;
}

/* ── Results table ── */
.sdp-table-wrap {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 24px;
}
.sdp-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}
.sdp-table thead { background: #fafafa; }
.sdp-table th {
    padding: 11px 14px;
    text-align: left;
    font-weight: 500;
    color: #555;
    border-bottom: 2px solid #e0e0e0;
    white-space: nowrap;
}
.sdp-table td {
    padding: 11px 14px;
    border-bottom: 1px solid #f0f0f0;
    vertical-align: top;
}
.sdp-table tr:last-child td { border-bottom: none; }
.sdp-table tr:hover td { background: #f5f5f5; }
.sdp-trk-link { color: #3f51b5; font-weight: 500; text-decoration: none; }
.sdp-snippet { font-style: italic; color: #555; max-width: 380px; display: block; }
.sdp-snippet mark { background: #fff59d; padding: 0 2px; border-radius: 2px; font-style: normal; }
.sdp-lock { color: #f57c00; }
.sdp-dl-btn {
    padding: 4px 10px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background: white;
    cursor: pointer;
    font-size: 12px;
}
.sdp-dl-denied { color: #f44336; font-size: 12px; }

/* ── Pagination ── */
.sdp-pagination {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 16px;
    border-top: 1px solid #e0e0e0;
    background: #fafafa;
    font-size: 13px;
    color: #666;
}

/* ── Button overrides ── */
div[data-testid="stButton"] > button {
    font-family: 'Roboto', sans-serif !important;
    font-weight: 500 !important;
    border-radius: 4px !important;
    transition: background 0.15s;
}

/* ── Expander overrides — remove arrow icon artifacts ── */
div[data-testid="stExpander"] > details > summary {
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #333 !important;
    background: #fafafa !important;
    padding: 12px 16px !important;
    border-radius: 0 !important;
    list-style: none !important;
}
div[data-testid="stExpander"] > details > summary::-webkit-details-marker { display: none; }
div[data-testid="stExpander"] {
    border: 1px solid #e0e0e0 !important;
    border-radius: 4px !important;
    margin-bottom: 1px !important;
    overflow: hidden !important;
}
div[data-testid="stExpander"] > details {
    border: none !important;
}

/* ── Input / select consistency ── */
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stSelectbox"] select {
    border: 1px solid #ccc !important;
    border-radius: 4px !important;
    font-size: 14px !important;
    font-family: 'Roboto', sans-serif !important;
}
div[data-testid="stTextInput"] label,
div[data-testid="stTextArea"] label,
div[data-testid="stSelectbox"] label,
div[data-testid="stDateInput"] label,
div[data-testid="stMultiSelect"] label {
    font-size: 12px !important;
    font-weight: 500 !important;
    color: #555 !important;
}

/* Masking info badge */
.access-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    margin-left: 6px;
}
.access-full { background: #e8f5e9; color: #2e7d32; }
.access-masked { background: #fff3e0; color: #e65100; }
.access-denied { background: #ffebee; color: #c62828; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# MOCK DATA
# ==============================================================================
MOCK_USERS = {
    "Regulator — RI (Full Access, Unmasked)": {
        "username": "e.rosso@regulator.ri.gov",
        "role": "STATE_REGULATOR",
        "state": "RI",
        "entitled_business_areas": ["Market Regulation", "Complaints", "Exams"],
        "can_download": True,
        "sees_unmasked_pii": True,
    },
    "Analyst — RI (Exams Only, Masked)": {
        "username": "j.smith@state.ri.gov",
        "role": "FINANCIAL_ANALYST",
        "state": "RI",
        "entitled_business_areas": ["Exams"],
        "can_download": True,
        "sees_unmasked_pii": False,
    },
    "Analyst — MA (Exams Only, No Download)": {
        "username": "d.jones@state.ma.gov",
        "role": "FINANCIAL_ANALYST",
        "state": "MA",
        "entitled_business_areas": ["Exams"],
        "can_download": False,
        "sees_unmasked_pii": False,
    },
}

MOCK_DOCUMENTS = [
    {
        "ATTACHMENT_ID": "890786543",
        "TRACKING_ID": "12350",
        "FILE_NAME": "court_doc.docx",
        "LOCKED": False,
        "UPLOAD_DATE": "10/03/2019",
        "CREATED_BY": "Luna Rover",
        "STATE": "RI",
        "BUSINESS_AREA": "Market Regulation",
        "CASE_TYPE": "Complaints",
        "CASE_STATUS": "Open",
        "INVESTIGATOR": "A. Miller",
        "ENTITY_NAME": "Apex Holdings LLC",
        "ENTITY_NAME_MASKED": "Ap** Ho****** LLC",
        "CHUNK_TEXT": "Accident appears to have occurred on Monday evening at the intersection of Main and Broad Street.",
        "DOC_TYPE": ".docx",
    },
    {
        "ATTACHMENT_ID": "890786544",
        "TRACKING_ID": "12351",
        "FILE_NAME": "JaneDoe_2024301.pdf",
        "LOCKED": True,
        "UPLOAD_DATE": "12/22/2019",
        "CREATED_BY": "Paddington Bear",
        "STATE": "RI",
        "BUSINESS_AREA": "Market Regulation",
        "CASE_TYPE": "Enforcement",
        "CASE_STATUS": "Closed",
        "INVESTIGATOR": "R. Vance",
        "ENTITY_NAME": "Beacon Mutual Insurance",
        "ENTITY_NAME_MASKED": "Be**** Mu**** Insurance",
        "CHUNK_TEXT": "In regards to the accident that occurred on the evening of December 19th the claimant filed a formal dispute.",
        "DOC_TYPE": ".pdf",
    },
    {
        "ATTACHMENT_ID": "890786545",
        "TRACKING_ID": "12352",
        "FILE_NAME": "uniformdoc.pdf",
        "LOCKED": False,
        "UPLOAD_DATE": "01/05/2020",
        "CREATED_BY": "Garfield Arbuckle",
        "STATE": "RI",
        "BUSINESS_AREA": "Complaints",
        "CASE_TYPE": "Complaints",
        "CASE_STATUS": "Open",
        "INVESTIGATOR": "A. Miller",
        "ENTITY_NAME": "Progressive Insurance",
        "ENTITY_NAME_MASKED": "Pr********* Insurance",
        "CHUNK_TEXT": "In regards to the accident that occurred on Monday the policyholder submitted a formal complaint regarding claim denial.",
        "DOC_TYPE": ".pdf",
    },
    {
        "ATTACHMENT_ID": "890786546",
        "TRACKING_ID": "12345",
        "FILE_NAME": "AccidentDetail.pdf",
        "LOCKED": False,
        "UPLOAD_DATE": "01/22/2019",
        "CREATED_BY": "Hudson Burgess",
        "STATE": "RI",
        "BUSINESS_AREA": "Exams",
        "CASE_TYPE": "Market Conduct Exams",
        "CASE_STATUS": "Under Review",
        "INVESTIGATOR": "C. Davis",
        "ENTITY_NAME": "Bay State Life Underwriters",
        "ENTITY_NAME_MASKED": "Ba* St*** Li** Underwriters",
        "CHUNK_TEXT": "Details of damage sustained by vehicle after accident — total loss assessment filed by adjuster.",
        "DOC_TYPE": ".pdf",
    },
    {
        "ATTACHMENT_ID": "890786547",
        "TRACKING_ID": "12355",
        "FILE_NAME": "CornwallMotorcycleClub.docx",
        "LOCKED": False,
        "UPLOAD_DATE": "02/10/2020",
        "CREATED_BY": "Indiana Jones",
        "STATE": "MA",
        "BUSINESS_AREA": "Exams",
        "CASE_TYPE": "Market Conduct Exams",
        "CASE_STATUS": "Closed",
        "INVESTIGATOR": "C. Davis",
        "ENTITY_NAME": "Cornwall Group LLC",
        "ENTITY_NAME_MASKED": "Co****** Gr*** LLC",
        "CHUNK_TEXT": "Details of accident damage assessment from third party inspector retained by Cornwall Group.",
        "DOC_TYPE": ".docx",
    },
]

# ==============================================================================
# SESSION STATE
# ==============================================================================
if "selected_user" not in st.session_state:
    st.session_state.selected_user = list(MOCK_USERS.keys())[0]
if "search_results" not in st.session_state:
    st.session_state.search_results = None
if "search_query_used" not in st.session_state:
    st.session_state.search_query_used = ""
if "show_col_case_type" not in st.session_state:
    st.session_state.show_col_case_type = False
if "show_col_investigator" not in st.session_state:
    st.session_state.show_col_investigator = False
if "show_col_status" not in st.session_state:
    st.session_state.show_col_status = False
if "show_col_entity" not in st.session_state:
    st.session_state.show_col_entity = False

user_info = MOCK_USERS[st.session_state.selected_user]

# ==============================================================================
# NAV BAR
# ==============================================================================
pii_label = "Unmasked PII" if user_info["sees_unmasked_pii"] else "Masked PII"
dl_label = "Download: Yes" if user_info["can_download"] else "Download: No"
st.markdown(f"""
<div class="sdp-nav">
    <span class="sdp-nav-title">Smart Document Platform — Search</span>
    <span class="sdp-nav-persona">
        👤 {user_info['username']} &nbsp;·&nbsp; {user_info['state']} &nbsp;·&nbsp; {user_info['role']} &nbsp;·&nbsp; {pii_label} &nbsp;·&nbsp; {dl_label}
    </span>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# PERSONA SWITCHER
# ==============================================================================
pc1, pc2, pc3 = st.columns([2, 2, 1])
with pc3:
    new_user = st.selectbox(
        "Switch persona",
        list(MOCK_USERS.keys()),
        index=list(MOCK_USERS.keys()).index(st.session_state.selected_user),
        label_visibility="collapsed",
        key="persona_selector"
    )
    if new_user != st.session_state.selected_user:
        st.session_state.selected_user = new_user
        st.session_state.search_results = None
        st.rerun()

user_info = MOCK_USERS[st.session_state.selected_user]

# ==============================================================================
# LEGEND
# ==============================================================================
st.markdown("""
<div class="sdp-legend">
    <span><span class="req">*</span>&nbsp; Required Field</span>
    <span><span class="smart-badge">✦ Smart</span>&nbsp; AI-powered search (Snowflake Cortex)</span>
    <span><span style="color:#f57c00;">🔒</span>&nbsp; Locked document</span>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# SEARCH CRITERIA
# ==============================================================================
st.markdown('<div class="sdp-card-header"><h2>Search Criteria</h2></div><div class="sdp-card-body">', unsafe_allow_html=True)

# Business Area
st.markdown('<span class="sdp-label">Business Area <span class="req">*</span></span>', unsafe_allow_html=True)
ba_options = [""] + user_info["entitled_business_areas"]
business_area = st.selectbox(
    "Business Area",
    ba_options,
    format_func=lambda x: "-- Select Business Area --" if x == "" else x,
    label_visibility="collapsed",
    key="ba_select"
)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# Search Document Contents
st.markdown('<span class="sdp-label">Search Document Contents <span class="req">*</span><span class="smart-badge">✦ Smart</span></span>', unsafe_allow_html=True)
search_query = st.text_area(
    "Search Document Contents",
    placeholder="Enter search terms to find within document text...",
    height=90,
    label_visibility="collapsed",
    key="search_query"
)
st.markdown('<span class="sdp-hint">Search within the text of all attached documents. Minimum 3 characters.</span>', unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── Accordion sections ──

with st.expander("Case Details", expanded=True):
    ca1, ca2 = st.columns(2)
    with ca1:
        case_type = st.selectbox(
            "Case Type",
            ["", "Complaints", "Enforcement", "Market Conduct Exams"],
            format_func=lambda x: "-- Select --" if x == "" else x,
            key="case_type"
        )
    with ca2:
        tracking_id = st.text_input("Tracking ID", placeholder="e.g., 12345", key="tracking_id")

    ca3, ca4 = st.columns(2)
    with ca3:
        st.markdown('<span class="sdp-label">Investigator <span class="smart-badge">✦ Smart</span></span>', unsafe_allow_html=True)
        investigator = st.text_input(
            "Investigator",
            placeholder="Search by investigator name",
            label_visibility="collapsed",
            key="investigator"
        )
        st.markdown('<span class="sdp-hint">Searches Primary and Secondary investigators.</span>', unsafe_allow_html=True)
    with ca4:
        case_status = st.selectbox(
            "Status",
            ["", "Open", "Closed", "Under Review", "Pending"],
            format_func=lambda x: "-- Select --" if x == "" else x,
            key="case_status"
        )

with st.expander("Entity"):
    e1, e2 = st.columns(2)
    with e1:
        st.markdown('<span class="sdp-label">Entity Name <span class="smart-badge">✦ Smart</span></span>', unsafe_allow_html=True)
        entity_name = st.text_input(
            "Entity Name",
            placeholder="Search by person or company name",
            label_visibility="collapsed",
            key="entity_name"
        )
        st.markdown('<span class="sdp-hint">Handles partial names, company names, or combinations.</span>', unsafe_allow_html=True)
    with e2:
        naic_group = st.selectbox(
            "NAIC Group Number",
            ["", "9083 - 21st Century Company", "8056 - 53rd Order of Insurance"],
            format_func=lambda x: "-- Select --" if x == "" else x,
            key="naic_group"
        )

with st.expander("Dates"):
    d1, d2 = st.columns(2)
    with d1:
        st.write("Case Initiated")
        di1, di2 = st.columns(2)
        with di1:
            case_init_from = st.date_input("From", value=None, key="ci_from", label_visibility="collapsed")
        with di2:
            case_init_to = st.date_input("To", value=None, key="ci_to", label_visibility="collapsed")
    with d2:
        st.write("Case Opened")
        do1, do2 = st.columns(2)
        with do1:
            case_open_from = st.date_input("From", value=None, key="co_from", label_visibility="collapsed")
        with do2:
            case_open_to = st.date_input("To", value=None, key="co_to", label_visibility="collapsed")

    d3, d4 = st.columns(2)
    with d3:
        st.write("Case Closed")
        dc1, dc2 = st.columns(2)
        with dc1:
            case_close_from = st.date_input("From", value=None, key="cc_from", label_visibility="collapsed")
        with dc2:
            case_close_to = st.date_input("To", value=None, key="cc_to", label_visibility="collapsed")
    with d4:
        st.write("File Upload")
        df1, df2 = st.columns(2)
        with df1:
            file_upload_from = st.date_input("From", value=None, key="fu_from", label_visibility="collapsed")
        with df2:
            file_upload_to = st.date_input("To", value=None, key="fu_to", label_visibility="collapsed")

with st.expander("Document"):
    doc1, doc2 = st.columns(2)
    with doc1:
        st.markdown('<span class="sdp-label">Document Name <span class="smart-badge">✦ Smart</span></span>', unsafe_allow_html=True)
        doc_name = st.text_input(
            "Document Name",
            placeholder="e.g., accident report, policy letter",
            label_visibility="collapsed",
            key="doc_name"
        )
    with doc2:
        file_type = st.selectbox(
            "File Type",
            ["", ".pdf", ".docx / .doc", ".xlsx", ".msg", ".ppt", ".csv"],
            format_func=lambda x: "-- Select --" if x == "" else x,
            key="file_type"
        )

with st.expander("Additional Details"):
    ad1, ad2, ad3 = st.columns(3)
    with ad1:
        case_subtype = st.selectbox(
            "Case Sub-Type",
            ["", "Administrative Report", "Franchise", "Inquiry", "Investigations", "Market Conduct", "Multi-State", "PBM", "Securities"],
            format_func=lambda x: "-- Select --" if x == "" else x,
            key="case_subtype"
        )
    with ad2:
        state_keyword = st.multiselect(
            "State Keyword",
            ["COVID-19", "Data Breach", "Fires Summer 2023", "Hurricane", "Pet Insurance", "Tornado"],
            key="state_keyword"
        )
    with ad3:
        reason = st.selectbox(
            "Reason",
            ["", "Reason 1", "Reason 2", "Reason 3"],
            format_func=lambda x: "-- Select --" if x == "" else x,
            key="reason"
        )
    ad4, ad5 = st.columns(2)
    with ad4:
        st.markdown('<span class="sdp-label">Line of Insurance <span class="smart-badge">✦ Smart</span></span>', unsafe_allow_html=True)
        loi = st.text_input(
            "Line of Insurance",
            placeholder="e.g., property, casualty, auto",
            label_visibility="collapsed",
            key="loi"
        )
        st.markdown('<span class="sdp-hint">Searches Coverage Type, Line of Insurance, Line of Business, and RIRS Line of Business.</span>', unsafe_allow_html=True)
    with ad5:
        st.markdown('<span class="sdp-label">Disposition <span class="smart-badge">✦ Smart</span></span>', unsafe_allow_html=True)
        disposition = st.text_input(
            "Disposition",
            placeholder="e.g., settled, dismissed",
            label_visibility="collapsed",
            key="disposition"
        )

st.markdown("</div>", unsafe_allow_html=True)

# ── Active filter chips ──
active_chips = []
if business_area:
    active_chips.append(f"Business Area: {business_area}")
if case_type:
    active_chips.append(f"Case Type: {case_type}")
if search_query:
    q_short = search_query[:28] + "..." if len(search_query) > 28 else search_query
    active_chips.append(f'Contents: "{q_short}"')
if investigator:
    active_chips.append(f"Investigator: {investigator}")
if entity_name:
    active_chips.append(f"Entity: {entity_name}")
if case_status:
    active_chips.append(f"Status: {case_status}")
if tracking_id:
    active_chips.append(f"Tracking ID: {tracking_id}")

if active_chips:
    chips_html = '<div class="sdp-chips"><span class="sdp-chip-label">Active Filters:</span>'
    for c in active_chips:
        chips_html += f'<span class="sdp-chip">{c}</span>'
    chips_html += '</div>'
    st.markdown(chips_html, unsafe_allow_html=True)

# ── Search / Reset buttons ──
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
b1, b2, b3 = st.columns([1, 1, 6])
with b1:
    search_clicked = st.button("🔍  Search", type="primary", use_container_width=True)
with b2:
    reset_clicked = st.button("Reset", use_container_width=True)

# ==============================================================================
# SEARCH LOGIC
# ==============================================================================
def run_search(user, query, ba, ct, status, inv, entity, tid, ft):
    results = []
    for doc in MOCK_DOCUMENTS:
        if doc["STATE"] != user["state"]:
            continue
        entitled = user["entitled_business_areas"]
        if ba:
            if doc["BUSINESS_AREA"] != ba:
                continue
        else:
            if doc["BUSINESS_AREA"] not in entitled:
                continue
        if ct and doc["CASE_TYPE"] != ct:
            continue
        if status and doc["CASE_STATUS"] != status:
            continue
        if inv and inv.lower() not in doc["INVESTIGATOR"].lower():
            continue
        if entity and entity.lower() not in doc["ENTITY_NAME"].lower():
            continue
        if tid and tid not in doc["TRACKING_ID"]:
            continue
        if ft and doc["DOC_TYPE"] != ft:
            continue

        snippet = doc["CHUNK_TEXT"]
        if query and len(query) >= 3:
            hit = False
            for term in query.lower().split():
                if term in snippet.lower() or term in doc["FILE_NAME"].lower():
                    hit = True
                    # highlight
                    for word in snippet.split():
                        if term in word.lower():
                            snippet = snippet.replace(word, f"<mark>{word}</mark>")
            if not hit:
                continue

        results.append({**doc, "SNIPPET": snippet})
    return results

# ==============================================================================
# VALIDATION + SEARCH EXECUTION
# ==============================================================================
if search_clicked:
    errors = []
    if not business_area:
        errors.append("Business Area is required.")
    if not search_query or len(search_query.strip()) < 3:
        errors.append("Search Document Contents is required (minimum 3 characters).")
    if errors:
        for e in errors:
            st.error(e)
    else:
        results = run_search(
            user_info, search_query, business_area,
            case_type, case_status, investigator,
            entity_name, tracking_id, file_type
        )
        st.session_state.search_results = results
        st.session_state.search_query_used = search_query

if reset_clicked:
    st.session_state.search_results = None
    st.session_state.search_query_used = ""
    st.rerun()

# ==============================================================================
# RESULTS
# ==============================================================================
if st.session_state.search_results is not None:
    results = st.session_state.search_results
    query_used = st.session_state.search_query_used

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Results header row
    rh1, rh2, rh3 = st.columns([4, 1, 1])
    with rh1:
        st.markdown(f"""
        <div style="font-size:17px;font-weight:500;color:#3f51b5;padding:4px 0;">
            Search Results
            <span style="font-weight:300;color:#888;font-size:14px;margin-left:8px;">({len(results)} results)</span>
        </div>
        """, unsafe_allow_html=True)
    with rh2:
        st.button("⬇ Export to Excel", use_container_width=True)
    with rh3:
        show_col_picker = st.button("⚙ Columns", use_container_width=True)

    if not results:
        st.info("No documents match your search criteria or access entitlements.")
    else:
        # Column picker inline
        if show_col_picker:
            st.session_state.col_picker_open = not st.session_state.get("col_picker_open", False)

        if st.session_state.get("col_picker_open", False):
            with st.container():
                st.markdown("**Customize Columns** — Attachment ID and Tracking ID are always visible.")
                cp1, cp2, cp3, cp4 = st.columns(4)
                with cp1:
                    st.session_state.show_col_case_type = st.checkbox("Case Type", value=st.session_state.show_col_case_type)
                with cp2:
                    st.session_state.show_col_investigator = st.checkbox("Investigator", value=st.session_state.show_col_investigator)
                with cp3:
                    st.session_state.show_col_status = st.checkbox("Status", value=st.session_state.show_col_status)
                with cp4:
                    st.session_state.show_col_entity = st.checkbox("Entity Name", value=st.session_state.show_col_entity)
                st.markdown("<hr style='border-color:#e0e0e0;margin:8px 0;'>", unsafe_allow_html=True)

        # Build table HTML
        header = """
        <th>Attachment ID</th>
        <th>Tracking ID</th>
        <th>File Name</th>
        <th>Summary</th>
        <th>Upload Date</th>
        <th>Created By</th>
        """
        if st.session_state.show_col_case_type:
            header += "<th>Case Type</th>"
        if st.session_state.show_col_investigator:
            header += "<th>Investigator</th>"
        if st.session_state.show_col_status:
            header += "<th>Status</th>"
        if st.session_state.show_col_entity:
            header += "<th>Entity Name</th>"
        header += "<th>Actions</th>"

        rows_html = ""
        for doc in results:
            entity_display = doc["ENTITY_NAME"] if user_info["sees_unmasked_pii"] else doc["ENTITY_NAME_MASKED"]
            lock_html = " 🔒" if doc["LOCKED"] else ""
            dl_html = "⬇ Download" if user_info["can_download"] else '<span class="sdp-dl-denied">🚫 Restricted</span>'

            row = f"""
            <tr>
                <td>{doc['ATTACHMENT_ID']}</td>
                <td><a class="sdp-trk-link" href="#">{doc['TRACKING_ID']}</a></td>
                <td style="white-space:nowrap;">{doc['FILE_NAME']}{lock_html}</td>
                <td><span class="sdp-snippet">&ldquo;{doc['SNIPPET']}&rdquo;</span></td>
                <td style="white-space:nowrap;">{doc['UPLOAD_DATE']}</td>
                <td>{doc['CREATED_BY']}</td>
            """
            if st.session_state.show_col_case_type:
                row += f"<td>{doc['CASE_TYPE']}</td>"
            if st.session_state.show_col_investigator:
                row += f"<td>{doc['INVESTIGATOR']}</td>"
            if st.session_state.show_col_status:
                row += f"<td>{doc['CASE_STATUS']}</td>"
            if st.session_state.show_col_entity:
                row += f"<td>{entity_display}</td>"
            row += f"<td>{dl_html}</td></tr>"
            rows_html += row

        table_html = f"""
        <div class="sdp-table-wrap">
            <table class="sdp-table">
                <thead><tr>{header}</tr></thead>
                <tbody>{rows_html}</tbody>
            </table>
            <div class="sdp-pagination">
                <span>Showing 1–{len(results)} of {len(results)} results</span>
                <span>Rows per page: 10</span>
            </div>
        </div>
        """
        st.markdown(table_html, unsafe_allow_html=True)

        # ── ABAC Debug Inspector ──
        with st.expander("🛠 Governance Debug Inspector"):
            tab1, tab2 = st.tabs(["Cortex Search Payload", "ABAC Audit Trace"])
            with tab1:
                st.caption("Spring Boot constructs this payload — the browser never sends it directly.")
                st.json({
                    "query": query_used,
                    "columns": ["DOC_ID", "ATTACHMENT_ID", "TRACKING_ID", "FILE_NAME", "CHUNK_TEXT"],
                    "filter": {
                        "@and": [
                            {"@eq": {"DOC_STATE": user_info["state"]}},
                            {"@eq": {"BUSINESS_AREA": business_area or f"(entitled: {user_info['entitled_business_areas']})"}}
                        ]
                    },
                    "limit": 10
                })
            with tab2:
                st.json({
                    "user": user_info["username"],
                    "role": user_info["role"],
                    "enforced_state": user_info["state"],
                    "entitled_business_areas": user_info["entitled_business_areas"],
                    "pii_unmasked": user_info["sees_unmasked_pii"],
                    "download_allowed": user_info["can_download"],
                    "documents_evaluated": len(MOCK_DOCUMENTS),
                    "documents_matched": len(results),
                    "documents_excluded_by_state_abac": len([d for d in MOCK_DOCUMENTS if d["STATE"] != user_info["state"]]),
                })



