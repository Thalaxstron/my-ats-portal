import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta
import time

# --- 1. PAGE CONFIG & RESPONSIVE CSS (Points 1, 2, 24, 26, 70) ---
st.set_page_config(page_title="Takecare ATS", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Gradient Background */
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }
    
    /* Fixed Header Styling (Point 24) */
    .fixed-header {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background: white;
        z-index: 999;
        padding: 15px 30px;
        border-bottom: 3px solid #0d47a1;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
    }
    
    /* White Input Boxes & Dark Blue Text (Point 6, 7, 70) */
    div[data-baseweb="input"], div[data-baseweb="select"], .stTextArea textarea {
        background-color: white !important;
        color: #0d47a1 !important;
        border-radius: 8px !important;
        border: 1px solid #0d47a1 !important;
    }
    
    input { color: #0d47a1 !important; }
    
    /* ATS Table Container (Point 25, 26) */
    .ats-container {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        color: black;
        margin-top: 220px; /* Space for fixed header */
        overflow-x: auto;
    }
    
    .main-title { color: #0d47a1; font-size: 26px; font-weight: bold; margin:0; }
    .slogan { color: #555; font-size: 14px; font-style: italic; margin-bottom: 10px;}
    .welcome-text { color: #0d47a1; font-size: 18px; font-weight: 500; }
    .target-bar { background-color: #e3f2fd; color: #0d47a1; padding: 10px; border-radius: 8px; font-weight: bold; border-left: 5px solid #0d47a1; }
    
    /* Buttons */
    .stButton>button {
        border-radius: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION ---
def get_gsheet_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

client = get_gsheet_client()
sh = client.open("ATS_Cloud_Database")
user_sheet = sh.worksheet("User_Master")
client_sheet = sh.worksheet("Client_Master")
data_sheet = sh.worksheet("ATS_Data")

# --- 3. HELPER FUNCTIONS ---
def get_next_ref_id():
    all_ids = data_sheet.col_values(1)
    if len(all_ids) <= 1: return "E0001"
    last_id = all_ids[-1]
    if last_id.startswith("E"):
        num = int(last_id[1:]) + 1
        return f"E{num:04d}"
    return "E0001"

# --- 4. SESSION MANAGEMENT (Point 69) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 5. LOGIN PAGE (Points 3-12) ---
if not st.session_state.logged_in:
    st.markdown("<br><br><h1 style='text-align:center; color:white;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:white;'>ATS LOGIN</h3>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        with st.container(border=True):
            u_mail = st.text_input("Email ID (Login)", placeholder="Enter Mail ID")
            u_pass = st.text_input("Password", type="password")
            st.checkbox("Remember me")
            
            if st.button("LOGIN", use_container_width=True, type="primary"):
                users = pd.DataFrame(user_sheet.get_all_records())
                user_match = users[(users['Mail_ID'] == u_mail) & (users['Password'].astype(str) == u_pass)]
                
                if not user_match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_match.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("Incorrect username or password")
            st.info("Forgot password? Contact Admin")

# --- 6. MAIN DASHBOARD ---
else:
    user = st.session_state.user_data
    
    # --- HEADER (Points 14-24) ---
    st.markdown(f"""
        <div class="fixed-header">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <div class="main-title">Takecare Manpower Service Pvt Ltd</div>
                    <div class="slogan">Successful HR Firm</div>
                    <div class="welcome-text">Welcome back, {user['Username']}!</div>
                    <div class="target-bar">📞 Target for Today: 80+ Telescreening Calls / 3-5 Interview / 1+ Joining</div>
                </div>
                <div style="text-align: right;">
                    <div id="header-actions"></div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Placing Streamlit buttons in the fixed header area using absolute positioning or columns
    header_col1, header_col2, header_col3 = st.columns([6, 2, 1])
    
    with header_col3:
        if st.button("Logout 🚪", key="logout_btn"):
            st.session_state.logged_in = False
            st.rerun()

    with header_col2:
        # Search & Filter Logic
        search_query = st.text_input("🔍 Search", placeholder="Search anything...", label_visibility="collapsed")
        
    # --- FLOATING ACTION BUTTONS ---
    btn_col1, btn_col2, btn_col3 = st.columns([1,1,1])
    
    # Point 29: New Shortlist Dialog
    @st.dialog("➕ New Shortlist Entry")
    def add_candidate_dialog():
        clients_df = pd.DataFrame(client_sheet.get_all_records())
        ref_id = get_next_ref_id()
        
        c1, c2 = st.columns(2)
        ref = c1.text_input("Reference ID", value=ref_id, disabled=True)
        s_date = c2.text_input("Shortlisted Date", value=datetime.now().strftime("%d-%m-%Y"), disabled=True)
        
        name = c1.text_input("Candidate Name")
        phone = c2.text_input("Contact Number")
        
        client_name = c1.selectbox("Client Name", options=clients_df['Client Name'].unique())
        # Point 40: Position Filtered by Client
        positions = clients_df[clients_df['Client Name'] == client_name]['Position'].tolist()
        job_title = c2.selectbox("Position / Job Title", options=positions)
        
        comm_date = c1.date_input("Commitment Date")
        status = c2.selectbox("Status", options=["Shortlisted"])
        fb = st.text_area("Feedback (Optional)")
        
        if st.button("SUBMIT"):
            data_sheet.append_row([
                ref_id, s_date, name, phone, client_name, job_title, 
                comm_date.strftime("%d-%m-%Y"), status, user['Username'], "", "", fb
            ])
            st.success("Entry Saved!")
            time.sleep(1)
            st.rerun()

    if st.button("+ New Shortlist", type="primary"):
        add_candidate_dialog()

    # --- ATS TRACKING TABLE ---
    st.markdown('<div class="ats-container">', unsafe_allow_html=True)
    
    # Load Data
    raw_df = pd.DataFrame(data_sheet.get_all_records())
    
    # Point 66-68: Role Visibility Logic
    if user['Role'] == 'RECRUITER':
        display_df = raw_df[raw_df['HR Name'] == user['Username']]
    elif user['Role'] == 'TL':
        # TL sees their team entries (Report_To logic required in User_Master)
        display_df = raw_df # Simplified for demo; filter logic goes here
    else:
        display_df = raw_df

    # Point 79-81: Search Filter
    if search_query:
        display_df = display_df[display_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]

    # Render Table Headers
    t_cols = st.columns([1, 2, 1.5, 2, 1.5, 1.5, 1.5, 1.5, 1, 1])
    headers = ["Ref ID", "Candidate", "Contact", "Position", "Int. Date", "Status", "Onboard", "SR Date", "Action", "WA"]
    for col, h in zip(t_cols, headers):
        col.write(f"**{h}**")

    # Render Data Rows
    for idx, row in display_df.iterrows():
        r_cols = st.columns([1, 2, 1.5, 2, 1.5, 1.5, 1.5, 1.5, 1, 1])
        r_cols[0].write(row['Reference_ID'])
        r_cols[1].write(row['Candidate Name'])
        r_cols[2].write(row['Contact Number'])
        r_cols[3].write(row['Job Title'])
        r_cols[4].write(row['Interview Date'])
        r_cols[5].write(row['Status'])
        r_cols[6].write(row['Joining Date'])
        r_cols[7].write(row['SR Date'])
        
        # Point 47: Edit Action
        if r_cols[8].button("📝", key=f"edit_{row['Reference_ID']}"):
            @st.dialog(f"Update: {row['Candidate Name']}")
            def update_status_dialog(row_data):
                st.write(f"Contact: {row_data['Contact Number']}")
                new_status = st.selectbox("Update Status", ["Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Left", "Project Success"])
                new_date = st.date_input("Interview/Onboard Date")
                new_fb = st.text_input("Feedback (Max 20 chars)", max_chars=20)
                
                if st.button("Update"):
                    # Find Google Sheet Row Index
                    sheet_idx = raw_df[raw_df['Reference_ID'] == row_data['Reference_ID']].index[0] + 2
                    data_sheet.update_cell(sheet_idx, 8, new_status)
                    data_sheet.update_cell(sheet_idx, 12, new_fb)
                    # Point 53/56: Date Logic
                    if new_status == "Interviewed":
                        data_sheet.update_cell(sheet_idx, 7, new_date.strftime("%d-%m-%Y"))
                    elif new_status == "Onboarded":
                        data_sheet.update_cell(sheet_idx, 10, new_date.strftime("%d-%m-%Y"))
                    st.rerun()
            update_status_dialog(row)

        # Point 44-46: WhatsApp Logic
        if r_cols[9].button("📲", key=f"wa_{row['Reference_ID']}"):
            clients_master = pd.DataFrame(client_sheet.get_all_records())
            c_info = clients_master[clients_master['Client Name'] == row['Client Name']].iloc[0]
            
            msg = f"""Dear {row['Candidate Name']},
Congratulations! We invite you for an interview.
Reference: Takecare Manpower Services Pvt Ltd
Position: {row['Job Title']}
Interview Date: {row['Interview Date']}
Time: 10.30 AM
Venue: {c_info['Address']}
Map: {c_info['Map Link']}
Contact Person: {c_info['Contact Person']}
Regards, {user['Username']}"""
            
            encoded_msg = urllib.parse.quote(msg)
            wa_link = f"https://wa.me/91{row['Contact Number']}?text={encoded_msg}"
            # Open in new tab
            st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{wa_link}\'">', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
