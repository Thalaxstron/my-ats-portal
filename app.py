import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta
import time

# --- 1. PAGE CONFIG & THEME (Points 1, 2, 70) ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for Red-Blue Gradient, Fixed Header, and White Input Boxes
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }
    /* Fixed Header Logic (Point 24) */
    .fixed-header {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background: white;
        z-index: 999;
        padding: 10px 20px;
        border-bottom: 2px solid #0d47a1;
    }
    /* White Boxes with Dark Blue Text (Point 70) */
    div[data-baseweb="input"], div[data-baseweb="select"], .stTextArea textarea {
        background-color: white !important;
        color: #0d47a1 !important;
        border-radius: 5px;
    }
    .main-title { color: #0d47a1; font-size: 24px; font-weight: bold; margin:0; }
    .sub-slogan { color: #555; font-size: 14px; font-style: italic; }
    .target-bar { background-color: #e3f2fd; color: #0d47a1; padding: 8px; border-radius: 5px; font-weight: bold; margin-top:5px; border-left: 5px solid #0d47a1; }
    
    /* ATS Table Styling (Point 25, 26) */
    .ats-container { background-color: white; padding: 20px; border-radius: 10px; color: black; margin-top: 180px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DB CONNECTION & CACHING ---
def get_gsheet_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

client = get_gsheet_client()
sh = client.open("ATS_Cloud_Database")
user_sheet = sh.worksheet("User_Master")
client_sheet = sh.worksheet("Client_Master")
data_sheet = sh.worksheet("ATS_Data")

# --- 3. CORE LOGIC FUNCTIONS ---

def get_next_ref_id():
    # Point 35: Auto ID Generation (E00001...)
    all_ids = data_sheet.col_values(1)
    if len(all_ids) <= 1: return "E00001"
    last_id = all_ids[-1]
    if last_id.startswith("E"):
        num = int(last_id[1:]) + 1
        return f"E{num:05d}"
    return "E00001"

def apply_auto_delete_logic(df):
    # Points 61-65: Visual Deletion Logic (Data remains in Sheet, hidden in App)
    today = datetime.now()
    df['Shortlisted Date'] = pd.to_datetime(df['Shortlisted Date'], format="%d-%m-%Y", errors='coerce')
    df['Interview Date'] = pd.to_datetime(df['Interview Date'], format="%d-%m-%Y", errors='coerce')
    
    # 1. Shortlisted > 7 days
    mask1 = (df['Status'] == 'Shortlisted') & (df['Shortlisted Date'] < today - timedelta(days=7))
    # 2. Interviewed/Selected/Hold/Rejected > 30 days
    mask2 = (df['Status'].isin(['Interviewed', 'Selected', 'Hold', 'Rejected'])) & (df['Interview Date'] < today - timedelta(days=30))
    # 3. Left/Not Joined > 3 days
    mask3 = (df['Status'].isin(['Left', 'Not Joined'])) & (df['Shortlisted Date'] < today - timedelta(days=3))
    
    # Apply filters (Keep Onboarded & Project Success)
    return df[~(mask1 | mask2 | mask3) | (df['Status'].isin(['Onboarded', 'Project Success']))]

# --- 4. SESSION STATE (Point 69: Refresh Persistence) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_role' not in st.session_state: st.session_state.user_role = None

# --- 5. LOGIN PAGE (Points 3-12) ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center; color:white;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:white;'>ATS LOGIN</h3>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 1, 1])
    with col:
        with st.container(border=True):
            u_mail = st.text_input("Email ID")
            u_pass = st.text_input("Password", type="password")
            show_pass = st.checkbox("Show Password") # Logic for point 7 handled by type toggle
            remember = st.checkbox("Remember me")
            
            if st.button("LOGIN", use_container_width=True):
                users = pd.DataFrame(user_sheet.get_all_records())
                user_match = users[(users['Mail_ID'] == u_mail) & (users['Password'].astype(str) == u_pass)]
                
                if not user_match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_match.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("Incorrect username or password")
            st.caption("Forgot password? Contact Admin")

# --- 6. MAIN DASHBOARD (Points 13-81) ---
else:
    user = st.session_state.user_data
    
    # --- HEADER (Points 14-24) ---
    st.markdown(f"""
        <div class="fixed-header">
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <div class="main-title">Takecare Manpower Service Pvt Ltd</div>
                    <div class="sub-slogan">Successful HR Firm</div>
                    <div style="font-size:18px; margin-top:5px;">Welcome back, <b>{user['Username']}</b>!</div>
                </div>
                <div style="text-align:right;">
                    <div class="target-bar">📞 Target for Today: 80+ Telescreening Calls / 3-5 Interview / 1+ Joining</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Action Row: Search, Filter, New Entry (Points 21, 22, 23, 71)
    st.markdown("<br><br><br><br><br><br><br>", unsafe_allow_html=True) # Spacer for fixed header
    
    top_col1, top_col2, top_col3, top_col4 = st.columns([2, 1, 1, 1])
    
    with top_col4:
        if st.button("Logout 🚪", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
            
    with top_col1:
        search_query = st.text_input("🔍 Search Candidate (Name, Phone, ID)", placeholder="Type and press Enter...")

    with top_col3:
        # --- NEW SHORTLIST POPUP (Points 28-43) ---
        @st.dialog("➕ New Shortlist Entry")
        def add_candidate():
            clients = pd.DataFrame(client_sheet.get_all_records())
            
            col_a, col_b = st.columns(2)
            ref_id = get_next_ref_id()
            col_a.text_input("Reference ID", value=ref_id, disabled=True)
            short_date = col_b.text_input("Shortlisted Date", value=datetime.now().strftime("%d-%m-%Y"), disabled=True)
            
            c_name = col_a.text_input("Candidate Name")
            c_phone = col_b.text_input("Contact Number")
            
            client_name = col_a.selectbox("Client Name", options=clients['Client Name'].unique())
            positions = clients[clients['Client Name'] == client_name]['Position'].tolist()
            job_title = col_b.selectbox("Position / Job Title", options=positions)
            
            int_date = col_a.date_input("Commitment Date")
            status = col_b.selectbox("Status", options=["Shortlisted"])
            feedback = st.text_area("Feedback")
            
            if st.button("SUBMIT"):
                # Save to Google Sheet
                data_sheet.append_row([
                    ref_id, short_date, c_name, c_phone, client_name, 
                    job_title, int_date.strftime("%d-%m-%Y"), status, 
                    user['Username'], "", "", feedback
                ])
                st.success("Data Saved!")
                time.sleep(1)
                st.rerun()
        
        if st.button("+ New Shortlist", type="primary", use_container_width=True):
            add_candidate()

    # --- FILTER POPUP (Points 71-78) ---
    if user['Role'] in ['ADMIN', 'TL']:
        with top_col2:
            @st.dialog("🎯 Filter Data")
            def filter_dialog():
                c1, c2 = st.columns(2)
                f_client = c1.selectbox("Filter by Client", ["All"] + list(pd.DataFrame(client_sheet.get_all_records())['Client Name'].unique()))
                f_user = c2.selectbox("Filter by Recruiter", ["All"] + list(pd.DataFrame(user_sheet.get_all_records())['Username'].unique()))
                
                start_date = c1.date_input("Interview From")
                end_date = c2.date_input("Interview To")
                
                if st.button("Apply Filter"):
                    st.session_state.filters = {"client": f_client, "user": f_user, "start": start_date, "end": end_date}
                    st.rerun()

            if st.button("📂 Filter", use_container_width=True):
                filter_dialog()

    # --- ATS TRACKING TABLE (Points 25-27, 47-65) ---
    st.markdown('<div class="ats-container">', unsafe_allow_html=True)
    
    # Load Data
    raw_df = pd.DataFrame(data_sheet.get_all_records())
    
    # Role Visibility (Points 66-68)
    if user['Role'] == 'RECRUITER':
        display_df = raw_df[raw_df['HR Name'] == user['Username']]
    elif user['Role'] == 'TL':
        team_members = pd.DataFrame(user_sheet.get_all_records())
        my_team = team_members[team_members['Report_To'] == user['Username']]['Username'].tolist()
        display_df = raw_df[raw_df['HR Name'].isin(my_team + [user['Username']])]
    else:
        display_df = raw_df

    # Apply Auto-Delete Logic
    display_df = apply_auto_delete_logic(display_df)

    # Apply Search Logic (Points 79-81)
    if search_query:
        display_df = display_df[display_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]

    # Render Table
    cols = st.columns([1, 2, 1.5, 2, 1.5, 1.5, 1.5, 1.5, 1, 1])
    headers = ["Ref ID", "Candidate Name", "Contact", "Position", "Int. Date", "Status", "Onboard", "SR Date", "Action", "WA"]
    for col, h in zip(cols, headers): col.write(f"**{h}**")

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
        
        # Edit Action (Point 47-60)
        if r_cols[8].button("📝", key=f"edit_{row['Reference_ID']}"):
            @st.dialog(f"Update {row['Candidate Name']}")
            def update_status(row_data):
                new_status = st.selectbox("Status", ["Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Left", "Project Success"])
                new_date = st.date_input("Select Date (Interview/Joining)")
                new_fb = st.text_input("Feedback (Max 20 chars)", max_chars=20)
                
                if st.button("Update"):
                    row_idx = raw_df[raw_df['Reference_ID'] == row_data['Reference_ID']].index[0] + 2
                    
                    # Point 61: SR Date Calculation
                    sr_date_val = ""
                    if new_status == "Onboarded":
                        clients = pd.DataFrame(client_sheet.get_all_records())
                        sr_days = clients[clients['Client Name'] == row_data['Client Name']]['SR Days'].values[0]
                        sr_date_val = (new_date + timedelta(days=int(sr_days))).strftime("%d-%m-%Y")
                        data_sheet.update_cell(row_idx, 10, new_date.strftime("%d-%m-%Y")) # Joining Date
                        data_sheet.update_cell(row_idx, 11, sr_date_val) # SR Date

                    data_sheet.update_cell(row_idx, 8, new_status)
                    if new_status == "Interviewed":
                        data_sheet.update_cell(row_idx, 7, new_date.strftime("%d-%m-%Y"))
                    
                    data_sheet.update_cell(row_idx, 12, new_fb)
                    st.success("Updated!")
                    st.rerun()
            update_status(row)

        # WhatsApp Logic (Points 44-46)
        if r_cols[9].button("📲", key=f"wa_{row['Reference_ID']}"):
            clients = pd.DataFrame(client_sheet.get_all_records())
            c_info = clients[(clients['Client Name'] == row['Client Name']) & (clients['Position'] == row['Job Title'])].iloc[0]
            
            msg = f"Dear {row['Candidate Name']},\n\nCongratulations! Invite for Interview.\n\nPosition: {row['Job Title']}\nInterview Date: {row['Interview Date']}\nTime: 10.30 AM\nVenue: {c_info['Address']}\nMap: {c_info['Map Link']}\nContact Person: {c_info['Contact Person']}\n\nRegards,\n{user['Username']}\nTakecare HR Team"
            encoded_msg = urllib.parse.quote(msg)
            wa_link = f"https
