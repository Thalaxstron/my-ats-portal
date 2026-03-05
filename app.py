import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG & ADVANCED UI STYLING ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* 1. Remove Top Black Bars & Extra Gaps */
    header[data-testid="stHeader"] { background: transparent !important; height: 0px; }
    .main .block-container { padding-top: 0.5rem !important; }
    
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e) !important;
        background-attachment: fixed;
    }

    /* 2. Header Freeze Concept */
    [data-testid="stVerticalBlock"] > div:nth-child(5) {
        position: sticky;
        top: 0;
        z-index: 999;
        background: #1a1a2e;
        padding: 5px 0;
    }

    /* 3. Dropdown Visibility Fix (Correction #1 & #2) */
    /* Targetting the selectbox and the text inside it after selection */
    div[data-baseweb="select"] > div {
        background-color: white !important;
        border-radius: 5px !important;
    }
    
    /* This ensures the selected text is visible (Dark Blue) against the white background */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] span, 
    div[data-testid="stSelectbox"] input {
        color: #00008b !important;
        font-weight: bold !important;
        -webkit-text-fill-color: #00008b !important;
    }

    /* Targetting the dropdown list items */
    div[role="listbox"] div {
        color: #00008b !important;
        font-weight: bold !important;
    }

    /* Standard inputs and textareas */
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div {
        background-color: white !important;
        border-radius: 5px !important;
    }
    input, textarea { color: #00008b !important; font-weight: bold !important; }

    /* 4. Text Visibility Fix */
    label p, .stMarkdown p, .stWrite { color: white !important; font-weight: 500 !important; }
    [data-testid="stText"], .stMarkdown { color: white !important; }

    /* 5. Button Styling */
    .stButton > button {
        background-color: #FF0000 !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: 1px solid white !important;
    }
    
    /* 6. Header Box Styling */
    .header-box {
        color: #00BFFF !important;
        font-size: 11px !important;
        font-weight: bold;
        text-align: center;
        border-bottom: 2px solid #555;
        padding: 5px 0;
        line-height: 1.2;
    }

    .row-text {
        color: white !important;
        font-size: 13px;
        text-align: center;
        padding: 5px 0;
    }
    
    .slogan { color: #FFD700 !important; font-size: 18px; font-weight: bold; margin-top: -10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION ---
@st.cache_resource
def get_gsheet_client():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        return authorize(creds)
    except Exception as e:
        st.error(f"Database Error: {e}"); return None

client = get_gsheet_client()
if client:
    sh = client.open("ATS_Cloud_Database")
    user_sheet = sh.worksheet("User_Master")
    client_sheet = sh.worksheet("Client_Master")
    cand_sheet = sh.worksheet("ATS_Data")

def get_next_ref_id():
    ids = cand_sheet.col_values(1)
    if len(ids) <= 1: return "E00001"
    nums = [int(i[1:]) for i in ids[1:] if i.startswith("E") and i[1:].isdigit()]
    return f"E{max(nums)+1:05d}" if nums else "E00001"

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. LOGIN PAGE ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: white;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    _, col_m, _ = st.columns([1, 1.2, 1])
    with col_m:
        st.markdown("<div style='background: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px;'>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Email ID")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("ATS LOGIN", use_container_width=True):
                udf = pd.DataFrame(user_sheet.get_all_records())
                match = udf[(udf['Mail_ID'] == u) & (udf['Password'].astype(str) == p)]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Invalid Credentials")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 4. MAIN DASHBOARD ---
else:
    u = st.session_state.user_data
    
    # Header Section
    h1, h2, h3 = st.columns([2, 1.5, 0.5])
    with h1:
        st.markdown("<h2 style='color: white; margin:0;'>Takecare Manpower Service Pvt Ltd</h2>", unsafe_allow_html=True)
        st.markdown("<p class='slogan'>Successful HR Firm</p>", unsafe_allow_html=True)
    with h2:
        st.markdown(f"<p style='color: white; font-size: 18px; margin-bottom:0;'>Welcome, <b>{u['Username']}</b></p>", unsafe_allow_html=True)
        st.markdown("<p style='color: #00FF00; font-size:13px;'>Target: 80+ Calls / 3-5 Interview / 1+ Joining</p>", unsafe_allow_html=True)
    with h3:
        if st.button("Logout"): st.session_state.logged_in = False; st.rerun()

    # Action Row
    b1, b2, b3, b_search = st.columns([0.8, 0.8, 1.2, 2.5])
    
    @st.dialog("➕ New Candidate Shortlist")
    def add_shortlist():
        rid = get_next_ref_id()
        st.markdown(f"<p style='color:black;'><b>Ref ID:</b> {rid} | <b>Date:</b> {datetime.now().strftime('%d-%m-%Y')}</p>", unsafe_allow_html=True)
        cm = pd.DataFrame(client_sheet.get_all_records())
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Candidate Name")
            phone = st.text_input("Phone Number")
            # Selectbox correction #1
            cl_name = st.selectbox("Client", ["--Select--"] + sorted(cm['Client Name'].unique().tolist()))
        with c2:
            plist = cm[cm['Client Name'] == cl_name]['Position'].tolist() if cl_name != "--Select--" else []
            pos = st.selectbox("Position", plist)
            c_date = st.date_input("Commitment Date")
        
        feed = st.text_area("Initial Feedback")
        if st.button("SAVE CANDIDATE", use_container_width=True):
            if name and phone and cl_name != "--Select--":
                row = [rid, datetime.now().strftime('%d-%m-%Y'), name, phone, cl_name, pos, c_date.strftime('%d-%m-%Y'), "Shortlisted", u['Username'], "", "", feed]
                cand_sheet.append_row(row)
                st.success("Saved!"); st.rerun()

    @st.dialog("📝 Update Candidate Status")
    def edit_candidate(row):
        st.markdown(f"<p style='color:black;'>Editing: <b>{row['Candidate Name']}</b></p>", unsafe_allow_html=True)
        st_list = ["Shortlisted", "Interviewed", "Selected", "Rejected", "Onboarded", "Hold", "Left"]
        # Selectbox correction #2
        curr_status = row.get('Status', 'Shortlisted')
        idx_status = st_list.index(curr_status) if curr_status in st_list else 0
        new_st = st.selectbox("Update Status", st_list, index=idx_status)
        new_fb = st.text_input("Feedback", value=row.get('Feedback', ''))
        evt_date = st.date_input("Update Date (Interview/Onboard)")
        
        if st.button("UPDATE DATA", use_container_width=True):
            idx = cand_sheet.find(row['Reference_ID']).row
            cand_sheet.update_cell(idx, 8, new_st)
            cand_sheet.update_cell(idx, 12, new_fb)
            
            if new_st == "Interviewed":
                cand_sheet.update_cell(idx, 7, evt_date.strftime('%d-%m-%Y'))
            
            if new_st == "Onboarded":
                cand_sheet.update_cell(idx, 10, evt_date.strftime('%d-%m-%Y'))
                cm = pd.DataFrame(client_sheet.get_all_records())
                days_list = cm[cm['Client Name'] == row['Client Name']]['SR Days'].values
                days = int(days_list[0]) if len(days_list) > 0 else 0
                sr_dt = (evt_date + timedelta(days=days)).strftime('%d-%m-%Y')
                cand_sheet.update_cell(idx, 11, sr_dt)
            st.rerun()

    with b1: st.button("🔍 Search")
    with b2: 
        if u['Role'] in ['ADMIN', 'TL']: st.button("⚡ Filter")
    with b3:
        if st.button("➕ New Shortlist"): add_shortlist()
    with b_search:
        find = st.text_input("Search", label_visibility="collapsed", placeholder="Search Ref ID, Candidate Name...")

    # --- 5. DATA TABLE (Correction #3: Column Names & Data Mapping) ---
    st.markdown("---")
    cols = st.columns([0.8, 1.2, 1, 1, 1.2, 1.2, 0.8, 1, 1, 0.8, 0.5, 0.5])
    titles = ["Ref ID", "Candidate", "Contact", "Client Name", "Position / Job", "Comm / Int Date", "Status", "Onboard Date", "SR Date", "HR Name", "Edit", "WA"]
    for c, t in zip(cols, titles): c.markdown(f"<div class='header-box'>{t}</div>", unsafe_allow_html=True)
    
    # Load and Clean Data
    raw_data = cand_sheet.get_all_records()
    data = pd.DataFrame(raw_data)
    # Important: Remove hidden spaces from column names to ensure mapping works
    data.columns = [c.strip() for c in data.columns] 
    data = data.iloc[::-1] 
    
    if u['Role'] == "RECRUITER": data = data[data['HR Name'] == u['Username']]
    if find: data = data[data.astype(str).apply(lambda x: x.str.contains(find, case=False)).any(axis=1)]

    # Display Rows (Correction #3: Data Mapping)
    for _, r in data.iterrows():
        r_cols = st.columns([0.8, 1.2, 1, 1, 1.2, 1.2, 0.8, 1, 1, 0.8, 0.5, 0.5])
        r_cols[0].markdown(f"<div class='row-text'>{r.get('Reference_ID','')}</div>", unsafe_allow_html=True)
        r_cols[1].markdown(f"<div class='row-text'>{r.get('Candidate Name','')}</div>", unsafe_allow_html=True)
        r_cols[2].markdown(f"<div class='row-text'>{r.get('Contact Number','')}</div>", unsafe_allow_html=True)
        r_cols[3].markdown(f"<div class='row-text'>{r.get('Client Name','')}</div>", unsafe_allow_html=True)
        r_cols[4].markdown(f"<div class='row-text'>{r.get('Job Title','')}</div>", unsafe_allow_html=True)
        
        # Commitment / Interview Date (Column 7 in Sheets)
        r_cols[5].markdown(f"<div class='row-text'>{r.get('Commitment Date','')}</div>", unsafe_allow_html=True)
        
        r_cols[6].markdown(f"<div class='row-text'>{r.get('Status','')}</div>", unsafe_allow_html=True)
        
        # Onboarded Date (Column 10 in Sheets)
        r_cols[7].markdown(f"<div class='row-text'>{r.get('Onboarded Date','')}</div>", unsafe_allow_html=True)
        
        r_cols[8].markdown(f"<div class='row-text'>{r.get('SR Date','')}</div>", unsafe_allow_html=True)
        r_cols[9].markdown(f"<div class='row-text'>{r.get('HR Name','')}</div>", unsafe_allow_html=True)
        
        if r_cols[10].button("📝", key=f"e_{r['Reference_ID']}"): edit_candidate(r)
        
        if r_cols[11].button("📲", key=f"w_{r['Reference_ID']}"):
            msg = f"Hi {r['Candidate Name']}, you are shortlisted for {r['Job Title']} at {r['Client Name']}."
            st.link_button("WA", f"https://wa.me/91{r['Contact Number']}?text={urllib.parse.quote(msg)}")
