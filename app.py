import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG & UI ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for Red-Blue Gradient, Layout & Input boxes
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }
    /* Login Page Styling */
    .login-title { color: white; text-align: center; font-size: 35px; font-weight: bold; margin-top: 50px; }
    .login-sub { color: white; text-align: center; font-size: 25px; margin-bottom: 20px; }
    
    /* Dashboard Header Styling */
    .company-name { color: white; font-size: 28px; font-weight: bold; line-height: 1.2; }
    .company-sub { color: white; font-size: 18px; margin-bottom: 10px; }
    .welcome-text { color: white; font-size: 22px; font-weight: bold; }
    .target-bar { background-color: #1565c0; color: white; padding: 10px; border-radius: 5px; font-weight: bold; margin-top: 10px; }
    
    /* Input Boxes: White background with Blue text */
    input, select, textarea, div[data-baseweb="select"] > div { 
        background-color: white !important; 
        color: #0d47a1 !important; 
        font-weight: bold !important; 
    }
    label { color: white !important; font-weight: bold !important; }
    .stButton>button { border-radius: 8px; font-weight: bold; }
    
    /* Table Styling */
    .data-header { color: white; font-weight: bold; border-bottom: 2px solid white; padding: 5px; }
    .data-row { color: white; padding: 5px; border-bottom: 0.5px solid rgba(255,255,255,0.3); }
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
    st.error(f"Database Error: {e}"); st.stop()

# --- 3. HELPER FUNCTIONS ---
def get_next_ref_id():
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1: return "E00001"
    valid_ids = [int(val[1:]) for val in all_ids[1:] if str(val).startswith("E") and str(val)[1:].isdigit()]
    return f"E{max(valid_ids)+1:05d}" if valid_ids else "E00001"

# --- 4. SESSION MANAGEMENT ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 5. LOGIN PAGE ---
if not st.session_state.logged_in:
    st.markdown("<div class='login-title'>TAKECARE MANPOWER SERVICES PVT LTD</div>", unsafe_allow_html=True)
    st.markdown("<div class='login-sub'>ATS LOGIN</div>", unsafe_allow_html=True)
    
    _, col_m, _ = st.columns([1, 1.2, 1])
    with col_m:
        with st.container(border=True):
            u_mail = st.text_input("Email ID")
            u_pass = st.text_input("Password", type="password")
            col_rs = st.columns([1, 1])
            show_pass = col_rs[0].checkbox("Show Password")
            remember = col_rs[1].checkbox("Remember Me")
            
            if st.button("LOGIN", use_container_width=True):
                users_df = pd.DataFrame(user_sheet.get_all_records())
                users_df.columns = users_df.columns.str.strip()
                user_row = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                
                if not user_row.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_row.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("Incorrect username or password")
            st.markdown("<p style='text-align:center; color:white;'>Forgot password? Contact Admin</p>", unsafe_allow_html=True)

# --- 6. DASHBOARD ---
else:
    u = st.session_state.user_data
    
    # Header layout based on image
    t_col1, t_col2, t_col3, t_col4, t_col5 = st.columns([2.5, 2.5, 2, 1, 0.8])
    
    with t_col1:
        st.markdown("<div class='company-name'>Takecare Manpower Service Pvt Ltd</div>", unsafe_allow_html=True)
        st.markdown("<div class='company-sub'>Successful HR Firm</div>", unsafe_allow_html=True)
    
    with t_col2:
        st.markdown(f"<div class='welcome-text'>Welcome back, {u['Username']}!</div>", unsafe_allow_html=True)

    with t_col3:
        search_q = st.text_input("Search (any thing in data sheet)", label_visibility="collapsed", placeholder="Search...")

    with t_col4:
        # Filter Logic (Recruiter cannot see this)
        if u['Role'] != "RECRUITER":
            filter_mode = st.selectbox("Filter Symbol", ["All", "Client Wise", "Recruiter Wise", "Date Wise"], label_visibility="collapsed")
        else:
            st.write("")

    with t_col5:
        if st.button("Log out"):
            st.session_state.logged_in = False
            st.rerun()

    # Target Bar
    st.markdown("<div class='target-bar'>Target for Today: 📞 80+ Telescreening Calls / 3-5 Interview / 1+ Joining</div>", unsafe_allow_html=True)

    # New Shortlist Button (Right Aligned)
    _, btn_col = st.columns([5, 1])
    
    @st.dialog("➕ Add New Candidate Shortlist")
    def new_entry_dialog():
        cl_df = pd.DataFrame(client_sheet.get_all_records())
        cl_df.columns = cl_df.columns.str.strip()
        
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Candidate Name")
            phone = st.text_input("Contact Number")
            sel_client = st.selectbox("Client Name", sorted(cl_df['Client Name'].unique().tolist()))
        with c2:
            pos_list = cl_df[cl_df['Client Name'] == sel_client]['Position'].tolist()
            sel_pos = st.selectbox("Position or Job Title", pos_list)
            c_date = st.date_input("Commitment Date")
        
        feedback = st.text_area("Feedback")
        send_wa = st.checkbox("WhatsApp Invite Link", value=True)
        
        b1, b2 = st.columns(2)
        if b1.button("SUBMIT", use_container_width=True):
            ref_id = get_next_ref_id()
            today = datetime.now().strftime("%d-%m-%Y")
            c_date_str = c_date.strftime("%d-%m-%Y")
            
            # WA Message Logic
            if send_wa:
                c_info = cl_df[(cl_df['Client Name'] == sel_client) & (cl_df['Position'] == sel_pos)].iloc[0]
                msg = f"Dear {name},\nCongratulations! Invite for Interview.\n\nPosition: {sel_pos}\nDate: {c_date_str}\nTime: 10.30 AM\nVenue: {c_info.get('Address')}\nMap: {c_info.get('Map Link')}\nContact: {c_info.get('Contact Person')}\n\nRegards,\n{u['Username']}\nTakecare HR Team"
                wa_url = f"https://wa.me/91{phone}?text={urllib.parse.quote(msg)}"
                st.markdown(f'<a href="{wa_url}" target="_blank">📲 Send WhatsApp Invite</a>', unsafe_allow_html=True)

            cand_sheet.append_row([ref_id, today, name, phone, sel_client, sel_pos, c_date_str, "Shortlisted", u['Username'], "", "", feedback])
            st.success("Shortlist Saved!")
            st.rerun()
        if b2.button("CANCEL", use_container_width=True): st.rerun()

    if btn_col.button("+ New Shortlist", use_container_width=True):
        new_entry_dialog()

    # --- 7. DATA DISPLAY WITH AUTO-DELETE LOGIC ---
    raw_df = pd.DataFrame(cand_sheet.get_all_records())
    if not raw_df.empty:
        raw_df.columns = raw_df.columns.str.strip()
        
        # Access Control
        if u['Role'] == "RECRUITER":
            df = raw_df[raw_df['HR Name'] == u['Username']]
        elif u['Role'] == "TL":
            users = pd.DataFrame(user_sheet.get_all_records())
            team = users[users['Report_To'] == u['Username']]['Username'].tolist()
            df = raw_df[raw_df['HR Name'].isin(team + [u['Username']])]
        else:
            df = raw_df

        # --- AUTO DELETE (Visual Only) ---
        today_dt = datetime.now()
        df['Shortlisted Date DT'] = pd.to_datetime(df['Shortlisted Date'], format="%d-%m-%Y", errors='coerce')
        df['Int Date DT'] = pd.to_datetime(df['Interview Date'], format="%d-%m-%Y", errors='coerce')

        # Logic 1: Shortlisted > 7 days
        df = df[~((df['Status'] == 'Shortlisted') & (df['Shortlisted Date DT'] < today_dt - timedelta(days=7)))]
        # Logic 2: Interviewed/Selected/Rejected > 30 days
        df = df[~((df['Status'].isin(['Selected', 'Rejected', 'Hold'])) & (df['Int Date DT'] < today_dt - timedelta(days=30)))]
        # Logic 3: Left/Not Joined > 7 days
        df = df[~((df['Status'].isin(['Left', 'Not Joined'])) & (df['Int Date DT'] < today_dt - timedelta(days=7)))]

        # --- TABLE ---
        st.markdown("---")
        cols = st.columns([0.8, 1.2, 1, 1.2, 1, 1, 1, 1, 1, 0.5])
        headers = ["Ref ID", "Candidate", "Contact", "Job Title", "Int. Date", "Status", "Onboard", "SR Date", "HR Name", "Edit"]
        for col, h in zip(cols, headers): col.markdown(f"<div class='data-header'>{h}</div>", unsafe_allow_html=True)

        for i, row in df.iterrows():
            if search_q.lower() not in str(row).lower(): continue
            r_cols = st.columns([0.8, 1.2, 1, 1.2, 1, 1, 1,
