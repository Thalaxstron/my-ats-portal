import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse

# --- 1. FORCE UI ALIGNMENT (Laptop Optimized) ---
st.set_page_config(page_title="Takecare ATS", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    /* 1. Remove All Default Gaps */
    header {visibility: hidden;}
    .block-container {padding: 0rem !important;}
    .stApp { background: linear-gradient(135deg, #d32f2f, #0d47a1); background-attachment: fixed; }

    /* 2. Fixed Header (215px) */
    .header-main {
        position: fixed; top: 0; left: 0; width: 100%; height: 215px;
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%);
        z-index: 1000; padding: 30px 40px; border-bottom: 2px solid white;
        color: white;
    }

    /* 3. RIGHT SIDE CONTROLS (Force Pinned to Top Right) */
    .controls-panel {
        position: fixed; top: 20px; right: 40px; z-index: 2000;
        width: 250px; text-align: right;
    }
    
    /* Button & Input Spacing for Laptop */
    .stButton button { margin-bottom: 8px !important; width: 100% !important; border-radius: 5px !important; font-weight: bold !important;}
    .stTextInput input { margin-bottom: 8px !important; }

    /* 4. STICKY TABLE BAR (45px) */
    .sticky-bar {
        position: fixed; top: 215px; left: 0; width: 100%; height: 45px;
        background-color: #0d47a1; z-index: 999; border-bottom: 1px solid white;
        display: flex; align-items: center; padding: 0 15px;
    }

    /* 5. DATA AREA */
    .content-scroll { margin-top: 260px; padding: 10px 15px; }
    
    /* 6. LOGIN PAGE STYLING */
    div[data-baseweb="checkbox"] span { color: white !important; font-weight: bold; } /* Remember Me White */
    .row-item { color: white; text-align: center; font-size: 14px; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.1); }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION ---
def get_gc():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
               scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return authorize(creds)
    except: return None

gc = get_gc()
sh = gc.open("ATS_Cloud_Database")
data_sh = sh.worksheet("ATS_Data")
user_sh = sh.worksheet("User_Master")
client_sh = sh.worksheet("Client_Master")

# --- 3. LOGIN & SESSION ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<br><br><h1 style='text-align:center; color:white;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:white;'>ATS LOGIN</h3>", unsafe_allow_html=True)
    _, lbox, _ = st.columns([1, 1, 1])
    with lbox:
        with st.container(border=True):
            user_mail = st.text_input("Email ID")
            user_pass = st.text_input("Password", type="password")
            st.checkbox("Remember Me") # Logic point 8: White text via CSS
            if st.button("LOGIN", type="primary", use_container_width=True):
                users = pd.DataFrame(user_sh.get_all_records())
                match = users[(users['Mail_ID']==user_mail) & (users['Password'].astype(str)==user_pass)]
                if not match.empty:
                    st.session_state.auth = True
                    st.session_state.user = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Invalid Credentials")
else:
    # --- 4. HEADER CONTENT (Left Side) ---
    u = st.session_state.user
    st.markdown(f"""
    <div class="header-main">
        <h1 style="margin:0; font-size:35px;">Takecare Manpower Service Pvt Ltd</h1>
        <h4 style="margin:0; opacity:0.9; font-style: italic;">Successful HR Firm</h4>
        <p style="margin:15px 0 5px 0; font-size:20px;">Welcome back, <b>{u['Username']}!</b></p>
        <div style="background:white; color:#d32f2f; padding:8px 20px; border-radius:5px; font-weight:bold; display:inline-block; border: 1px solid #d32f2f;">
            Target for Today: 80+ Calls / 3-5 Interview / 1+ Joining
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- 5. FIXED CONTROLS (Right Side - Force Pinned) ---
    with st.container():
        st.markdown('<div class="controls-panel">', unsafe_allow_html=True)
        if st.button("Logout 🚪", key="exit"):
            st.session_state.auth = False
            st.rerun()
        
        # Search bar without label
        search_txt = st.text_input("Search", placeholder="🔍 Search...", label_visibility="collapsed", key="srch")
        
        # Filter & New in one row for better laptop space
        c1, c2 = st.columns(2)
        with c1:
            if u['Role'] in ['ADMIN', 'TL']:
                if st.button("Filter ⚙️"): pass
        with c2:
            if st.button("+ New", type="primary"): st.session_state.show_add = True
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 6. STICKY TABLE HEADER ---
    # Col widths optimized for Laptop 100% alignment
    cw = [0.7, 1.3, 1.1, 1.5, 1.2, 1.0, 1.0, 1.1, 1.0, 0.5, 0.5]
    cols_labels = ["Ref ID", "Candidate", "Contact", "Position", "Int. Date", "Status", "Joined", "SR Date", "HR Name", "Edit", "WA"]
    
    st.markdown('<div class="sticky-bar">', unsafe_allow_html=True)
    h_cols = st.columns(cw)
    for col, label in zip(h_cols, cols_labels):
        col.markdown(f"<p style='color:white; font-weight:bold; text-align:center; margin:0; font-size:14px;'>{label}</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 7. DATA DISPLAY ---
    st.markdown('<div class="content-scroll">', unsafe_allow_html=True)
    
    df = pd.DataFrame(data_sh.get_all_records())
    if u['Role'] == "RECRUITER": df = df[df['HR Name'] == u['Username']]
    if search_txt: df = df[df.apply(lambda r: search_txt.lower() in str(r).lower(), axis=1)]

    for idx, row in df.iterrows():
        r_cols = st.columns(cw)
        r_cols[0].markdown(f"<div class='row-item'>{row['Reference_ID']}</div>", unsafe_allow_html=True)
        r_cols[1].markdown(f"<div class='row-item'>{row['Candidate Name']}</div>", unsafe_allow_html=True)
        r_cols[2].markdown(f"<div class='row-item'>{row['Contact Number']}</div>", unsafe_allow_html=True)
        r_cols[3].markdown(f"<div class='row-item'>{row['Job Title']}</div>", unsafe_allow_html=True)
        r_cols[4].markdown(f"<div class='row-item'>{row['Interview Date']}</div>", unsafe_allow_html=True)
        r_cols[5].markdown(f"<div class='row-item'>{row['Status']}</div>", unsafe_allow_html=True)
        r_cols[6].markdown(f"<div class='row-item'>{row['Joining Date']}</div>", unsafe_allow_html=True)
        r_cols[7].markdown(f"<div class='row-item'>{row['SR Date']}</div>", unsafe_allow_html=True)
        r_cols[8].markdown(f"<div class='row-item'>{row['HR Name']}</div>", unsafe_allow_html=True)
        
        # Action Buttons
        if r_cols[9].button("📝", key=f"e_{idx}"): pass
        if r_cols[10].button("📲", key=f"w_{idx}"): pass

    st.markdown('</div>', unsafe_allow_html=True)

# --- 8. DIALOG LOGIC ---
if "show_add" in st.session_state:
    @st.dialog("➕ Add New Shortlist")
    def add_popup():
        st.write("Form Logic Here...")
        if st.button("Close"): 
            del st.session_state.show_add
            st.rerun()
    add_popup()
