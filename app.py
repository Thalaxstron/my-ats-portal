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
    div[data-baseweb="input"], div[data-baseweb="select"], .stTextArea textarea {
        background-color: white !important;
        color: #0d47a1 !important;
        border-radius: 5px;
    }
    .main-title { color: #0d47a1; font-size: 24px; font-weight: bold; margin:0; }
    .sub-slogan { color: #555; font-size: 14px; font-style: italic; }
    .target-bar { background-color: #e3f2fd; color: #0d47a1; padding: 8px; border-radius: 5px; font-weight: bold; margin-top:5px; border-left: 5px solid #0d47a1; }
    .ats-container { background-color: white; padding: 20px; border-radius: 10px; color: black; margin-top: 180px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DB CONNECTION ---
def get_gsheet_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

try:
    client = get_gsheet_client()
    sh = client.open("ATS_Cloud_Database")
    user_sheet = sh.worksheet("User_Master")
    client_sheet = sh.worksheet("Client_Master")
    data_sheet = sh.worksheet("ATS_Data")
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.stop()

# --- 3. CORE LOGIC ---
def get_next_ref_id():
    all_ids = data_sheet.col_values(1)
    if len(all_ids) <= 1: return "E00001"
    last_id = all_ids[-1]
    if last_id.startswith("E"):
        num = int(last_id[1:]) + 1
        return f"E{num:05d}"
    return "E00001"

def apply_auto_delete_logic(df):
    today = datetime.now()
    df['Shortlisted Date'] = pd.to_datetime(df['Shortlisted Date'], format="%d-%m-%Y", errors='coerce')
    df['Interview Date'] = pd.to_datetime(df['Interview Date'], format="%d-%m-%Y", errors='coerce')
    mask1 = (df['Status'] == 'Shortlisted') & (df['Shortlisted Date'] < today - timedelta(days=7))
    mask2 = (df['Status'].isin(['Interviewed', 'Selected', 'Hold', 'Rejected'])) & (df['Interview Date'] < today - timedelta(days=30))
    mask3 = (df['Status'].isin(['Left', 'Not Joined'])) & (df['Shortlisted Date'] < today - timedelta(days=3))
    return df[~(mask1 | mask2 | mask3) | (df['Status'].isin(['Onboarded', 'Project Success']))]

# --- 4. SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 5. LOGIN PAGE ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center; color:white;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:white;'>ATS LOGIN</h3>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1, 1])
    with col:
        with st.container(border=True):
            u_mail = st.text_input("Email ID")
            u_pass = st.text_input("Password", type="password")
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

# --- 6. MAIN DASHBOARD ---
else:
    user = st.session_state.user_data
    st.markdown(f"""
        <div class="fixed-header">
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <div class="main-title">Takecare Manpower Service Pvt Ltd</div>
                    <div class="sub-slogan">Successful HR Firm</div>
                    <div style="font-size:18px; margin-top:5px;">Welcome back, <b>{user['Username']}</b>!</div>
                </div>
                <div style="text-align:right;">
                    <div class="target-bar">📞 Target: 80+ Calls / 3-5 Interview / 1+ Joining</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br><br><br><br><br><br><br>", unsafe_allow_html=True)
    top_col1, top_col2, top_col3, top_col4 = st.columns([2, 1, 1, 1])
    
    with top_col4:
        if st.button("Logout 🚪", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
            
    with top_col1:
        search_query = st.text_input("🔍 Search Candidate", placeholder="Type and press Enter...")

    with top_col3:
        @st.dialog("➕ New Shortlist Entry")
        def add_candidate():
            clients = pd.DataFrame(client_sheet.get_all_records())
            col_a, col_b = st.columns(2)
            ref_id = get_next_ref_id()
            col_a.text_input("Reference ID", value=ref_id, disabled=True)
            short_date = col_b.text_input("Date", value=datetime.now().strftime("%d-%m-%Y"), disabled=True)
            c_name = col_a.text_input("Candidate Name")
            c_phone = col_b.text_input("Contact Number")
            client_name = col_a.selectbox("Client", options=clients['Client Name'].unique())
            positions = clients[clients['Client Name'] == client_name]['Position'].tolist()
            job_title = col_b.selectbox("Position", options=positions)
            int_date = col_a.date_input("Commitment Date")
            if st.button("SUBMIT"):
                data_sheet.append_row([ref_id, short_date, c_name, c_phone, client_name, job_title, int_date.strftime("%d-%m-%Y"), "Shortlisted", user['Username'], "", "", ""])
                st.success("Saved!")
                time.sleep(1)
                st.rerun()
        if st.button("+ New Shortlist", type="primary", use_container_width=True):
            add_candidate()

    # --- ATS TABLE ---
    st.markdown('<div class="ats-container">', unsafe_allow_html=True)
    raw_df = pd.DataFrame(data_sheet.get_all_records())
    
    if user['Role'] == 'RECRUITER':
        display_df = raw_df[raw_df['HR Name'] == user['Username']]
    elif user['Role'] == 'TL':
        team = pd.DataFrame(user_sheet.get_all_records())
        team_list = team[team['Report_To'] == user['Username']]['Username'].tolist()
        display_df = raw_df[raw_df['HR Name'].isin(team_list + [user['Username']])]
    else:
        display_df = raw_df

    display_df = apply_auto_delete_logic(display_df)
    if search_query:
        display_df = display_df[display_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]

    cols = st.columns([1, 2, 1.5, 2, 1.5, 1.5, 1.5, 1.5, 1, 1])
    headers = ["Ref ID", "Candidate", "Contact", "Position", "Int. Date", "Status", "Onboard", "SR Date", "Edit", "WA"]
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
        
        if r_cols[8].button("📝", key=f"edit_{row['Reference_ID']}"):
            @st.dialog(f"Update {row['Candidate Name']}")
            def update_status(row_data):
                new_status = st.selectbox("Status", ["Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Left"])
                new_date = st.date_input("Date")
                if st.button("Update"):
                    idx_val = raw_df[raw_df['Reference_ID'] == row_data['Reference_ID']].index[0] + 2
                    data_sheet.update_cell(idx_val, 8, new_status)
                    st.success("Updated!")
                    st.rerun()
            update_status(row)

        if r_cols[9].button("📲", key=f"wa_{row['Reference_ID']}"):
            clients = pd.DataFrame(client_sheet.get_all_records())
            c_info = clients[(clients['Client Name'] == row['Client Name']) & (clients['Position'] == row['Job Title'])].iloc[0]
            msg = f"Dear {row['Candidate Name']},\nInvite for Interview.\nPosition: {row['Job Title']}\nDate: {row['Interview Date']}\nVenue: {c_info['Address']}\nMap: {c_info['Map Link']}\nContact: {c_info['Contact Person']}"
            encoded_msg = urllib.parse.quote(msg)
            # Corrected f-string logic
            wa_url = f"https://wa.me/91{row['Contact Number']}?text={encoded_msg}"
            st.markdown(f'<a href="{wa_url}" target="_blank">Click to open WhatsApp</a>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
