import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse

# --- 1. PAGE CONFIG & UI FIX ---
st.set_page_config(page_title="Takecare ATS", layout="wide", initial_sidebar_state="collapsed")

# Intha CSS thaan neenga screenshot-la kaattuna alignment-ai fix pannum
st.markdown("""
<style>
    header {visibility: hidden;} /* Top black bar removal */
    .stApp { background: linear-gradient(135deg, #d32f2f, #0d47a1); background-attachment: fixed; }

    /* Fixed Header (215px) */
    .header-box {
        position: fixed; top: 0; left: 0; width: 100%; height: 215px;
        background: linear-gradient(135deg, #d32f2f, #0d47a1);
        z-index: 1000; padding: 20px 40px; border-bottom: 2px solid white;
        color: white;
    }

    /* Floating Controls Container (Logout, Search, etc.) */
    .floating-controls {
        position: fixed; top: 15px; right: 40px; z-index: 2000;
        width: 250px; display: flex; flex-direction: column; gap: 8px;
    }

    /* Sticky Table Header (45px) */
    .table-header-bar {
        position: fixed; top: 215px; left: 0; width: 100%; height: 45px;
        background-color: #0d47a1; z-index: 999; border-bottom: 1px solid white;
        display: flex; align-items: center; padding: 0 10px;
    }

    /* Content Area Scrollable */
    .main-body { margin-top: 265px; padding: 10px; }

    /* Login Page Checkbox Color Fix */
    div[data-baseweb="checkbox"] span { color: white !important; font-weight: bold; }
    
    /* Alignment for labels in columns */
    .header-label { color: white; font-weight: bold; text-align: center; font-size: 14px; }
    .row-data { color: white; text-align: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.2); }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE (Simplified) ---
def connect_db():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
           scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return authorize(creds)

gc = connect_db()
sh = gc.open("ATS_Cloud_Database")
data_sh = sh.worksheet("ATS_Data")
user_sh = sh.worksheet("User_Master")
client_sh = sh.worksheet("Client_Master")

# --- 3. SESSION & LOGIN ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align:center; color:white; margin-top:80px;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:white;'>ATS LOGIN</h3>", unsafe_allow_html=True)
    _, login_box, _ = st.columns([1, 1, 1])
    with login_box:
        with st.container(border=True):
            e = st.text_input("Email ID")
            p = st.text_input("Password", type="password")
            st.checkbox("Remember Me") # CSS will make this white
            if st.button("LOGIN", use_container_width=True, type="primary"):
                users = pd.DataFrame(user_sh.get_all_records())
                match = users[(users['Mail_ID']==e) & (users['Password'].astype(str)==p)]
                if not match.empty:
                    st.session_state.auth = True
                    st.session_state.user = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Access Denied")
else:
    # --- 4. DASHBOARD HEADER ---
    u = st.session_state.user
    
    # Left Content
    st.markdown(f"""
    <div class="header-box">
        <h1 style="margin:0; font-size:32px;">Takecare Manpower Service Pvt Ltd</h1>
        <h4 style="margin:0; opacity:0.9;">Successful HR Firm</h4>
        <p style="margin:10px 0 5px 0; font-size:18px;">Welcome back, {u['Username']}!</p>
        <div style="background:white; color:#d32f2f; padding:6px 15px; border-radius:5px; font-weight:bold; display:inline-block;">
            Target: 80+ Calls / 3-5 Interview / 1+ Joining
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Right Side Controls (FIXED POSITION)
    st.markdown('<div class="floating-controls">', unsafe_allow_html=True)
    if st.button("Logout 🚪", key="logout_btn"):
        st.session_state.auth = False
        st.rerun()
    search_query = st.text_input("Search", placeholder="🔍 Search...", label_visibility="collapsed")
    if u['Role'] in ['ADMIN', 'TL']:
        if st.button("Filter ⚙️"): st.session_state.show_filter = True
    if st.button("+ New Shortlist", type="primary"): st.session_state.show_add = True
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 5. STICKY TABLE HEADER ---
    c_widths = [0.7, 1.2, 1.1, 1.4, 1.1, 1.1, 1.1, 1.1, 1.1, 0.4, 0.4]
    labels = ["Ref ID", "Candidate", "Contact", "Position", "Int. Date", "Status", "Joined", "SR Date", "HR Name", "Edit", "WA"]
    
    st.markdown('<div class="table-header-bar">', unsafe_allow_html=True)
    h_cols = st.columns(c_widths)
    for col, lab in zip(h_cols, labels):
        col.markdown(f"<div class='header-label'>{lab}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 6. DATA AREA ---
    st.markdown('<div class="main-body">', unsafe_allow_html=True)
    
    # Logic for New Shortlist Popup
    if "show_add" in st.session_state:
        @st.dialog("Create New Shortlist")
        def add_entry():
            # (All 68 logic points for form go here)
            st.write("New Entry Form")
            if st.button("Close"): del st.session_state.show_add; st.rerun()
        add_entry()

    # Data Fetching & Display
    df = pd.DataFrame(data_sh.get_all_records())
    if u['Role'] == "RECRUITER": df = df[df['HR Name'] == u['Username']]
    if search_query: df = df[df.apply(lambda r: search_query.lower() in str(r).lower(), axis=1)]

    for idx, row in df.iterrows():
        r_cols = st.columns(c_widths)
        r_cols[0].markdown(f"<div class='row-data'>{row['Reference_ID']}</div>", unsafe_allow_html=True)
        r_cols[1].markdown(f"<div class='row-data'>{row['Candidate Name']}</div>", unsafe_allow_html=True)
        r_cols[2].markdown(f"<div class='row-data'>{row['Contact Number']}</div>", unsafe_allow_html=True)
        r_cols[3].markdown(f"<div class='row-data'>{row['Job Title']}</div>", unsafe_allow_html=True)
        r_cols[4].markdown(f"<div class='row-data'>{row['Interview Date']}</div>", unsafe_allow_html=True)
        r_cols[5].markdown(f"<div class='row-data'>{row['Status']}</div>", unsafe_allow_html=True)
        r_cols[6].markdown(f"<div class='row-data'>{row['Joining Date']}</div>", unsafe_allow_html=True)
        r_cols[7].markdown(f"<div class='row-data'>{row['SR Date']}</div>", unsafe_allow_html=True)
        r_cols[8].markdown(f"<div class='row-data'>{row['HR Name']}</div>", unsafe_allow_html=True)
        
        if r_cols[9].button("📝", key=f"ed_{idx}"): pass
        if r_cols[10].button("📲", key=f"wa_{idx}"): pass

    st.markdown('</div>', unsafe_allow_html=True)
