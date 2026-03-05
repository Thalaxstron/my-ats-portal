import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG & UI STYLING ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide")

# Point 69 & UI Cleanup: Removing initial black patches
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e) !important;
        background-attachment: fixed;
    }
    /* Removing dark overlays from containers */
    div[data-testid="stVerticalBlock"] > div { background: transparent !important; }
    div[data-testid="stForm"] { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 15px; }

    /* Input Boxes (Point 7 & 8) */
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div, div[data-baseweb="textarea"] > div {
        background-color: white !important;
        border-radius: 8px !important;
    }
    input, select, textarea { color: #00008b !important; font-weight: bold !important; }
    label { color: white !important; font-weight: bold !important; }
    
    /* Login Button (Point 10) */
    .stButton > button {
        background-color: #FF0000 !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        border-radius: 10px !important;
    }
    .slogan { color: #FFD700 !important; font-size: 20px; font-weight: bold; }
    .header-text { color: #00BFFF !important; font-weight: bold; border-bottom: 1px solid #444; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION ---
def get_gsheet_client():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        return authorize(creds)
    except Exception as e:
        st.error(f"GCP Connection Error: {e}"); return None

client = get_gsheet_client()
if client:
    sh = client.open("ATS_Cloud_Database")
    user_sheet = sh.worksheet("User_Master")
    client_sheet = sh.worksheet("Client_Master")
    cand_sheet = sh.worksheet("ATS_Data")

# --- 3. HELPER FUNCTIONS ---
def get_next_ref_id():
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1: return "E0001"
    valid_ids = [int(val[1:]) for val in all_ids[1:] if str(val).startswith("E") and str(val)[1:].isdigit()]
    return f"E{max(valid_ids)+1:04d}" if valid_ids else "E0001"

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 4. LOGIN PAGE (Points 2-13) ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: white;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: white; border-bottom: 2px solid red; padding-bottom: 10px;'>ATS LOGIN</h3>", unsafe_allow_html=True)
    
    _, col_m, _ = st.columns([1, 1.2, 1])
    with col_m:
        with st.form("login_form"):
            u_mail = st.text_input("Email ID")
            u_pass = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN", use_container_width=True):
                users_df = pd.DataFrame(user_sheet.get_all_records())
                user_match = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                if not user_match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_match.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("Incorrect username or password")
            st.markdown("<p style='text-align:center; color:white;'>Forgot password? Contact Admin</p>", unsafe_allow_html=True)

# --- 5. DASHBOARD (LOGGED IN) ---
else:
    u_data = st.session_state.user_data
    
    # Header Section
    h_col1, h_col2, h_col3 = st.columns([2, 1.5, 0.5])
    with h_col1:
        st.markdown("<h1 style='font-size: 25px; color: white; margin-bottom:0;'>Takecare Manpower Service Pvt Ltd</h1>", unsafe_allow_html=True)
        st.markdown("<p class='slogan'>Successful HR Firm</p>", unsafe_allow_html=True)
    with h_col2:
        st.markdown(f"<p style='color: white; font-size: 18px; margin-bottom:0;'>Welcome back, {u_data['Username']}!</p>", unsafe_allow_html=True)
        st.markdown("<p style='color: #00FF00;'>Target: 80+ Calls / 3-5 Interview / 1+ Joining</p>", unsafe_allow_html=True)
    with h_col3:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # Action Row
    c_btn1, c_btn2, c_btn3, c_search = st.columns([1, 1, 1.2, 2])
    
    # DIALOG: New Shortlist (Point 24-38)
    @st.dialog("➕ New Candidate Shortlist")
    def new_shortlist_dialog():
        ref_id = get_next_ref_id()
        st.markdown(f"**Reference ID:** `{ref_id}` | **Date:** {datetime.now().strftime('%d-%m-%Y')}")
        
        c_master = pd.DataFrame(client_sheet.get_all_records())
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Candidate Name")
            phone = st.text_input("Contact Number")
            sel_client = st.selectbox("Client Name", ["--Select--"] + sorted(c_master['Client Name'].unique().tolist()))
        with col2:
            pos_list = c_master[c_master['Client Name'] == sel_client]['Position'].tolist() if sel_client != "--Select--" else []
            sel_pos = st.selectbox("Position", pos_list)
            comm_date = st.date_input("Commitment Date")
            status = st.selectbox("Status", ["Shortlisted"])
            
        feedback = st.text_area("Feedback (Optional)")
        
        c1, c2 = st.columns(2)
        if c1.button("SUBMIT", use_container_width=True):
            if name and phone and sel_client != "--Select--":
                new_row = [ref_id, datetime.now().strftime('%d-%m-%Y'), name, phone, sel_client, sel_pos, comm_date.strftime('%d-%m-%Y'), status, u_data['Username'], "", "", feedback]
                cand_sheet.append_row(new_row)
                st.success("Shortlisted Successfully!")
                st.rerun()
            else: st.warning("Please fill required fields")
        if c2.button("CANCEL", use_container_width=True): st.rerun()

    # DIALOG: Update Status (Point 39-49)
    @st.dialog("📝 Update Candidate Status")
    def update_status_dialog(row_data):
        st.markdown(f"**Updating:** {row_data['Candidate Name']} ({row_data['Reference_ID']})")
        col1, col2 = st.columns(2)
        with col1:
            new_status = st.selectbox("Status", ["Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Left", "Project Success"])
            fb = st.text_input("Feedback (Max 20 chars)", max_chars=20)
        with col2:
            dt = st.date_input("Interview / Onboarded Date")

        if st.button("UPDATE DATA"):
            # Update logic (Point 54: Onboarded + SR Days)
            sr_date = ""
            if new_status == "Onboarded":
                c_master = pd.DataFrame(client_sheet.get_all_records())
                days = c_master[c_master['Client Name'] == row_data['Client Name']]['SR Days'].values[0]
                sr_date = (dt + timedelta(days=int(days))).strftime('%d-%m-%Y')
            
            # Find row and update
            cell = cand_sheet.find(row_data['Reference_ID'])
            cand_sheet.update_cell(cell.row, 8, new_status) # Status
            cand_sheet.update_cell(cell.row, 12, fb) # Feedback
            if sr_date: cand_sheet.update_cell(cell.row, 11, sr_date)
            st.rerun()

    with c_btn3:
        if st.button("➕ New Shortlist"): new_shortlist_dialog()
    with c_search:
        search_query = st.text_input("🔍 Search Anything", placeholder="Type name, ID, or phone...")

    # --- DATA TABLE ---
    st.markdown("---")
    h_cols = st.columns([0.8, 1.5, 1.2, 1.2, 1.2, 1, 1, 1, 0.5, 0.5])
    labels = ["Ref ID", "Candidate", "Number", "Job Title", "Int/Comm Date", "Status", "Onboard", "SR Date", "Edit", "WA"]
    for col, l in zip(h_cols, labels): col.markdown(f"<div class='header-text'>{l}</div>", unsafe_allow_html=True)
    
    raw_data = cand_sheet.get_all_records()
    df = pd.DataFrame(raw_data)
    
    # Handling Column Name Discrepancy (KeyError Fix)
    df.columns = [c.strip() for c in df.columns]
    
    if u_data['Role'] == "RECRUITER": df = df[df['HR Name'] == u_data['Username']]
    if search_query: df = df[df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]

    for _, row in df.iterrows():
        r_cols = st.columns([0.8, 1.5, 1.2, 1.2, 1.2, 1, 1, 1, 0.5, 0.5])
        r_cols[0].write(row.get('Reference_ID', ''))
        r_cols[1].write(row.get('Candidate Name', ''))
        r_cols[2].write(row.get('Contact Number', ''))
        r_cols[3].write(row.get('Job Title', ''))
        r_cols[4].write(row.get('Commitment Date', '')) # Verified name
        r_cols[5].write(row.get('Status', ''))
        r_cols[6].write(row.get('Onboarded Date', ''))
        r_cols[7].write(row.get('SR Date', ''))
        
        if r_cols[8].button("📝", key=f"ed_{row['Reference_ID']}"):
            update_status_dialog(row)
            
        if r_cols[9].button("📲", key=f"wa_{row['Reference_ID']}"):
            msg = f"Dear {row['Candidate Name']},\nCongratulations! You are shortlisted for {row['Job Title']}..."
            url = f"https://wa.me/91{row['Contact Number']}?text={urllib.parse.quote(msg)}"
            st.link_button("Open WhatsApp", url)
