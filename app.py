import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta
import time

# --- 1. PAGE CONFIG & UI THEME (Points 1, 2, 70, 81) ---
st.set_page_config(page_title="Takecare ATS", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for Red-Blue Gradient, Fixed Header, and White Input Boxes
st.markdown("""
    <style>
    /* Background Gradient (Point 2) */
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }
    
    /* Fixed Header (Points 24, 81) */
    .fixed-header {
        position: fixed; top: 0; left: 0; width: 100%; height: 210px;
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%);
        z-index: 1000; padding: 20px 45px; border-bottom: 2px solid white;
    }

    /* ATS Table Container (Point 25, 26) */
    .ats-container {
        background-color: white; margin-top: 220px; 
        padding: 0px; border-radius: 0px; min-height: 80vh;
    }

    /* Input Boxes Styling (Point 6, 7, 70) */
    div[data-baseweb="input"], div[data-baseweb="select"], .stTextArea textarea, input {
        background-color: white !important; color: #0d47a1 !important;
        font-weight: bold !important; border: 1px solid #ccc !important;
    }

    /* Table Header (Point 27) */
    .sticky-th {
        position: sticky; top: 210px; z-index: 999;
        background-color: #0d47a1; color: white;
        display: flex; border-bottom: 1px solid #ccc;
    }
    .th-cell {
        flex: 1; padding: 12px 5px; text-align: center;
        font-weight: bold; border: 0.5px solid white; font-size: 13px;
    }

    /* Pop-up Box Style (Point 2, 29, 72) */
    div[role="dialog"] { background-color: #0d47a1 !important; color: white !important; }
    div[role="dialog"] label { color: white !important; }

    /* Login Page Centering (Points 4, 5) */
    .login-title { color: white; text-align: center; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION (Google Sheets) ---
@st.cache_resource
def init_connection():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

gc = init_connection()
sh = gc.open("ATS_Cloud_Database")
u_sheet, c_sheet, d_sheet = sh.worksheet("User_Master"), sh.worksheet("Client_Master"), sh.worksheet("ATS_Data")

# --- 3. CORE LOGIC FUNCTIONS ---

def get_next_ref_id(): # Point 35
    ids = d_sheet.col_values(1)
    if len(ids) <= 1: return "E0001"
    last_id = ids[-1]
    return f"E{int(last_id[1:]) + 1:04d}"

def clean_date(val): # Removes 00:00:00
    return str(val).split(' ')[0] if val else ""

def auto_delete_logic(df): # Points 62, 63, 64
    today = datetime.now()
    # Logic based on status and days
    df['Shortlisted Date'] = pd.to_datetime(df['Shortlisted Date'], format='%d-%m-%Y', errors='coerce')
    # Filter out rows that meet deletion criteria for UI only
    mask = ~((df['Status'] == 'Shortlisted') & (df['Shortlisted Date'] < today - timedelta(days=7)))
    return df[mask]

# --- 4. LOGIN PAGE (Points 3 - 12) ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("<h1 class='login-title'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    st.markdown("<h3 class='login-title'>ATS LOGIN</h3>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.container(border=True):
            user_mail = st.text_input("Email ID")
            pwd = st.text_input("Password", type="password")
            show_pwd = st.checkbox("Show Password") # Point 7
            rem = st.checkbox("Remember me") # Point 8
            
            if st.button("LOGIN", use_container_width=True, type="primary"):
                users = pd.DataFrame(u_sheet.get_all_records())
                match = users[(users['Mail_ID'] == user_mail) & (users['Password'].astype(str) == pwd)]
                if not match.empty:
                    st.session_state.auth = True
                    st.session_state.user = match.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("Incorrect username or password") # Point 11
            
            st.info("Forgot password? Contact Admin") # Point 10

# --- 5. DASHBOARD (Points 13 - 81) ---
else:
    u = st.session_state.user
    
    # --- PAGE HEADER (Fixed Top) ---
    st.markdown(f"""
        <div class="fixed-header">
            <div style="display: flex; justify-content: space-between;">
                <div style="color: white;">
                    <h2 style="margin:0;">Takecare Manpower Service Pvt Ltd</h2>
                    <p style="margin:0; font-size:16px;">Successful HR Firm</p>
                    <div style="height:15px;"></div>
                    <p style="margin:0; font-size:18px;">Welcome back, {u['Username']}!</p>
                    <div class="target-pill">📞 Target for Today: 80+ Telescreening Calls / 3-5 Interview / 1+ Joining</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Header Right Side Controls (Point 20-23)
    _, r_col = st.columns([3, 1])
    with r_col:
        st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
        if st.button("Logout 🚪", key="logout"):
            st.session_state.auth = False
            st.rerun()
            
        search_term = st.text_input("Search Candidate", label_visibility="collapsed", placeholder="🔍 Search...")
        
        c1, c2 = st.columns(2)
        with c1:
            if u['Role'] in ['ADMIN', 'TL']: # Point 78
                if st.button("Filter ⚙️"):
                    @st.dialog("Advanced Filter") # Point 72
                    def filter_pop():
                        st.selectbox("Client Name", ["All"])
                        st.selectbox("User Name", ["All"])
                        st.date_input("From Date")
                        st.date_input("To Date")
                        st.button("Apply Filter")
                    filter_pop()
        with c2:
            if st.button("+ New Shortlist", type="primary"): # Point 23, 29
                @st.dialog("Add New Candidate")
                def add_pop():
                    rid = get_next_ref_id()
                    col1, col2 = st.columns(2)
                    name = col1.text_input("Candidate Name")
                    phone = col2.text_input("Contact Number")
                    clients = pd.DataFrame(c_sheet.get_all_records())
                    cl_name = col1.selectbox("Client Name", clients['Client Name'].unique())
                    pos = col2.selectbox("Position", clients[clients['Client Name']==cl_name]['Position'].unique())
                    c_date = col1.date_input("Commitment Date")
                    stat = col2.selectbox("Status", ["Shortlisted"])
                    feed = st.text_area("Feedback (Optional)")
                    
                    if st.button("SUBMIT"):
                        # Save to Google Sheet
                        new_row = [rid, datetime.now().strftime("%d-%m-%Y"), name, phone, cl_name, pos, c_date.strftime("%d-%m-%Y"), stat, u['Username'], "", "", feed]
                        d_sheet.append_row(new_row)
                        st.success("Entry Saved!")
                        time.sleep(1)
                        st.rerun()
                add_pop()

    # --- ATS TRACKING TABLE (Points 25 - 27) ---
    st.markdown('<div class="ats-container">', unsafe_allow_html=True)
    
    # Table Header Labels
    t_headers = ["Ref ID", "Candidate", "Contact", "Position", "Commit/Int Date", "Status", "Onboarded", "SR Date", "HR Name", "Action", "WA Invite"]
    h_cols = st.columns([1, 1.5, 1.2, 1.5, 1.2, 1.2, 1.2, 1, 1, 0.8, 0.8])
    for col, text in zip(h_cols, t_headers):
        col.markdown(f'<div class="th-cell" style="background-color:#0d47a1; color:white;">{text}</div>', unsafe_allow_html=True)

    # Fetch and Filter Data
    raw_df = pd.DataFrame(d_sheet.get_all_records())
    df = auto_delete_logic(raw_df) # Points 62-65
    
    # Role-based visibility (Points 66-68)
    if u['Role'] == 'RECRUITER':
        df = df[df['HR Name'] == u['Username']]
    elif u['Role'] == 'TL':
        users_list = pd.DataFrame(u_sheet.get_all_records())
        team = users_list[users_list['Report_To'] == u['Username']]['Username'].tolist()
        df = df[df['HR Name'].isin(team + [u['Username']])]

    # Search Logic (Points 79-81)
    if search_term:
        df = df[df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)]

    # Display Rows
    for i, row in df.iterrows():
        r_cols = st.columns([1, 1.5, 1.2, 1.5, 1.2, 1.2, 1.2, 1, 1, 0.8, 0.8])
        r_cols[0].write(row['Reference_ID'])
        r_cols[1].write(row['Candidate Name'])
        r_cols[2].write(row['Contact Number'])
        r_cols[3].write(row['Job Title'])
        r_cols[4].write(clean_date(row['Interview Date']))
        r_cols[5].write(row['Status'])
        r_cols[6].write(clean_date(row['Joining Date']))
        r_cols[7].write(clean_date(row['SR Date']))
        r_cols[8].write(row['HR Name'])
        
        # Action Edit Pencil (Points 47-60)
        if r_cols[9].button("📝", key=f"edit_{i}"):
            @st.dialog("Update Status")
            def edit_pop(r):
                st.write(f"Candidate: {r['Candidate Name']} | {r['Contact Number']}")
                new_status = st.selectbox("Status", ["Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Left"])
                action_date = st.date_input("Date")
                new_feed = st.text_input("Feedback", max_chars=20)
                
                if st.button("SAVE CHANGES"):
                    idx = raw_df[raw_df['Reference_ID'] == r['Reference_ID']].index[0] + 2
                    d_sheet.update_cell(idx, 8, new_status) # Update Status
                    d_sheet.update_cell(idx, 12, new_feed) # Update Feedback
                    
                    if new_status == "Interviewed":
                        d_sheet.update_cell(idx, 7, action_date.strftime("%d-%m-%Y")) # Updates Commit Date (Point 54)
                    elif new_status == "Onboarded":
                        d_sheet.update_cell(idx, 10, action_date.strftime("%d-%m-%Y"))
                        # SR Date Logic (Point 61)
                        c_info = pd.DataFrame(c_sheet.get_all_records())
                        sr_days = c_info[c_info['Client Name'] == r['Client Name']]['SR Days'].values[0]
                        sr_date = (action_date + timedelta(days=int(sr_days))).strftime("%d-%m-%Y")
                        d_sheet.update_cell(idx, 11, sr_date)
                    st.rerun()
            edit_pop(row)

        # Whatsapp Invite (Points 44-46)
        if r_cols[10].button("📲", key=f"wa_{i}"):
            c_info = pd.DataFrame(c_sheet.get_all_records())
            client = c_info[c_info['Client Name'] == row['Client Name']].iloc[0]
            
            msg = f"""Dear {row['Candidate Name']},
Congratulations! We invite you for a Direct Interview.
Reference: Takecare Manpower Services Pvt Ltd
Position: {row['Job Title']}
Interview Date: {row['Interview Date']}
Interview Time: 10.30 Am
Venue: {client['Address']}
Map: {client['Map Link']}
Contact Person: {client['Contact Person']}
Regards, {u['Username']}
Takecare HR Team"""
            
            encoded_msg = urllib.parse.quote(msg)
            wa_url = f"https://wa.me/{row['Contact Number']}?text={encoded_msg}"
            st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{wa_url}\'">', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
