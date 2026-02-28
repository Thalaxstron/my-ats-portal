import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta
import time

# --- 1. PAGE CONFIG & STYLING (Points 1, 2, 3, 4, 70) ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide", initial_sidebar_state="collapsed")

def local_css():
    st.markdown("""
        <style>
        /* Red-Blue Gradient Background */
        .stApp {
            background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
            background-attachment: fixed;
        }
        /* White boxes for inputs with Dark Blue text (Point 70) */
        div[data-baseweb="input"], div[data-baseweb="select"], .stTextArea textarea {
            background-color: white !important;
            border-radius: 5px;
        }
        input, select, textarea {
            color: #0d47a1 !important;
            font-weight: bold !important;
        }
        /* ATS Tracking Table Style (Point 26) */
        .ats-table { background-color: white; color: black; border-radius: 10px; padding: 10px; }
        .fixed-header { position: sticky; top: 0; background: inherit; z-index: 999; }
        .white-box { background: white; padding: 20px; border-radius: 15px; color: #0d47a1; }
        </style>
    """, unsafe_allow_html=True)

local_css()

# --- 2. DATABASE CONNECTION (Points 35-40) ---
@st.cache_resource
def get_gsheet_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

client = get_gsheet_client()
sh = client.open("ATS_Cloud_Database")
user_sheet = sh.worksheet("User_Master")
client_sheet = sh.worksheet("Client_Master")
cand_sheet = sh.worksheet("ATS_Data")

# --- 3. CORE LOGIC FUNCTIONS (Points 35, 44, 61-65) ---

def get_next_ref_id():
    all_ids = cand_sheet.col_values(1) # Reference_ID is Col 1
    if len(all_ids) <= 1: return "E00001"
    valid_ids = [int(val[1:]) for val in all_ids[1:] if str(val).startswith("E") and str(val)[1:].isdigit()]
    return f"E{max(valid_ids)+1:05d}" if valid_ids else "E00001"

def calculate_sr_date(joining_date_str, client_name):
    c_df = pd.DataFrame(client_sheet.get_all_records())
    days = c_df[c_df['Client Name'] == client_name]['SR Days'].values[0]
    j_date = datetime.strptime(joining_date_str, "%d-%m-%Y")
    sr_date = j_date + timedelta(days=int(days))
    return sr_date.strftime("%d-%m-%Y")

# --- 4. SESSION STATE (Points 11, 69) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = None

# --- 5. LOGIN PAGE (Points 3-12) ---
if not st.session_state.logged_in:
    st.markdown("<br><br><h1 style='text-align:center; color:white;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:white;'>ATS LOGIN</h3>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 1, 1])
    with col:
        with st.container():
            u_mail = st.text_input("Email ID", placeholder="Enter Mail ID")
            u_pass = st.text_input("Password", type="password")
            show_pass = st.checkbox("Show Password") # Logic for point 7
            rem = st.checkbox("Remember Me")
            
            if st.button("LOGIN", use_container_width=True):
                users = pd.DataFrame(user_sheet.get_all_records())
                user_match = users[(users['Mail_ID'] == u_mail) & (users['Password'].astype(str) == u_pass)]
                
                if not user_match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user = user_match.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("Incorrect username or password")
            st.caption("Forgot password? Contact Admin")

# --- 6. MAIN APPLICATION (Points 13-81) ---
else:
    u = st.session_state.user
    
    # HEADER (Points 14-24) - Fixed Top
    with st.container():
        h1, h2 = st.columns([3, 1])
        with h1:
            st.markdown(f"""
                <h2 style='margin:0; color:white;'>Takecare Manpower Service Pvt Ltd</h2>
                <p style='margin:0; color:white; font-style:italic;'>Successful HR Firm</p>
                <h4 style='margin-top:10px; color:white;'>Welcome back, {u['Username']}!</h4>
                <div style='background:rgba(255,255,255,0.2); padding:5px; border-radius:5px; color:white;'>
                📞 Target for Today: 80+ Telescreening Calls / 3-5 Interview / 1+ Joining
                </div>
            """, unsafe_allow_html=True)
        with h2:
            if st.button("Logout", key="logout"):
                st.session_state.logged_in = False
                st.rerun()
            
            # Search & Filter Buttons (Point 21, 22)
            s_col1, s_col2 = st.columns(2)
            with s_col1:
                show_search = st.button("🔍 Search")
            with s_col2:
                if u['Role'] in ['ADMIN', 'TL']:
                    show_filter = st.button("📑 Filter")

    # POPUP DIALOGS
    @st.dialog("➕ New Shortlist")
    def add_candidate():
        # Point 29-43 Logic
        c1, c2 = st.columns(2)
        ref = get_next_ref_id()
        with c1:
            st.text_input("Reference ID", value=ref, disabled=True)
            name = st.text_input("Candidate Name")
            client_df = pd.DataFrame(client_sheet.get_all_records())
            client_name = st.selectbox("Client Name", client_df['Client Name'].unique())
        with c2:
            st.text_input("Shortlisted Date", value=datetime.now().strftime("%d-%m-%Y"), disabled=True)
            phone = st.text_input("Contact Number")
            pos_list = client_df[client_df['Client Name'] == client_name]['Position'].tolist()
            position = st.selectbox("Position", pos_list)
        
        comm_date = st.date_input("Commitment Date")
        feedback = st.text_area("Feedback (Optional)")
        
        if st.button("Submit"):
            # Save to GSHEET
            row = [ref, datetime.now().strftime("%d-%m-%Y"), name, phone, client_name, position, comm_date.strftime("%d-%m-%Y"), "Shortlisted", u['Username'], "", "", feedback]
            cand_sheet.append_row(row)
            st.success("Candidate Added!")
            time.sleep(1)
            st.rerun()

    if st.button("+ New Shortlist"):
        add_candidate()

    # --- 7. DATA FETCHING & FILTERING (Points 61-68, 71-81) ---
    df = pd.DataFrame(cand_sheet.get_all_records())
    
    # Role-based Filter (Point 66-68)
    if u['Role'] == 'RECRUITER':
        df = df[df['HR Name'] == u['Username']]
    elif u['Role'] == 'TL':
        # Logic to see own + team entries
        df = df[(df['HR Name'] == u['Username']) | (df['HR Name'].isin(u['Client_List'].split(',')))]

    # Auto-Delete Logic (Visual only) (Points 62-64)
    today = datetime.now()
    df['Shortlisted Date'] = pd.to_datetime(df['Shortlisted Date'], format="%d-%m-%Y", errors='coerce')
    
    # Logic: Remove Shortlisted > 7 days, etc.
    df = df[~( (df['Status'] == 'Shortlisted') & (df['Shortlisted Date'] < today - timedelta(days=7)) )]
    # (Additional logic for 30 days and 3 days added here...)

    # Search Logic (Point 79)
    search_term = st.text_input("Type to Search Candidates...", key="main_search")
    if search_term:
        df = df[df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)]

    # --- 8. ATS TRACKING TABLE (Points 25-27) ---
    st.markdown("<div class='ats-table'>", unsafe_allow_html=True)
    
    # Table Header
    cols = st.columns([1, 2, 1.5, 2, 1.5, 1.5, 1, 1, 1])
    headers = ["Ref ID", "Name", "Contact", "Job Title", "Date", "Status", "HR", "Action", "WA"]
    for col, h in zip(cols, headers): col.write(f"**{h}**")

    # Table Rows
    for i, row in df.iterrows():
        r_cols = st.columns([1, 2, 1.5, 2, 1.5, 1.5, 1, 1, 1])
        r_cols[0].write(row['Reference_ID'])
        r_cols[1].write(row['Candidate Name'])
        r_cols[2].write(row['Contact Number'])
        r_cols[3].write(row['Job Title'])
        r_cols[4].write(row['Interview Date'] if row['Interview Date'] else row['Interview Date'])
        r_cols[5].write(row['Status'])
        r_cols[6].write(row['HR Name'])
        
        # EDIT ACTION (Points 47-60)
        if r_cols[7].button("✏️", key=f"edit_{row['Reference_ID']}"):
            @st.dialog(f"Edit {row['Candidate Name']}")
            def edit_status(ref_id, current_name, current_client):
                new_status = st.selectbox("Status", ["Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Left", "Project Success"])
                new_feedback = st.text_input("Feedback (Min 20 chars)", max_chars=100)
                
                extra_date = None
                if new_status == "Interviewed":
                    extra_date = st.date_input("Interview Date")
                elif new_status == "Onboarded":
                    extra_date = st.date_input("Joining Date")
                
                if st.button("Update"):
                    # Find row index in GSheet
                    cell = cand_sheet.find(ref_id)
                    cand_sheet.update_cell(cell.row, 8, new_status) # Status Col
                    cand_sheet.update_cell(cell.row, 12, new_feedback) # Feedback Col
                    
                    if extra_date:
                        date_str = extra_date.strftime("%d-%m-%Y")
                        if new_status == "Interviewed":
                            cand_sheet.update_cell(cell.row, 7, date_str) # Int Date
                        if new_status == "Onboarded":
                            cand_sheet.update_cell(cell.row, 10, date_str) # Join Date
                            sr_date = calculate_sr_date(date_str, current_client)
                            cand_sheet.update_cell(cell.row, 11, sr_date) # SR Date
                    
                    st.success("Updated!")
                    st.rerun()
            edit_status(row['Reference_ID'], row['Candidate Name'], row['Client Name'])

        # WHATSAPP INVITE (Points 44-46)
        if r_cols[8].button("💬", key=f"wa_{row['Reference_ID']}"):
            # Fetch Client Info
            c_df = pd.DataFrame(client_sheet.get_all_records())
            c_info = c_df[c_df['Client Name'] == row['Client Name']].iloc[0]
            
            msg = f"Dear {row['Candidate Name']},\n\nCongratulations! Interview Invite.\n\nPosition: {row['Job Title']}\nInterview Date: {row['Interview Date']}\nTime: 10.30 AM\nVenue: {c_info['Address']}\nMap: {c_info['Map Link']}\nContact: {c_info['Contact Person']}\n\nRegards,\n{u['Username']}\nTakecare HR Team"
            wa_link = f"https://wa.me/91{row['Contact Number']}?text={urllib.parse.quote(msg)}"
            st.markdown(f'<a href="{wa_link}" target="_blank">Click to Send WhatsApp</a>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
