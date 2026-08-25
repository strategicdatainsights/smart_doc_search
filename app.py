import streamlit as st
import pandas as pd
from datetime import datetime, date

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
# WIREFRAME-MATCHED CSS
# ==============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
@import url('https://fonts.googleapis.com/icon?family=Material+Icons');

* { font-family: 'Roboto', sans-serif !important; }

/* Nav bar */
.nav-bar {
    background: #3f51b5;
    color: white;
    padding: 12px 24px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    margin: -1rem -1rem 1.5rem -1rem;
    border-radius: 0;
}
.nav-bar h1 { font-size: 18px; font-weight: 500; color: white; margin: 0; }

/* Legend */
.legend {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 14px 20px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 24px;
    font-size: 13px;
}
.required-star { color: #f44336; font-weight: bold; }
.smart-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 11px;
    color: #7c4dff;
    background: #ede7f6;
    padding: 2px 8px;
    border-radius: 12px;
    font-weight: 500;
    margin-left: 4px;
}

/* Cards */
.card {
    background: white;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    margin-bottom: 24px;
    overflow: hidden;
}
.card-header {
    padding: 14px 20px;
    border-bottom: 1px solid #e0e0e0;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.card-header h2 { font-size: 17px; font-weight: 500; color: #3f51b5; margin: 0; }

/* Chip container */
.chip-container {
    padding: 10px 16px;
    background: #f9f9f9;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
    margin-bottom: 12px;
}
.chip-label { font-size: 12px; color: #666; font-weight: 500; }
.chip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #e8eaf6;
    color: #3f51b5;
    padding: 4px 12px;
    border-radius: 16px;
    font-size: 12px;
    font-weight: 500;
}

/* Results table */
.results-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}
.results-table thead { background: #fafafa; }
.results-table th {
    padding: 12px 16px;
    text-align: left;
    font-weight: 500;
    color: #666;
    border-bottom: 2px solid #e0e0e0;
    white-space: nowrap;
}
.results-table td {
    padding: 12px 16px;
    border-bottom: 1px solid #f0f0f0;
    vertical-align: middle;
}
.results-table tr:hover { background: #f5f5f5; }
.link { color: #3f51b5; font-weight: 500; text-decoration: none; }
.snippet { font-style: italic; color: #555; }
.snippet mark { background: #fff59d; padding: 0 2px; border-radius: 2px; }
.lock-icon { color: #f57c00; font-size: 14px; vertical-align: middle; margin-left: 4px; }

/* Pagination */
.pagination-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 16px;
    border-top: 1px solid #e0e0e0;
    background: #fafafa;
    font-size: 13px;
    color: #666;
}

/* User persona badge */
.persona-badge {
    background: rgba(255,255,255,0.15);
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 12px;
    color: white;
}

/* Form labels */
.field-label {
    font-size: 12px;
    font-weight: 500;
    color: #555;
    margin-bottom: 2px;
}
.field-hint {
    font-size: 11px;
    color: #999;
    font-style: italic;
    margin-top: 2px;
}

/* Streamlit overrides */
div[data-testid="stExpander"] {
    border: 1px solid #e0e0e0 !important;
    border-radius: 4px !important;
    margin-bottom: 1px !important;
}
div[data-testid="stExpander"] summary {
    padding: 12px 16px !important;
    background: #fafafa !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}
.stButton > button {
    font-family: 'Roboto', sans-serif !important;
    font-weight: 500 !important;
    border-radius: 4px !important;
}
.stButton > button[kind="primary"] {
    background: #3f51b5 !important;
    color: white !important;
}
.stSelectbox label, .stTextInput label, .stTextArea label,
.stDateInput label, .stMultiSelect label {
    font-size: 12px !important;
    font-weight: 500 !important;
    color: #555 !important;
}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# MOCK DATA
# ==============================================================================
MOCK_USERS = {
    "Regulator — RI (State Regulator, Full Access)": {
        "username": "elizabeth.rosso@regulator.ri.gov",
        "role": "STATE_REGULATOR",
        "state": "RI",
        "entitled_business_areas": ["Market Regulation", "Complaints", "Exams"],
        "can_download": True,
        "sees_unmasked_pii": True,
    },
    "Analyst — RI (Financial Exams, Masked)": {
        "username": "j.smith@state.ri.gov",
        "role": "FINANCIAL_ANALYST",
        "state": "RI",
        "entitled_business_areas": ["Exams"],
        "can_download": True,
        "sees_unmasked_pii": False,
    },
    "Analyst — MA (Financial Exams, No Download)": {
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
        "CHUNK_TEXT": "In regards to the accident that occurred on the evening of December 19th...",
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
        "CHUNK_TEXT": "In regards to the accident that occurred on Monday, the policyholder submitted a formal complaint.",
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
        "CHUNK_TEXT": "Details of accident damage assessment from third party inspector retained by Cornwall.",
        "DOC_TYPE": ".docx",
    },
]

# ==============================================================================
# NAV BAR
# ==============================================================================
if "selected_user" not in st.session_state:
    st.session_state.selected_user = list(MOCK_USERS.keys())[0]

user_info = MOCK_USERS[st.session_state.selected_user]

st.markdown(f"""
<div class="nav-bar">
    <h1>Smart Document Platform — Search</h1>
    <span class="persona-badge">👤 {user_info['username']} &nbsp;|&nbsp; {user_info['state']} &nbsp;|&nbsp; {user_info['role']}</span>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# USER PERSONA SWITCHER (inline, not sidebar)
# ==============================================================================
with st.container():
    pcol1, pcol2 = st.columns([3, 1])
    with pcol2:
        selected_user = st.selectbox(
            "Active Persona (Demo)",
            list(MOCK_USERS.keys()),
            index=list(MOCK_USERS.keys()).index(st.session_state.selected_user),
            key="persona_switcher",
            label_visibility="collapsed"
        )
        if selected_user != st.session_state.selected_user:
            st.session_state.selected_user = selected_user
            st.rerun()

user_info = MOCK_USERS[st.session_state.selected_user]

# ==============================================================================
# LEGEND
# ==============================================================================
st.markdown("""
<div class="legend">
    <div><span class="required-star">*</span> &nbsp;Required Field</div>
    <div><span class="smart-badge">✦ Smart</span> &nbsp;AI-powered search (Snowflake Cortex)</div>
    <div><span style="color:#f57c00;">🔒</span> &nbsp;Locked document</div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# SEARCH CRITERIA CARD
# ==============================================================================
st.markdown('<div class="card"><div class="card-header"><h2>Search Criteria</h2></div></div>', unsafe_allow_html=True)

with st.container():
    # Required fields
    col_ba, _ = st.columns([1, 2])
    with col_ba:
        st.markdown('<div class="field-label">Business Area <span class="required-star">*</span></div>', unsafe_allow_html=True)
        business_area = st.selectbox(
            "Business Area",
            [""] + user_info["entitled_business_areas"],
            format_func=lambda x: "-- Select Business Area --" if x == "" else x,
            label_visibility="collapsed"
        )

    st.markdown('<div class="field-label">Search Document Contents <span class="required-star">*</span> <span class="smart-badge">✦ Smart</span></div>', unsafe_allow_html=True)
    search_query = st.text_area(
        "Search Document Contents",
        placeholder="Enter search terms to find within document text...",
        height=100,
        label_visibility="collapsed"
    )
    st.markdown('<div class="field-hint">Search within the text of all attached documents.</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Accordion sections
    with st.expander("Case Details", expanded=True):
        cd1, cd2 = st.columns(2)
        with cd1:
            st.markdown('<div class="field-label">Case Type</div>', unsafe_allow_html=True)
            case_type = st.selectbox("Case Type", ["", "Complaints", "Enforcement", "Market Conduct Exams"], format_func=lambda x: "-- Select --" if x == "" else x, label_visibility="collapsed")
        with cd2:
            st.markdown('<div class="field-label">Tracking ID</div>', unsafe_allow_html=True)
            tracking_id = st.text_input("Tracking ID", placeholder="e.g., 12345", label_visibility="collapsed")
        cd3, cd4 = st.columns(2)
        with cd3:
            st.markdown('<div class="field-label">Investigator <span class="smart-badge">✦ Smart</span></div>', unsafe_allow_html=True)
            investigator = st.text_input("Investigator", placeholder="Search by investigator name", label_visibility="collapsed")
            st.markdown('<div class="field-hint">Searches Primary and Secondary investigators.</div>', unsafe_allow_html=True)
        with cd4:
            st.markdown('<div class="field-label">Status</div>', unsafe_allow_html=True)
            case_status = st.selectbox("Status", ["", "Open", "Closed", "Under Review", "Pending"], format_func=lambda x: "-- Select --" if x == "" else x, label_visibility="collapsed")

    with st.expander("Entity"):
        e1, e2 = st.columns(2)
        with e1:
            st.markdown('<div class="field-label">Entity Name <span class="smart-badge">✦ Smart</span></div>', unsafe_allow_html=True)
            entity_name = st.text_input("Entity Name", placeholder="Search by person or company name", label_visibility="collapsed")
            st.markdown('<div class="field-hint">Handles partial names, company names, or combinations.</div>', unsafe_allow_html=True)
        with e2:
            st.markdown('<div class="field-label">NAIC Group Number</div>', unsafe_allow_html=True)
            naic_group = st.selectbox("NAIC Group Number", ["", "9083 - 21st Century Company", "8056 - 53rd Order of Insurance"], format_func=lambda x: "-- Select --" if x == "" else x, label_visibility="collapsed")

    with st.expander("Dates"):
        da1, da2 = st.columns(2)
        with da1:
            st.markdown('<div class="field-label">Case Initiated</div>', unsafe_allow_html=True)
            ci1, ci2 = st.columns(2)
            with ci1:
                case_init_from = st.date_input("Case Initiated From", value=None, label_visibility="collapsed")
            with ci2:
                case_init_to = st.date_input("Case Initiated To", value=None, label_visibility="collapsed")
        with da2:
            st.markdown('<div class="field-label">Case Opened</div>', unsafe_allow_html=True)
            co1, co2 = st.columns(2)
            with co1:
                case_open_from = st.date_input("Case Opened From", value=None, label_visibility="collapsed")
            with co2:
                case_open_to = st.date_input("Case Opened To", value=None, label_visibility="collapsed")
        da3, da4 = st.columns(2)
        with da3:
            st.markdown('<div class="field-label">Case Closed</div>', unsafe_allow_html=True)
            cc1, cc2 = st.columns(2)
            with cc1:
                case_close_from = st.date_input("Case Closed From", value=None, label_visibility="collapsed")
            with cc2:
                case_close_to = st.date_input("Case Closed To", value=None, label_visibility="collapsed")
        with da4:
            st.markdown('<div class="field-label">File Upload</div>', unsafe_allow_html=True)
            fu1, fu2 = st.columns(2)
            with fu1:
                file_upload_from = st.date_input("File Upload From", value=None, label_visibility="collapsed")
            with fu2:
                file_upload_to = st.date_input("File Upload To", value=None, label_visibility="collapsed")

    with st.expander("Document"):
        doc1, doc2 = st.columns(2)
        with doc1:
            st.markdown('<div class="field-label">Document Name <span class="smart-badge">✦ Smart</span></div>', unsafe_allow_html=True)
            doc_name = st.text_input("Document Name", placeholder="e.g., accident report, policy letter", label_visibility="collapsed")
        with doc2:
            st.markdown('<div class="field-label">File Type</div>', unsafe_allow_html=True)
            file_type = st.selectbox("File Type", ["", ".pdf", ".docx / .doc", ".xlsx", ".msg", ".ppt", ".csv"], format_func=lambda x: "-- Select --" if x == "" else x, label_visibility="collapsed")

    with st.expander("Additional Details"):
        ad1, ad2, ad3 = st.columns(3)
        with ad1:
            st.markdown('<div class="field-label">Case Sub-Type</div>', unsafe_allow_html=True)
            case_subtype = st.selectbox("Case Sub-Type", ["", "Administrative Report", "Franchise", "Inquiry", "Investigations", "Market Conduct", "Multi-State", "PBM", "Securities"], format_func=lambda x: "-- Select --" if x == "" else x, label_visibility="collapsed")
        with ad2:
            st.markdown('<div class="field-label">State Keyword</div>', unsafe_allow_html=True)
            state_keyword = st.multiselect("State Keyword", ["COVID-19", "Data Breach", "Fires Summer 2023", "Hurricane", "Pet Insurance", "Tornado"], label_visibility="collapsed")
        with ad3:
            st.markdown('<div class="field-label">Reason</div>', unsafe_allow_html=True)
            reason = st.selectbox("Reason", ["", "Reason 1", "Reason 2", "Reason 3"], format_func=lambda x: "-- Select --" if x == "" else x, label_visibility="collapsed")
        ad4, ad5 = st.columns(2)
        with ad4:
            st.markdown('<div class="field-label">Line of Insurance <span class="smart-badge">✦ Smart</span></div>', unsafe_allow_html=True)
            loi = st.text_input("Line of Insurance", placeholder="e.g., property, casualty, auto", label_visibility="collapsed")
            st.markdown('<div class="field-hint">Searches Coverage Type, Line of Insurance, Line of Business, and RIRS Line of Business.</div>', unsafe_allow_html=True)
        with ad5:
            st.markdown('<div class="field-label">Disposition <span class="smart-badge">✦ Smart</span></div>', unsafe_allow_html=True)
            disposition = st.text_input("Disposition", placeholder="e.g., settled, dismissed", label_visibility="collapsed")

# Active filter chips
active_chips = []
if business_area:
    active_chips.append(f"Business Area: {business_area}")
if case_type:
    active_chips.append(f"Case Type: {case_type}")
if search_query:
    active_chips.append(f"Contents: \"{search_query[:30]}{'...' if len(search_query) > 30 else ''}\"")
if investigator:
    active_chips.append(f"Investigator: {investigator}")
if entity_name:
    active_chips.append(f"Entity: {entity_name}")
if case_status:
    active_chips.append(f"Status: {case_status}")
if tracking_id:
    active_chips.append(f"Tracking ID: {tracking_id}")

if active_chips:
    chips_html = '<div class="chip-container"><span class="chip-label">Active Filters:</span>'
    for chip in active_chips:
        chips_html += f'<span class="chip">{chip}</span>'
    chips_html += '</div>'
    st.markdown(chips_html, unsafe_allow_html=True)

# Search / Reset buttons
bcol1, bcol2, bcol3 = st.columns([1, 1, 6])
with bcol1:
    search_clicked = st.button("🔍 Search", type="primary", use_container_width=True)
with bcol2:
    reset_clicked = st.button("Reset", use_container_width=True)

# ==============================================================================
# SEARCH LOGIC
# ==============================================================================
def run_search(user, query, ba, ct, status, inv, entity, tid, ft):
    results = []
    for doc in MOCK_DOCUMENTS:
        # ABAC: state isolation
        if doc["STATE"] != user["state"]:
            continue
        # ABAC: business area entitlement
        if ba and doc["BUSINESS_AREA"] != ba:
            continue
        if ba == "" and doc["BUSINESS_AREA"] not in user["entitled_business_areas"]:
            continue
        # Structured filters
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
        # Semantic search (mock keyword match)
        snippet = doc["CHUNK_TEXT"]
        if query:
            if query.lower() not in snippet.lower() and query.lower() not in doc["FILE_NAME"].lower():
                continue
            # Highlight keyword
            highlighted = snippet.replace(
                query, f"<mark>{query}</mark>"
            ).replace(
                query.lower(), f"<mark>{query.lower()}</mark>"
            ).replace(
                query.capitalize(), f"<mark>{query.capitalize()}</mark>"
            )
        else:
            highlighted = snippet
        results.append({**doc, "SNIPPET": highlighted})
    return results

# ==============================================================================
# RESULTS
# ==============================================================================
if search_clicked or ("search_results" in st.session_state and st.session_state.search_results is not None):

    if search_clicked:
        if not business_area:
            st.error("Business Area is required.")
            st.stop()
        if not search_query:
            st.error("Search Document Contents is required.")
            st.stop()
        results = run_search(user_info, search_query, business_area, case_type, case_status, investigator, entity_name, tracking_id, file_type)
        st.session_state.search_results = results
        st.session_state.search_query_used = search_query
    else:
        results = st.session_state.get("search_results", [])

    query_used = st.session_state.get("search_query_used", "")

    st.markdown("<br>", unsafe_allow_html=True)

    # Results card header
    rcol1, rcol2 = st.columns([4, 1])
    with rcol1:
        st.markdown(f'<div class="card-header"><h2>Search Results <span style="font-weight:300;color:#666;font-size:14px;">({len(results)} results)</span></h2></div>', unsafe_allow_html=True)
    with rcol2:
        st.button("⬇ Export to Excel", use_container_width=True)

    if not results:
        st.info("No documents match your search criteria or entitlements.")
    else:
        # Column picker state
        if "show_cols" not in st.session_state:
            st.session_state.show_cols = {
                "File Name": True, "Summary": True, "Upload Date": True, "Created By": True,
                "Case Type": False, "Investigator": False, "Status": False, "Entity Name": False,
            }

        # Build table
        table_rows = ""
        for doc in results:
            entity_display = doc["ENTITY_NAME"] if user_info["sees_unmasked_pii"] else doc["ENTITY_NAME_MASKED"]
            locked_icon = ' <span class="lock-icon">🔒</span>' if doc["LOCKED"] else ""
            snippet_cell = f'<span class="snippet">&ldquo;{doc["SNIPPET"]}&rdquo;</span>'

            row = f"""
            <tr>
                <td>{doc['ATTACHMENT_ID']}</td>
                <td><a class="link" href="#">{doc['TRACKING_ID']}</a></td>
            """
            if st.session_state.show_cols.get("File Name"):
                row += f"<td>{doc['FILE_NAME']}{locked_icon}</td>"
            if st.session_state.show_cols.get("Summary"):
                row += f"<td style='max-width:380px;'>{snippet_cell}</td>"
            if st.session_state.show_cols.get("Upload Date"):
                row += f"<td style='white-space:nowrap;'>{doc['UPLOAD_DATE']}</td>"
            if st.session_state.show_cols.get("Created By"):
                row += f"<td>{doc['CREATED_BY']}</td>"
            if st.session_state.show_cols.get("Case Type"):
                row += f"<td>{doc['CASE_TYPE']}</td>"
            if st.session_state.show_cols.get("Investigator"):
                row += f"<td>{doc['INVESTIGATOR']}</td>"
            if st.session_state.show_cols.get("Status"):
                row += f"<td>{doc['CASE_STATUS']}</td>"
            if st.session_state.show_cols.get("Entity Name"):
                row += f"<td>{entity_display}</td>"

            dl_btn = "⬇" if user_info["can_download"] else "🚫"
            row += f"<td><button style='padding:4px 10px;border:1px solid #ccc;border-radius:4px;background:white;cursor:pointer;font-size:12px;'>{dl_btn}</button></td>"
            row += "</tr>"
            table_rows += row

        # Header
        header_cols = '<th>Attachment ID</th><th>Tracking ID</th>'
        for col, visible in st.session_state.show_cols.items():
            if visible:
                header_cols += f"<th>{col}</th>"
        header_cols += "<th>Actions</th>"

        table_html = f"""
        <div style="overflow-x:auto;background:white;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.12);">
            <table class="results-table">
                <thead><tr>{header_cols}</tr></thead>
                <tbody>{table_rows}</tbody>
            </table>
            <div class="pagination-bar">
                <span>Showing 1–{len(results)} of {len(results)} results</span>
                <span>Rows per page: 10 &nbsp;|&nbsp; Page 1</span>
            </div>
        </div>
        """
        st.markdown(table_html, unsafe_allow_html=True)

        # Column picker
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("⚙ Column Picker — Show/Hide Columns"):
            cp_cols = st.columns(4)
            col_keys = list(st.session_state.show_cols.keys())
            for i, col in enumerate(col_keys):
                with cp_cols[i % 4]:
                    st.session_state.show_cols[col] = st.checkbox(
                        col,
                        value=st.session_state.show_cols[col],
                        key=f"col_{col}"
                    )

        # ABAC debug inspector
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("🛠 Governance Debug Inspector — ABAC Audit Log"):
            st.markdown("**Cortex Search Payload (Spring Boot constructs this — browser never sees it)**")
            st.json({
                "query": query_used,
                "columns": ["DOC_ID", "ATTACHMENT_ID", "TRACKING_ID", "FILE_NAME", "CHUNK_TEXT"],
                "filter": {
                    "@and": [
                        {"@eq": {"DOC_STATE": user_info["state"]}},
                        {"@eq": {"BUSINESS_AREA": business_area or f"[user entitled: {user_info['entitled_business_areas']}]"}}
                    ]
                },
                "limit": 10
            })
            st.markdown("**ABAC Evaluation**")
            st.json({
                "user": user_info["username"],
                "role": user_info["role"],
                "enforced_state": user_info["state"],
                "entitled_business_areas": user_info["entitled_business_areas"],
                "pii_unmasked": user_info["sees_unmasked_pii"],
                "download_allowed": user_info["can_download"],
                "documents_evaluated": len(MOCK_DOCUMENTS),
                "documents_matched": len(results),
                "documents_excluded_by_abac": len(MOCK_DOCUMENTS) - len(results),
            })

if reset_clicked:
    st.session_state.search_results = None
    st.rerun()
