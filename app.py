import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse

# --- 1. PAGE CONFIG & PERFECT ALIGNMENT CSS ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    /* Gradient Background & No Black Bar */
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }
    header {visibility: hidden;} /* Removes top streamlit black bar */

    /* Fixed Header (215px) - Exact Placement */
    .fixed-header {
        position: fixed; top: 0; left: 0; width: 100%; height: 215px;
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%);
        z-index: 1000; padding: 20px 50px; border-bottom: 2px solid white;
        color: white; display: flex; justify-content: space-between;
    }
    
    .header-left { width: 65%; }
    .header-right { width: 30%; display: flex; flex-direction: column; align-items: flex-end; gap: 5px; }

    /* Sticky Table Header (45px) - Perfect Alignment with Rows */
    .sticky-bar {
        position: fixed; top: 215px; left: 0; width: 100%; height: 45px;
        background-color: #0d47a1; z-index: 999; border-bottom: 1px solid white;
        display: flex; align-items: center; color: white; font-weight: bold;
        padding: 0 10px;
    }

    /* Main Content Area - No White Gaps */
    .main-content { margin-top: 265px; padding: 0 10px; }
    
    /* White Text for Checkbox */
    div[data-baseweb="checkbox"] span { color: white !important; font-weight: bold; }

    /* Input Styling */
    input, select, textarea { color: #0d47a1 !important; font-weight: bold !important; }
    .stButton > button { width: 180px; border-radius: 5px; font-weight: bold; }
    .new-btn button { background-color: #ff4b4b !important; color: white !important; border: none; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE (Point 28-29) ---
def connect():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

gc = connect()
sh = gc.open("ATS_Cloud_Database")
data_sh = sh.worksheet("ATS_Data")
user_sh = sh.worksheet("User_Master")
client_sh = sh.worksheet("Client_Master")

# --- 3. LOGIN PAGE (Points 3-12) ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align:center; color:white; margin-top:100px;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:white;'>ATS LOGIN</h3>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1, 1])
    with col:
        with st.container(border=True):
            email = st.text_input("Email ID")
            pwd = st.text_input("Password", type="password")
            # Point 8: Remember Me in White
            st.checkbox("Remember Me") 
            if st.button("LOGIN", type="primary", use_container_width=True):
                users = pd.DataFrame(user_sh.get_all_records())
                match = users[(users['Mail_ID']==email) & (users['Password'].astype(str)==pwd)]
                if not match.empty:
                    st.session_state.auth = True
                    st.session_state.user = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Invalid Credentials")
else:
    # --- 4. DASHBOARD HEADER (Points 13-21) ---
    u = st.session_state.user
    
    # Header Content Placement
    st.markdown(f"""
    <div class="fixed-header">
        <div class="header-left">
            <h1 style="margin:0;">Takecare Manpower Service Pvt Ltd</h1>
            <h4 style="margin:0; opacity:0.8;">Successful HR Firm</h4>
            <p style="margin:5px 0; font-size:18px;">Welcome back, {u['Username']}!</p>
            <div style="background:white; color:#d32f2f; padding:5px 15px; border-radius:5px; font-weight:bold; display:inline-block;">
                📞 Target: 80+ Calls / 3-5 Interview / 1+ Joining
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Right Side Elements (Logout, Search, Filter, New)
    with st.container():
        st.markdown('<div style="position: fixed; top: 20px; right: 50px; z-index: 1001; width: 220px; display: flex; flex-direction: column; gap: 8px;">', unsafe_allow_html=True)
        if st.button("Logout 🚪"): 
            st.session_state.auth = False
            st.rerun()
        
        search_q = st.text_input("Search", placeholder="🔍 Search...", label_visibility="collapsed")
        
        if u['Role'] in ['ADMIN', 'TL']:
            if st.button("Filter ⚙️"): st.session_state.show_filter = True
        
        if st.button("+ New Shortlist", type="primary"):
            st.session_state.show_add = True
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 5. STICKY TABLE HEADER (Points 22-23) ---
    # Col widths optimized to match row data exactly
    c_widths = [0.7, 1.2, 1.0, 1.3, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.5]
    labels = ["Ref ID", "Candidate", "Contact", "Position", "Int. Date", "Status", "Joined", "SR Date", "HR Name", "Edit", "WA"]
    
    h_cols = st.columns(c_widths)
    st.markdown('<div class="sticky-bar">', unsafe_allow_html=True)
    # This bar is visually created in CSS, Streamlit columns below will align to it
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Overlays labels on the blue sticky bar
    st.markdown('<div style="position:fixed; top:215px; left:0; width:100%; z-index:1002; padding: 10px 10px;">', unsafe_allow_html=True)
    t_cols = st.columns(c_widths)
    for col, label in zip(t_cols, labels):
        col.markdown(f"<p style='color:white; font-weight:bold; text-align:center; margin:0;'>{label}</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 6. DATA ROWS (Points 55-68) ---
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    # Data Logic
    df = pd.DataFrame(data_sh.get_all_records())
    if u['Role'] == "RECRUITER": df = df[df['HR Name'] == u['Username']]
    if search_q: df = df[df.apply(lambda r: search_q.lower() in str(r).lower(), axis=1)]

    for idx, row in df.iterrows():
        # Auto-Delete Logic Visual (Point 55-58)
        r_cols = st.columns(c_widths)
        r_cols[0].write(row['Reference_ID'])
        r_cols[1].write(row['Candidate Name'])
        r_cols[2].write(row['Contact Number'])
        r_cols[3].write(row['Job Title'])
        r_cols[4].write(row['Interview Date'])
        r_cols[5].write(row['Status'])
        r_cols[6].write(row['Joining Date'])
        r_cols[7].write(row['SR Date'])
        r_cols[8].write(row['HR Name'])
        
        # Action Buttons (Points 39, 51)
        if r_cols[9].button("📝", key=f"e_{idx}"):
            st.session_state.edit_id = row['Reference_ID']
            st.rerun()
        if r_cols[10].button("📲", key=f"w_{idx}"):
            # WhatsApp logic
            pass
            
    st.markdown('</div>', unsafe_allow_html=True)

# --- 7. DIALOGS (Point 24, 39) ---
@st.dialog("New Entry")
def add_new():
    # New Shortlist Logic
    pass

if "show_add" in st.session_state:
    add_new()
    del st.session_state.show_add
