import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta
import time

# --- 1. PAGE CONFIG & THEME (Points 1, 2, 24, 26, 70) ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }
    .fixed-header {
        position: fixed;
        top: 0; left: 0; width: 100%;
        background: white;
        z-index: 1000;
        padding: 10px 30px;
        border-bottom: 3px solid #0d47a1;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
    }
    div[data-baseweb="input"], div[data-baseweb="select"], .stTextArea textarea {
        background-color: white !important;
        color: #0d47a1 !important;
        border-radius: 5px;
        border: 1px solid #0d47a1 !important;
    }
    .main-title { color: #0d47a1; font-size: 24px; font-weight: bold; margin:0; }
    .target-bar { background-color: #e3f2fd; color: #0d47a1; padding: 8px; border-radius: 5px; font-weight: bold; border-left: 5px solid #0d47a1; margin-top:5px;}
    .ats-container { background-color: white; padding: 20px; border-radius: 10px; color: black; margin-top: 200px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DB CONNECTION ---
def get_gsheet_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

client = get_gsheet_client()
sh = client.open("ATS_Cloud_Database")
user_sheet = sh.worksheet("User_Master")
client_sheet = sh.worksheet("Client_Master")
data_sheet = sh.worksheet("ATS_Data")

# --- 3. LOGIC FUNCTIONS (Points 35, 61-65) ---
def get_next_ref_id():
    all_ids = data_sheet.col_values(1)
    if len(all_ids) <= 1: return "E0001"
    last_id = all_ids[-1]
    if last_id.startswith("E"):
        num = int(last_id[1:]) + 1
        return f"E{num:04d}"
    return "E0001"

def apply_auto_delete(df):
    today = datetime.now()
    df['Shortlisted Date'] = pd.to_datetime(df['Shortlisted Date'], format="%d-%m-%Y", errors='coerce')
    df['Interview Date'] = pd.to_datetime(df['Interview Date'], format="%d-%m-%Y", errors='coerce')
    
    m1 = (df['Status'] == 'Shortlisted') & (df['Shortlisted Date'] < today - timedelta(days=7))
    m2 = (df['Status'].isin(['Interviewed', 'Selected', 'Hold', 'Rejected'])) & (df['Interview Date'] < today - timedelta(days=30))
    m3 = (df['Status'].isin(['Left', 'Not Joined'])) & (df['Shortlisted Date'] < today - timedelta(days=3))
    
    return df[~(m1 | m2 | m3) | (df['Status'].isin(['Onboarded', 'Project Success']))]

# --- 4. LOGIN SESSION (Point 69) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 5. LOGIN PAGE ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center; color:white;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:white;'>ATS LOGIN</h3>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.container(border=True):
            u_mail = st.text_input("Email ID")
            u_pass = st.text_input("Password", type="password")
            if st.button("LOGIN", use_container_width=True, type="primary"):
                users = pd.DataFrame(user_sheet.get_all_records())
                match = users[(users['Mail_ID'] == u_mail) & (users['Password'].astype(str) == u_pass)]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Incorrect username or password")
            st.caption("Forgot password? Contact Admin")

# --- 6. MAIN DASHBOARD ---
else:
    user = st.session_state.user_data
    
    # FIXED HEADER
    st.markdown(f"""
        <div class="fixed-header">
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <div class="main-title">Takecare Manpower Service Pvt Ltd</div>
                    <div style="font-size:14px; color:#555; font-style:italic;">Successful HR Firm</div>
                    <div style="font-size:18px; color:#0d47a1;">Welcome back, <b>{user['Username']}</b>!</div>
                    <div class="target-bar">📞 Target: 80+ Calls / 3-5 Interview / 1+ Joining</div>
                </div>
                <div style="text-align:right;">
                    <div id="logout-placeholder"></div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
    top1, top2, top3, top4 = st.columns([2, 1, 1, 1])
    with top1: search_query = st.text_input("🔍 Search Candidate", placeholder="Type and Enter...")
    with top4: 
        if st.button("Logout 🚪", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # NEW SHORTLIST POPUP (Point 29-43)
    @st.dialog("➕ New Shortlist Entry")
    def add_candidate():
        clients_df = pd.DataFrame(client_sheet.get_all_records())
        c1, c2 = st.columns(2)
        ref_id = get_next_ref_id()
        c1.text_input("Ref ID", value=ref_id, disabled=True)
        s_date = c2.text_input("Date", value=datetime.now().strftime("%d-%m-%Y"), disabled=True)
        name = c1.text_input("Candidate Name")
        phone = c2.text_input("Contact Number")
        client_name = c1.selectbox("Client", options=clients_df['Client Name'].unique())
        job_title = c2.selectbox("Position", options=clients_df[clients_df['Client Name']==client_name]['Position'].unique())
        int_date = c1.date_input("Interview Date")
        if st.button("SUBMIT"):
            data_sheet.append_row([ref_id, s_date, name, phone, client_name, job_title, int_date.strftime("%d-%m-%Y"), "Shortlisted", user['Username'], "", "", ""])
            st.success("Saved!"); time.sleep(1); st.rerun()

    with top3:
        if st.button("+ New Shortlist", type="primary", use_container_width=True): add_candidate()

    # ATS TABLE
    st.markdown('<div class="ats-container">', unsafe_allow_html=True)
    raw_df = pd.DataFrame(data_sheet.get_all_records())
    
    # ROLE FILTER
    if user['Role'] == 'RECRUITER': df = raw_df[raw_df['HR Name'] == user['Username']]
    elif user['Role'] == 'TL': 
        users_df = pd.DataFrame(user_sheet.get_all_records())
        team = users_df[users_df['Report_To'] == user['Username']]['Username'].tolist()
        df = raw_df[raw_df['HR Name'].isin(team + [user['Username']])]
    else: df = raw_df

    df = apply_auto_delete(df)
    if search_query: df = df[df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]

    # RENDER TABLE
    cols = st.columns([1, 1.5, 1.2, 1.5, 1.2, 1.2, 1.2, 1, 1, 1])
    headers = ["Ref ID", "Candidate", "Contact", "Position", "Int. Date", "Status", "Onboard", "SR", "Edit", "WA"]
    for col, h in zip(cols, headers): col.write(f"**{h}**")

    for idx, row in df.iterrows():
        r_cols = st.columns([1, 1.5, 1.2, 1.5, 1.2, 1.2, 1.2, 1, 1, 1])
        r_cols[0].write(row['Reference_ID'])
        r_cols[1].write(row['Candidate Name'])
        r_cols[2].write(row['Contact Number'])
        r_cols[3].write(row['Job Title'])
        r_cols[4].write(row['Interview Date'])
        r_cols[5].write(row['Status'])
        r_cols[6].write(row['Joining Date'])
        r_cols[7].write(row['SR Date'])
        
        # EDIT ACTION
        if r_cols[8].button("📝", key=f"e_{row['Reference_ID']}"):
            @st.dialog(f"Update {row['Candidate Name']}")
            def update_ui(r):
                new_status = st.selectbox("Status", ["Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Left"])
                new_date = st.date_input("Date")
                new_fb = st.text_input("Feedback", max_chars=20)
                if st.button("SAVE"):
                    s_idx = raw_df[raw_df['Reference_ID'] == r['Reference_ID']].index[0] + 2
                    data_sheet.update_cell(s_idx, 8, new_status)
                    data_sheet.update_cell(s_idx, 12, new_fb)
                    if new_status == "Onboarded":
                        c_master = pd.DataFrame(client_sheet.get_all_records())
                        sr_days = c_master[c_master['Client Name'] == r['Client Name']]['SR Days'].values[0]
                        sr_date = (new_date + timedelta(days=int(sr_days))).strftime("%d-%m-%Y")
                        data_sheet.update_cell(s_idx, 10, new_date.strftime("%d-%m-%Y"))
                        data_sheet.update_cell(s_idx, 11, sr_date)
                    st.rerun()
            update_ui(row)

        # WHATSAPP (Point 46)
        if r_cols[9].button("📲", key=f"w_{row['Reference_ID']}"):
            c_master = pd.DataFrame(client_sheet.get_all_records())
            info = c_master[c_master['Client Name'] == row['Client Name']].iloc[0]
            msg = f"Dear {row['Candidate Name']},\n\nInvite for Interview.\nRef: Takecare Manpower\nPosition: {row['Job Title']}\nDate: {row['Interview Date']}\nVenue: {info['Address']}\nMap: {info['Map Link']}\nContact: {info['Contact Person']}\n\nRegards,\n{user['Username']}"
            url = f"https://wa.me/91{row['Contact Number']}?text={urllib.parse.quote(msg)}"
            st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{url}\'">', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
