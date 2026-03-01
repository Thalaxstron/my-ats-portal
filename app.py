import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Takecare ATS", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS (Points 2, 6, 7, 23) ---
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #d32f2f, #0d47a1) !important; background-attachment: fixed; }
    
    /* Fixed Header (215px) */
    .header-container {
        position: fixed; top: 0; left: 0; width: 100%; height: 215px;
        background: linear-gradient(135deg, #d32f2f, #0d47a1);
        z-index: 1000; border-bottom: 2px solid white; padding: 15px 50px;
        display: flex; justify-content: space-between;
    }
    
    .header-left { color: white; width: 65%; }
    .header-right { width: 30%; display: flex; flex-direction: column; align-items: flex-end; gap: 8px; }

    /* Table Header Freeze (45px) */
    .sticky-bar {
        position: fixed; top: 215px; left: 0; width: 100%; height: 45px;
        background-color: #0d47a1; z-index: 999; border-bottom: 1px solid white;
        display: flex; align-items: center; color: white; font-weight: bold;
    }

    /* Scrollable Body */
    .main-body { margin-top: 270px; padding: 20px; background: white; min-height: 100vh; border-radius: 15px 15px 0 0; }
    
    /* Input Styling */
    input, select, textarea { color: #0d47a1 !important; font-weight: bold !important; background: white !important; }
    .stButton > button { border-radius: 5px; font-weight: bold; width: 100%; }
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
client_sh = sh.worksheet("Client_Master")
user_sh = sh.worksheet("User_Master")

# --- 3. SESSION & LOGIN ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    # Login Page (Points 3-12)
    st.markdown("<h1 style='text-align:center; color:white; margin-top:50px;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:white;'>ATS LOGIN</h3>", unsafe_allow_html=True)
    _, login_col, _ = st.columns([1, 1, 1])
    with login_col:
        with st.container(border=True):
            email = st.text_input("Email ID")
            pwd = st.text_input("Password", type="password")
            if st.button("LOGIN", type="primary"):
                users = pd.DataFrame(user_sh.get_all_records())
                match = users[(users['Mail_ID']==email) & (users['Password'].astype(str)==pwd)]
                if not match.empty:
                    st.session_state.auth = True
                    st.session_state.user = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Incorrect username or password")
            st.caption("Forgot password? Contact Admin")
else:
    # --- 4. DASHBOARD ---
    u = st.session_state.user
    
    # HEADER (Points 14-21)
    # Left Side: 4 Lines
    st.markdown(f"""
    <div class="header-container">
        <div class="header-left">
            <h2 style="margin:0; font-size:25px;">Takecare Manpower Service Pvt Ltd</h2>
            <h4 style="margin:0; font-size:20px; font-style:italic;">Successful HR Firm</h4>
            <p style="margin:5px 0; font-size:18px;">Welcome back, {u['Username']}!</p>
            <p style="margin:0; font-size:18px; background:white; color:#0d47a1; display:inline-block; padding:2px 10px; border-radius:4px;">
                Target for Today: 80+ Telescreening Calls / 3-5 Interview / 1+ Joining
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Right Side: 4 Buttons (Onne kela onnu)
    with st.container():
        st.markdown('<div style="position: fixed; top: 15px; right: 50px; z-index: 1001; width: 220px; display: flex; flex-direction: column; gap: 5px;">', unsafe_allow_html=True)
        if st.button("Logout 🚪"): 
            st.session_state.auth = False
            st.rerun()
        search_val = st.text_input("Search", placeholder="Search...", label_visibility="collapsed")
        
        if u['Role'] in ['ADMIN', 'TL']:
            if st.button("Filter ⚙️"): st.session_state.show_filter = True
        else: st.write("") # Placeholder to maintain alignment

        if st.button("+ New Shortlist", type="primary"):
            st.session_state.show_add = True
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 5. TABLE HEADER (Point 22) ---
    cols = [6, 12, 10, 12, 10, 10, 10, 10, 10, 5, 5]
    labels = ["Ref ID", "Candidate", "Contact", "Position", "Int. Date", "Status", "Onboard", "SR Date", "HR Name", "Edit", "WA"]
    h_html = "".join([f'<div style="width:{w}%; text-align:center;">{l}</div>' for w, l in zip(cols, labels)])
    st.markdown(f'<div class="sticky-bar">{h_html}</div>', unsafe_allow_html=True)

    # --- 6. DATA & POPUPS ---
    st.markdown('<div class="main-body">', unsafe_allow_html=True)
    
    # Dialogs
    if "show_add" in st.session_state:
        @st.dialog("➕ Add New Shortlist")
        def add_dialog():
            # ID Logic (Point 30)
            ids = data_sh.col_values(1)
            new_id = f"E{len(ids):05d}"
            st.write(f"Ref ID: **{new_id}**")
            
            c1, c2 = st.columns(2)
            name = c1.text_input("Candidate Name")
            phone = c2.text_input("Contact Number")
            
            clients_df = pd.DataFrame(client_sh.get_all_records())
            sel_client = st.selectbox("Client Name", sorted(clients_df['Client Name'].unique()))
            pos_list = clients_df[clients_df['Client Name']==sel_client]['Position'].tolist()
            sel_pos = st.selectbox("Position", pos_list)
            
            dt = st.date_input("Commitment Date")
            fb = st.text_area("Feedback")
            
            if st.button("Submit"):
                data_sh.append_row([new_id, datetime.now().strftime("%d-%m-%Y"), name, phone, sel_client, sel_pos, dt.strftime("%d-%m-%Y"), "Shortlisted", u['Username'], "", "", fb])
                del st.session_state.show_add
                st.rerun()
        add_dialog()

    # Data Fetching
    df = pd.DataFrame(data_sh.get_all_records())
    if u['Role'] == "RECRUITER": df = df[df['HR Name'] == u['Username']]
    
    # Search Logic
    if search_val:
        df = df[df.apply(lambda r: search_val.lower() in str(r).lower(), axis=1)]

    # Render Rows
    for idx, row in df.iterrows():
        r_cols = st.columns(cols)
        r_cols[0].write(row['Reference_ID'])
        r_cols[1].write(row['Candidate Name'])
        r_cols[2].write(row['Contact Number'])
        r_cols[3].write(row['Job Title'])
        r_cols[4].write(row['Interview Date'])
        r_cols[5].write(row['Status'])
        r_cols[6].write(row['Joining Date'])
        r_cols[7].write(row['SR Date'])
        r_cols[8].write(row['HR Name'])
        
        if r_cols[9].button("📝", key=f"ed_{idx}"):
            # Edit Popup Logic here
            pass
            
        if r_cols[10].button("📲", key=f"wa_{idx}"):
            # WA Logic here
            pass

    st.markdown('</div>', unsafe_allow_html=True)
