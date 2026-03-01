import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse
import time

# --- 1. PAGE CONFIG & FULL UI FIX ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide", initial_sidebar_state="collapsed")

# Indha CSS thaan unga alignment issues-ai fix pannum
st.markdown("""
<style>
    /* Full Gradient Background */
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }
    header {visibility: hidden;} /* Top black bar-ai remove pannum */

    /* Fixed Design Header (215px) */
    .fixed-header {
        position: fixed; top: 0; left: 0; width: 100%; height: 215px;
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%);
        z-index: 1000; padding: 25px 50px; border-bottom: 2px solid white;
        color: white;
    }

    /* Fixed Table Header (45px) - Matches Data Rows */
    .sticky-table-header {
        position: fixed; top: 215px; left: 0; width: 100%; height: 45px;
        background-color: #0d47a1; z-index: 999; display: flex; align-items: center;
        border-bottom: 1px solid white; color: white; font-weight: bold;
        padding: 0 10px;
    }

    /* Content Area - No Gaps */
    .main-content { margin-top: 260px; padding: 10px; }

    /* Input & Button Styling */
    input, select, textarea { color: #0d47a1 !important; font-weight: bold !important; background-color: white !important; }
    div[data-baseweb="checkbox"] span { color: white !important; font-weight: bold; } /* Remember Me White */
    
    .stButton > button { border-radius: 5px; font-weight: bold; width: 100%; }
    
    /* Table Cell Design */
    .cell-data { color: white; text-align: center; padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,0.1); }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION ---
def get_db():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        return authorize(creds)
    except: return None

gc = get_db()
sh = gc.open("ATS_Cloud_Database")
data_sh = sh.worksheet("ATS_Data")
user_sh = sh.worksheet("User_Master")
client_sh = sh.worksheet("Client_Master")

# --- 3. LOGIN PAGE (Points 3-12) ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align:center; color:white; margin-top:80px;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:white;'>ATS LOGIN</h3>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1, 1])
    with col:
        with st.container(border=True):
            email = st.text_input("Email ID")
            pwd = st.text_input("Password", type="password")
            # Point 8: Remember Me - Text in White (handled by CSS)
            st.checkbox("Remember Me") 
            if st.button("LOGIN", type="primary"):
                users = pd.DataFrame(user_sh.get_all_records())
                match = users[(users['Mail_ID']==email) & (users['Password'].astype(str)==pwd)]
                if not match.empty:
                    st.session_state.auth = True
                    st.session_state.user = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Check Email/Password")
else:
    # --- 4. DASHBOARD HEADER (Points 13-21) ---
    u = st.session_state.user
    
    # Left Side Info
    st.markdown(f"""
    <div class="fixed-header">
        <div style="float: left; width: 65%;">
            <h1 style="margin:0;">Takecare Manpower Service Pvt Ltd</h1>
            <h2 style="margin:0; opacity:1.0;">Successful HR Firm</h2>
            <p style="margin:5px 0; font-size:22px;">Welcome back, {u['Username']}!</p>
            <div style="background: white; color: #d32f2f; padding: 5px 15px; border-radius: 5px; display: inline-block; font-weight: bold;">
                Target for Today: 📞 80+ Telescreening / 3-5 Interview / 1+ Joining
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Right Side Controls (Logout, Search, Filter, New Shortlist)
    with st.container():
        # Fixed position to keep them above everything else
        st.markdown('<div style="position: fixed; top: 15px; right: 50px; z-index: 1001; width: 220px; display: flex; flex-direction: column; gap: 5px;">', unsafe_allow_html=True)
        if st.button("Logout 🚪"): 
            st.session_state.auth = False
            st.rerun()
        s_val = st.text_input("Search", placeholder="Search...", label_visibility="collapsed")
        if u['Role'] in ['ADMIN', 'TL']:
            if st.button("Filter ⚙️"): st.session_state.show_filter = True
        if st.button("+ New Shortlist", type="primary"):
            st.session_state.show_add = True
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 5. STICKY TABLE HEADER (Point 22-23) ---
    # Col widths optimized for 100% alignment
    c_widths = [0.7, 1.2, 1.0, 1.3, 1.0, 1.0, 1.0, 1.0, 1.0, 0.4, 0.4]
    labels = ["Ref ID", "Candidate", "Contact", "Position", "Int. Date", "Status", "Joined", "SR Date", "HR Name", "Edit", "WA"]
    
    # Sticky header row
    st.markdown('<div class="sticky-table-header">', unsafe_allow_html=True)
    h_cols = st.columns(c_widths)
    for col, lab in zip(h_cols, labels):
        col.markdown(f"<p style='text-align:center; margin:0;'>{lab}</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 6. DATA AREA (Points 55-68) ---
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    # New Entry Dialog (Point 24)
    @st.dialog("➕ Add Shortlist")
    def add_new():
        ids = data_sh.col_values(1)
        new_id = f"E{len(ids):05d}"
        st.write(f"Ref ID: **{new_id}**")
        name = st.text_input("Name")
        phone = st.text_input("Phone")
        clients = pd.DataFrame(client_sh.get_all_records())
        sel_client = st.selectbox("Client", sorted(clients['Client Name'].unique()))
        pos = clients[clients['Client Name']==sel_client]['Position'].tolist()
        sel_pos = st.selectbox("Position", pos)
        dt = st.date_input("Date")
        fb = st.text_area("Feedback")
        if st.button("Save"):
            data_sh.append_row([new_id, datetime.now().strftime("%d-%m-%Y"), name, phone, sel_client, sel_pos, dt.strftime("%d-%m-%Y"), "Shortlisted", u['Username'], "", "", fb])
            st.rerun()

    if "show_add" in st.session_state:
        add_new()
        del st.session_state.show_add

    # Data Fetch and Filter
    df = pd.DataFrame(data_sh.get_all_records())
    if u['Role'] == "RECRUITER": df = df[df['HR Name'] == u['Username']]
    if s_val: df = df[df.apply(lambda r: s_val.lower() in str(r).lower(), axis=1)]

    # Display Data Rows
    for idx, row in df.iterrows():
        # Visual cleanup: hide old entries logic can go here (Point 55)
        r_cols = st.columns(c_widths)
        r_cols[0].markdown(f"<div class='cell-data'>{row['Reference_ID']}</div>", unsafe_allow_html=True)
        r_cols[1].markdown(f"<div class='cell-data'>{row['Candidate Name']}</div>", unsafe_allow_html=True)
        r_cols[2].markdown(f"<div class='cell-data'>{row['Contact Number']}</div>", unsafe_allow_html=True)
        r_cols[3].markdown(f"<div class='cell-data'>{row['Job Title']}</div>", unsafe_allow_html=True)
        r_cols[4].markdown(f"<div class='cell-data'>{row['Interview Date']}</div>", unsafe_allow_html=True)
        r_cols[5].markdown(f"<div class='cell-data'>{row['Status']}</div>", unsafe_allow_html=True)
        r_cols[6].markdown(f"<div class='cell-data'>{row['Joining Date']}</div>", unsafe_allow_html=True)
        r_cols[7].markdown(f"<div class='cell-data'>{row['SR Date']}</div>", unsafe_allow_html=True)
        r_cols[8].markdown(f"<div class='cell-data'>{row['HR Name']}</div>", unsafe_allow_html=True)
        
        # Edit Button (Point 39)
        if r_cols[9].button("📝", key=f"ed_{idx}"):
            # Edit dialog logic
            pass
            
        # WA Button (Point 51)
        if r_cols[10].button("📲", key=f"wa_{idx}"):
            # WhatsApp logic
            pass

    st.markdown('</div>', unsafe_allow_html=True)
