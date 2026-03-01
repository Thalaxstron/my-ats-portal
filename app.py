import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG & Master CSS (Points 1, 2, 70, 81) ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
/* Full Page Gradient */
.stApp {
    background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
    background-attachment: fixed;
}

/* FIXED HEADER CONTAINER (Point 24, 81) */
.fixed-header {
    position: fixed; top: 0; left: 0; width: 100%; height: 215px;
    background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%);
    z-index: 1000; padding: 20px 45px; border-bottom: 2px solid white;
    display: flex; justify-content: space-between; align-items: flex-start;
}

/* TABLE HEADER FREEZE (Point 27) */
.table-header-freeze {
    position: fixed; top: 215px; left: 0; width: 100%; height: 45px;
    background-color: #0d47a1; z-index: 999; display: flex;
    border-bottom: 1px solid #ccc; align-items: center;
}

.h-cell {
    color: white; font-weight: bold; text-align: center; font-size: 13px;
    border-right: 1px solid rgba(255,255,255,0.3); display: flex; 
    align-items: center; justify-content: center; height: 100%;
}

/* Data Content Area */
.data-container { margin-top: 270px; background-color: white; min-height: 100vh; padding: 10px; }

/* White Inputs (Point 6, 7) */
div[data-baseweb="input"] > div, input, textarea {
    background-color: white !important; color: #0d47a1 !important; font-weight: bold !important;
}

.main-title { color: white; text-align: center; font-size: 40px; font-weight: bold; }
.sub-title { color: white; text-align: center; font-size: 25px; }

/* Red Login Button */
.stButton > button {
    background-color: #d32f2f !important; color: white !important;
    border-radius: 8px; font-weight: bold; border: none;
}
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION ---
def get_gsheet_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

try:
    client = get_gsheet_client()
    sh = client.open("ATS_Cloud_Database")
    user_sheet = sh.worksheet("User_Master")
    client_sheet = sh.worksheet("Client_Master")
    cand_sheet = sh.worksheet("ATS_Data")
except Exception as e:
    st.error(f"Database Error: {e}")
    st.stop()

# --- 3. HELPER FUNCTIONS ---
def get_next_ref_id():
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1: return "E00001"
    valid_ids = [int(val[1:]) for val in all_ids[1:] if str(val).startswith("E") and str(val)[1:].isdigit()]
    return f"E{max(valid_ids)+1:05d}" if valid_ids else "E00001"

# --- 4. LOGIN LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<br><div class='main-title'>TAKECARE MANPOWER SERVICES PVT LTD</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>ATS LOGIN</div>", unsafe_allow_html=True)
    _, col_m, _ = st.columns([1, 1.2, 1])
    with col_m:
        with st.container(border=True):
            u_mail = st.text_input("Email ID")
            u_pass = st.text_input("Password", type="password")
            if st.button("LOGIN", use_container_width=True):
                users_df = pd.DataFrame(user_sheet.get_all_records())
                user_row = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                if not user_row.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_row.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Incorrect username or password")
            st.caption("Forgot password? Contact Admin")
else:
    # --- 5. FIXED HEADER UI (LEFT SIDE 4 LINES / RIGHT SIDE 4 CONTROLS) ---
    u_data = st.session_state.user_data
    
    # HTML for Left Side Info (Points 14, 15, 17, 18)
    st.markdown(f"""
        <div class="fixed-header">
            <div style="color: white; flex: 2;">
                <h2 style="margin:0;">Takecare Manpower Services Pvt Ltd</h2>
                <p style="margin:0; font-size:16px;">Successful HR Firm</h1>
                <p style="margin:10px 0 0 0; font-size:18px;">Welcome back, {u_data['Username']}!</p>
				p style="margin:0; font-size:16px;">Successful HR Firm</h1
                <div style="background:white; color:#0d47a1; padding:6px 12px; border-radius:4px; font-weight:bold; margin-top:8px; display:inline-block;">
                    📞 Target: 80+ Calls / 3-5 Interview / 1+ Joining
                </div>
            </div>
            <div style="width: 250px;"></div>
        </div>
    """, unsafe_allow_html=True)

    # Right Side Controls (Points 20, 21, 22, 23)
    _, r_col = st.columns([3, 1])
    with r_col:
        st.markdown("<div style='height:25px;'></div>", unsafe_allow_html=True)
        if st.button("Logout 🚪", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
        s_query = st.text_input("Search", placeholder="🔍 Search...", label_visibility="collapsed")
        c1, c2 = st.columns(2)
        c1.button("Filter ⚙️", use_container_width=True)
        
        @st.dialog("➕ New Shortlist")
        def popup():
            ref = get_next_ref_id()
            st.write(f"**Ref ID:** {ref}")
            name = st.text_input("Candidate Name")
            phone = st.text_input("WhatsApp Number")
            c_master = pd.DataFrame(client_sheet.get_all_records())
            client_sel = st.selectbox("Client", ["-- Select --"] + sorted(c_master['Client Name'].unique().tolist()))
            pos = st.selectbox("Position", c_master[c_master['Client Name']==client_sel]['Position'].tolist() if client_sel != "-- Select --" else ["Select Client"])
            dt = st.date_input("Interview Date")
            if st.button("SUBMIT"):
                cand_sheet.append_row([ref, datetime.now().strftime("%d-%m-%Y"), name, phone, client_sel, pos, dt.strftime("%d-%m-%Y"), "Shortlisted", u_data['Username']])
                st.success("Saved!"); st.rerun()

        if c2.button("+ New", type="primary", use_container_width=True):
            popup()

    # --- 6. TABLE HEADERS FREEZE ---
    h_labels = ["Ref ID", "Candidate", "Contact", "Job Title", "Int. Date", "Status", "Joined", "SR Date", "HR Name", "Edit", "WA"]
    h_widths = [8, 12, 10, 15, 12, 10, 10, 8, 10, 5, 5]
    h_html = "".join([f'<div style="width:{w}%;" class="h-cell">{l}</div>' for l, w in zip(h_labels, h_widths)])
    st.markdown(f'<div class="table-header-freeze">{h_html}</div>', unsafe_allow_html=True)

    # --- 7. DATA CONTENT AREA ---
    st.markdown('<div class="data-container">', unsafe_allow_html=True)
    
    raw = cand_sheet.get_all_records()
    if raw:
        df = pd.DataFrame(raw)
        # Filter logic
        if u_data['Role'] == "RECRUITER": df = df[df['HR Name'] == u_data['Username']]
        
        for idx, row in df.iterrows():
            if s_query.lower() in str(row).lower():
                r_cols = st.columns([8, 12, 10, 15, 12, 10, 10, 8, 10, 5, 5])
                r_cols[0].write(row.get('Reference_ID',''))
                r_cols[1].write(row.get('Candidate Name',''))
                r_cols[2].write(row.get('Contact Number',''))
                r_cols[3].write(row.get('Job Title',''))
                r_cols[4].write(row.get('Interview Date',''))
                r_cols[5].write(row.get('Status',''))
                r_cols[6].write(row.get('Joining Date',''))
                r_cols[7].write(row.get('SR Date',''))
                r_cols[8].write(row.get('HR Name',''))
                if r_cols[9].button("📝", key=f"ed_{idx}"): st.info(f"Editing {row['Reference_ID']}")
                r_cols[10].write("📲")
    
    st.markdown('</div>', unsafe_allow_html=True)
